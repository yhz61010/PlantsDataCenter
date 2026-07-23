import argparse
import json
import os
import re
import sys

# 允许以 `python3 scripts/retrieve_context.py ...` 直接运行（把仓库根加入 sys.path）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.export import load_all


PLACEHOLDERS = {"", "无", "暂无数据", None}
FIELD_ORDER = (
    "学名",
    "中文名",
    "俗名",
    "异名",
    "描述",
    "分类系统",
    "物种保护",
    "分类信息",
    "形态特征",
    "生态习性",
    "功用价值",
    "植物志",
    "备注",
)
DEFAULT_CONTEXT_FIELDS = ("描述", "分类系统", "形态特征", "生态习性", "功用价值", "物种保护", "分类信息", "植物志")
FIELD_HINTS = {
    "俗名": ("俗名", "别名"),
    "异名": ("异名", "synonym"),
    "分类系统": ("分类", "科", "属", "拉丁", "学名"),
    "物种保护": ("保护", "濒危", "等级"),
    "分类信息": ("分类信息", "模式", "属种"),
    "形态特征": ("形态", "特征", "识别", "生活型", "叶", "花", "果", "种子"),
    "生态习性": ("生态", "习性", "分布", "产地", "生境", "海拔", "物候"),
    "功用价值": ("功用", "用途", "价值", "经济", "文化", "药用", "观赏"),
    "植物志": ("植物志", "文献", "引证", "变种"),
}
FIELD_WEIGHTS = {
    "中文名": 30,
    "俗名": 18,
    "学名": 16,
    "异名": 12,
    "分类系统": 10,
    "描述": 6,
    "形态特征": 5,
    "生态习性": 5,
    "功用价值": 5,
    "物种保护": 4,
    "分类信息": 4,
    "植物志": 2,
    "备注": 1,
}
STOP_TERMS = {
    "什么",
    "怎么",
    "如何",
    "哪些",
    "有哪",
    "有什么",
    "有哪些",
    "植物",
    "记录",
    "资料",
    "形态",
    "特征",
    "形态特征",
    "用途",
    "功用",
    "价值",
}
QUESTION_MARKERS = ("什么", "哪些", "有哪", "哪个", "哪种", "属于")
LIST_QUERY_MARKERS = ("哪些", "有哪", "有哪些", "列出", "名单", "列表")

# 单字中文名“点名”判定用的边界字符：虚词、常见问句/请求引导动词、标点、空白
#（非中文字符另行判定）。用于避免“桑拿→桑”式误锁，同时保住“桑的果实→桑”“桃树→桃”式真实点名。
_BOUNDARY_CHARS = set(
    "的是和与及或有无这那每各某本该其为在对把让从跟向到于也都又还就要会能可想"
    "哪什怎如何吗呢吧啊么了地得着过并且但即"
    "问查看找搜说讲"                       # 常见问句/请求引导动词：请问槐…/帮我查桃…/看看莲…
    "、，,。.；;：:？?！!…（）()「」『』【】《》“”\"'‘’ \t\r\n"
)
# 紧跟在单字名之后、仍指代该植物的常见后缀，如“桃树/槐花/艾叶/桑果”。
# 只放植物部位/衍生词；不要放 属/科/目（分类阶查询由 taxonomy_terms / rank query 处理）。
# 末尾 草菜藕葚椹 针对现有单字名：艾草 / 荠菜 / 莲藕(莲菜) / 桑葚 / 桑椹。
_NAME_SUFFIX_CHARS = set("树花叶果实子籽苗枝干根皮草菜藕葚椹")


def _norm(s):
    return str(s).lower()


def _is_placeholder(v):
    if isinstance(v, (dict, list)):
        return False
    return v in PLACEHOLDERS


def _rank_terms_from_chunk(chunk, rank_vocab=None):
    terms = set(re.findall(r"[\u4e00-\u9fff]{1,8}?[界门纲目科属](?!于)", chunk))
    terms = {term for term in terms if not any(marker in term for marker in QUESTION_MARKERS)}
    if rank_vocab is not None:
        terms = {term for term in terms if term in rank_vocab}
    return terms


def taxonomy_terms(records):
    terms = set()
    for record in records:
        taxonomy = record.get("分类系统")
        if not isinstance(taxonomy, dict):
            continue
        for value in taxonomy.values():
            if not value or _is_placeholder(value):
                continue
            text = str(value)
            latin, sep, rest = text.partition("-")
            if sep and latin:
                terms.add(latin)
            chinese = rest.split("(", 1)[0].strip() if rest else text.strip()
            if chinese:
                terms.add(chinese)
    return terms


def _flatten(v):
    if _is_placeholder(v):
        return ""
    if isinstance(v, dict):
        return " ".join(f"{k} {v2}" for k, v2 in v.items() if not _is_placeholder(v2))
    if isinstance(v, list):
        return " ".join(str(x) for x in v if not _is_placeholder(x))
    return str(v)


def extract_terms(query, rank_vocab=None):
    terms = set()
    for chunk in re.findall(r"[A-Za-z0-9×'().-]+|[\u4e00-\u9fff]+", query):
        if len(chunk) < 2:
            continue
        if re.fullmatch(r"[\u4e00-\u9fff]+", chunk):
            rank_terms = _rank_terms_from_chunk(chunk, rank_vocab=rank_vocab)
            if rank_terms:
                terms.update(rank_terms)
                continue
            terms.add(_norm(chunk))
            for size in (2, 3, 4):
                for i in range(0, len(chunk) - size + 1):
                    term = chunk[i : i + size]
                    if rank_vocab is not None and re.search(r"[界门纲目科属]", term) and term not in rank_vocab:
                        continue
                    terms.add(term)
        else:
            terms.add(_norm(chunk))
    return {term for term in terms if term not in STOP_TERMS}


def interested_fields(query):
    q = _norm(query)
    fields = []
    for field, hints in FIELD_HINTS.items():
        if any(_norm(hint) in q for hint in hints):
            fields.append(field)
    return fields


def _is_boundary(ch):
    # 句首/句尾（None）与所有非中文字符（拉丁/数字/空白/标点）都算边界。
    if ch is None:
        return True
    if not ("一" <= ch <= "鿿"):
        return True
    return ch in _BOUNDARY_CHARS


def _mentions_single_char(name, query):
    # 单字中文名需以“词边界”出现才算点名：左侧为边界，右侧为边界或指代该植物的后缀。
    for i, ch in enumerate(query):
        if ch != name:
            continue
        left = query[i - 1] if i > 0 else None
        right = query[i + 1] if i + 1 < len(query) else None
        if _is_boundary(left) and (_is_boundary(right) or right in _NAME_SUFFIX_CHARS):
            return True
    return False


def _exact_name_match(value, query):
    if not value or _is_placeholder(value):
        return False
    value = str(value)
    q = query.strip()
    if value == q:
        return True
    if len(value) == 1:
        # 仅“单个中文字符”才走边界匹配；其他单字符值（如单个拉丁字母）保持“只认整串相等”。
        if "一" <= value <= "鿿":
            return _mentions_single_char(value, q)
        return False
    return _norm(value) in _norm(q)


def score_record(record, query, terms, rank_query=False):
    q = _norm(query)
    score = 0
    matched_terms = set()
    matched_fields = set()

    for field in FIELD_ORDER:
        text = _norm(_flatten(record.get(field)))
        if not text:
            continue
        weight = FIELD_WEIGHTS.get(field, 1)
        for term in terms:
            if term in text:
                score += weight * min(len(term), 8)
                matched_terms.add(term)
                matched_fields.add(field)

    for field in ("中文名", "学名"):
        value = record.get(field)
        if not rank_query and _exact_name_match(value, query):
            score += 300 if field == "中文名" else 180
            matched_terms.add(str(value))
            matched_fields.add(field)

    for field in ("俗名", "异名"):
        value = record.get(field)
        values = value if isinstance(value, list) else [value]
        for item in values:
            if not rank_query and _exact_name_match(item, query):
                score += 120
                matched_terms.add(str(item))
                matched_fields.add(field)

    return {
        "score": score,
        "record": record,
        "matched_terms": sorted(matched_terms),
        "matched_fields": sorted(matched_fields, key=lambda f: FIELD_ORDER.index(f) if f in FIELD_ORDER else 999),
    }


def _record_mentioned(record, query):
    values = [record.get("中文名"), record.get("学名")]
    for field in ("俗名", "异名"):
        value = record.get(field)
        values.extend(value if isinstance(value, list) else [value])
    return any(_exact_name_match(value, query) for value in values)


def _has_rank_query(query, rank_vocab=None):
    return any(
        _rank_terms_from_chunk(chunk, rank_vocab=rank_vocab)
        for chunk in re.findall(r"[\u4e00-\u9fff]+", query)
    )


def _is_list_query(query):
    return any(marker in query for marker in LIST_QUERY_MARKERS)


def default_limit(records, query):
    rank_vocab = taxonomy_terms(records)
    if _has_rank_query(query, rank_vocab=rank_vocab) and _is_list_query(query):
        return None
    return 5


def retrieve(records, query, limit=5, min_score=1):
    rank_vocab = taxonomy_terms(records)
    rank_query = _has_rank_query(query, rank_vocab=rank_vocab)
    terms = extract_terms(query, rank_vocab=rank_vocab)
    mentioned = [] if rank_query else [record for record in records if _record_mentioned(record, query)]
    candidates = mentioned if mentioned else records
    hits = [score_record(record, query, terms, rank_query=rank_query) for record in candidates]
    hits = [hit for hit in hits if hit["score"] >= min_score]
    hits.sort(key=lambda h: (-h["score"], h["record"].get("中文名") or ""))
    if limit is None or limit <= 0:
        return hits
    return hits[:limit]


def _format_map(v):
    return "\n".join(f"- {k}: {val}" for k, val in v.items() if not _is_placeholder(val))


def _format_value(v):
    if _is_placeholder(v):
        return ""
    if isinstance(v, dict):
        return _format_map(v)
    if isinstance(v, list):
        return "、".join(str(x) for x in v if not _is_placeholder(x))
    return str(v)


def _selected_fields(query, explicit_fields=None):
    if explicit_fields:
        return [f.strip() for f in explicit_fields.split(",") if f.strip()]
    fields = interested_fields(query)
    if fields:
        for base in ("描述", "分类系统"):
            if base not in fields:
                fields.insert(0, base)
        return fields
    return list(DEFAULT_CONTEXT_FIELDS)


def format_context(hits, query, fields=None, total=None):
    total = len(hits) if total is None else total
    selected = _selected_fields(query, fields)
    lines = [
        "# 检索上下文",
        "",
        f"问题：{query}",
        "",
    ]
    if total == len(hits):
        lines.extend([f"命中记录：{total}", ""])
    else:
        lines.extend([f"总命中记录：{total}", f"显示记录：{len(hits)}", ""])
    if not hits:
        lines.append("未找到匹配记录。")
        return "\n".join(lines)

    for idx, hit in enumerate(hits, 1):
        rec = hit["record"]
        lines.extend(
            [
                f"## {idx}. {rec.get('中文名', '未命名')}",
                "",
                f"- 匹配分数：{hit['score']}",
                f"- 匹配字段：{', '.join(hit['matched_fields']) if hit['matched_fields'] else '无'}",
                f"- 学名：{rec.get('学名', '')}",
            ]
        )
        for field in selected:
            value = _format_value(rec.get(field))
            if value:
                lines.extend(["", f"### {field}", value])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def format_prompt(hits, query, fields=None, total=None):
    context = format_context(hits, query, fields=fields, total=total)
    return "\n".join(
        [
            "请只根据下面资料回答问题。资料中没有的信息，请明确说“资料中未提供”。",
            "回答时优先给出直接结论，再列出依据的物种记录。",
            "",
            context,
        ]
    )


def _json_hits(hits):
    return [
        {
            "score": hit["score"],
            "matched_terms": hit["matched_terms"],
            "matched_fields": hit["matched_fields"],
            "record": hit["record"],
        }
        for hit in hits
    ]


def main():
    ap = argparse.ArgumentParser(description="从 data/ 检索与问题相关的物种记录，生成 AI 可用上下文")
    ap.add_argument("query", nargs="+", help="问题或关键词，例如：臭椿有什么形态特征和用途")
    ap.add_argument("--root", default="data", help="YAML 数据根目录，默认 data")
    ap.add_argument("--limit", type=int, help="最多返回多少条记录；分类列举查询默认返回全部，其余默认 5；0 表示全部")
    ap.add_argument("--min-score", type=int, default=1, help="最低匹配分数，默认 1")
    ap.add_argument("--fields", help="逗号分隔的输出字段，例如：分类系统,形态特征,功用价值")
    ap.add_argument("--json", action="store_true", help="输出结构化 JSON")
    ap.add_argument("--prompt", action="store_true", help="输出可直接发给 AI 的完整提示词")
    args = ap.parse_args()

    query = " ".join(args.query).strip()
    records = load_all(args.root)
    limit = default_limit(records, query) if args.limit is None else args.limit
    all_hits = retrieve(records, query, limit=None, min_score=args.min_score)
    hits = all_hits if limit is None or limit <= 0 else all_hits[:limit]

    if args.json:
        print(
            json.dumps(
                {"query": query, "total_count": len(all_hits), "count": len(hits), "results": _json_hits(hits)},
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.prompt:
        print(format_prompt(hits, query, fields=args.fields, total=len(all_hits)))
    else:
        print(format_context(hits, query, fields=args.fields, total=len(all_hits)))


if __name__ == "__main__":
    main()
