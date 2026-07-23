# retrieve_context 单字中文名检索回归 · 修改方案

- 日期：2026-07-23
- 范围：`scripts/retrieve_context.py`、`tests/test_retrieve_context.py`
- 背景：`fix: harden AI context retrieval matching`（提交 `2999ee5`）修好了三处关键词启发式问题，
  但连带引入一处回归，本方案专门修复它，且不回退已修好的三处。

## 问题

单字中文名（数据里有 9 个：榆/荠/艾/槐/莲/构/桑/桃/杏）写进自然长句被点名时检索不到：

```
'槐的药用价值'  -> 牡丹(24), 构(14), 桃(14)      # 槐 不在 Top3
'桃树怎么修剪'  -> 黄杨(12), 二球悬铃木(10)…       # 桃 不在 Top3
'莲的观赏价值'  -> 大花金鸡菊, 瓜叶菊, 大花萱草      # 莲 不在 Top3
'桑的果实能吃吗' -> 鸡树条(90), 西府海棠(40), 桑(26) # 桑 被噪声压到第3
```

命中的是"药用/价值/观赏"等泛词碰巧匹配的记录，真正被点名的物种被淹没。

## 根因

修 finding 2 时，`_exact_name_match` 对长度 1 的名字**只认整串相等**（`value == query`）；
而 `extract_terms` 的 n-gram 最小长度是 2，**单字永远不会成为检索词**。两者叠加，单字名既不锁定
也不打分，只能靠"整句恰好等于该字"命中——自然句里必然落空。

## 思路

恢复单字名匹配，但用**两侧词边界**判定替代"全句子串"：

- 名字**左侧**须为边界（句首/句尾、虚词、标点、非中文字符）；
- 名字**右侧**为边界，**或**为指代该植物的常见后缀（树/花/叶/果…）。

这样 `桑的果实→桑`、`桃树→桃` 命中，而 `桑拿→桑`、`艾滋→艾`、`构造→构` 不命中（finding 2 不回退）。

## 改动 1 · 新增两个常量

在常量区 `QUESTION_MARKERS = (...)` 之后（约第 75 行）追加：

```python
# 单字中文名“点名”判定用的边界字符：虚词、标点、空白（非中文字符另行判定）。
_BOUNDARY_CHARS = set(
    "的是和与及或有无这那每各某本该其为在对把让从跟向到于也都又还就要会能可想"
    "哪什怎如何吗呢吧啊么了地得着过并且但即"
    "问查看找搜说讲"                       # 常见问句/请求引导动词：请问槐…/帮我查桃…/看看莲…
    "、，,。.；;：:？?！!…（）()「」『』【】《》“”\"'‘’ \t\r\n"
)
# 紧跟在单字名之后、仍指代该植物的常见后缀，如“桃树/槐花/艾叶/桑果”。
# 只保留植物部位/称谓；不要放 属/科/目——分类阶查询已由 taxonomy_terms / rank query 处理，
# 若放进来会让“桃属有哪些”在“桃属”非真实 taxonomy 词时退化成硬锁单株“桃”。
# 末尾 草菜藕葚椹 针对现有单字名的常见问法：艾草 / 荠菜 / 莲藕(莲菜) / 桑葚 / 桑椹。
_NAME_SUFFIX_CHARS = set("树花叶果实子籽苗枝干根皮草菜藕葚椹")
```

## 改动 2 · 新增两个辅助函数

放在 `_exact_name_match` 定义之前（约第 155 行前）：

```python
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
```

## 改动 3 · 替换 `_exact_name_match`

把当前（约第 155–160 行）：

```python
def _exact_name_match(value, query):
    if not value or _is_placeholder(value):
        return False
    value = str(value)
    q = query.strip()
    return value == q or (len(value) > 1 and _norm(value) in _norm(q))
```

改为：

```python
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
```

多字名分支不变（仍子串匹配）；单字名从"仅整串相等"升级为"词边界点名"。该函数被
`_record_mentioned`、`score_record` 的精确名加权、俗名/异名匹配共用，一处改动三处生效——
故对单字中文字符的收窄同时保护了俗名/异名/学名路径（避免对非中文单字符做子串匹配）。

## 改动 4 · 新增回归测试（`tests/test_retrieve_context.py`）

在 `RECORDS = [...]` 之后加构造 helper：

```python
def _rec(name, latin, **over):
    base = {
        "学名": latin, "中文名": name, "俗名": "无", "异名": "无",
        "描述": "暂无数据", "分类系统": "暂无数据", "物种保护": "暂无数据",
        "分类信息": "暂无数据", "形态特征": "暂无数据", "生态习性": "暂无数据",
        "功用价值": "暂无数据", "植物志": "暂无数据",
        "元数据": {"来源文件": "x.xlsx", "来源工作表": name},
    }
    base.update(over)
    return base
```

在 `TestRetrieveContext` 内新增以下 **5 个** 回归测试（勿删减）：

```python
    def test_single_char_name_matched_in_compound_query(self):
        # 回归防护：单字名物种在“X的…/X树…”式长句里被点名，应检索到，
        # 且必须是靠“中文名点名加权”命中——故断言“中文名”进入 matched_fields，
        # 并加一条含相同泛词（药用/价值）的干扰记录：若单字匹配没修好，牡丹会
        # 靠内容词与 槐 并列/反超，两条断言都会失败，避免测试假通过。
        records = [
            _rec("槐", "Styphnolobium japonicum (L.) Schott",
                 功用价值={"药用": "花蕾入药，清热"}),
            _rec("牡丹", "Paeonia × suffruticosa Andrews",
                 功用价值={"药用": "根皮入药，称丹皮", "观赏": "花大艳丽，价值高"}),
        ]
        for q in ("槐的药用价值", "槐树怎么修剪"):
            hits = retrieve(records, q)
            self.assertEqual([h["record"]["中文名"] for h in hits], ["槐"], q)
            self.assertIn("中文名", hits[0]["matched_fields"])

    def test_single_char_name_not_locked_by_unrelated_substring(self):
        # finding 2 不回退：单字名恰是无关词子串时不得误锁。
        records = [
            _rec("桑", "Morus alba L."),
            _rec("艾", "Artemisia argyi H.Lév. & Vaniot"),
            _rec("构", "Broussonetia papyrifera (L.) L'Hér. ex Vent."),
        ]
        for q in ("桑拿房很热", "艾滋病", "地质构造分析"):
            self.assertEqual(retrieve(records, q), [], q)

    def test_single_char_name_matched_after_leading_verb(self):
        # 自然问句常带引导动词（请问/帮我查/看看），单字名左邻是动词时也应命中。
        records = [_rec("槐", "Styphnolobium japonicum (L.) Schott",
                        功用价值={"药用": "花蕾入药，清热"}),
                   _rec("桃", "Prunus persica (L.) Batsch",
                        形态特征={"花": "先叶开放，粉红"})]
        cases = {"请问槐的药用价值": "槐", "帮我查桃树怎么修剪": "桃", "看看槐花": "槐"}
        for q, expected in cases.items():
            hits = retrieve(records, q)
            self.assertEqual([h["record"]["中文名"] for h in hits], [expected], q)

    def test_single_char_name_matched_with_plant_part_suffix(self):
        # 常见“衍生词”后缀：艾草 / 荠菜 / 莲藕 / 桑葚 应命中对应单字名。
        records = [
            _rec("艾", "Artemisia argyi H.Lév. & Vaniot", 功用价值={"药用": "全草入药"}),
            _rec("荠", "Capsella bursa-pastoris (L.) Medik."),
            _rec("莲", "Nelumbo nucifera Gaertn."),
            _rec("桑", "Morus alba L."),
        ]
        cases = {"艾草有什么用": "艾", "荠菜能吃吗": "荠", "莲藕怎么做": "莲", "桑葚甜吗": "桑"}
        for q, expected in cases.items():
            hits = retrieve(records, q)
            self.assertEqual([h["record"]["中文名"] for h in hits], [expected], q)

    def test_plant_part_suffix_does_not_falsely_lock(self):
        # 后缀字出现在无关词里（前面不是单字名）时不得误锁。
        records = [_rec("桑", "Morus alba L."), _rec("艾", "Artemisia argyi H.Lév. & Vaniot")]
        for q in ("白菜炒肉", "花草茶很香", "藕断丝连"):
            self.assertEqual(retrieve(records, q), [], q)
```

## 验证方法与预期

```bash
# ① 回归修复 + finding 2 不回退（真实 107 物种）
python3 - <<'PY'
import sys; sys.path.insert(0, '.')
from scripts.export import load_all
from scripts.retrieve_context import retrieve
recs = load_all('data')
for q in ['槐的药用价值', '桃树怎么修剪', '莲的观赏价值', '桑的果实能吃吗',
          '请问槐的药用价值', '帮我查桃树怎么修剪',   # 问句引导动词左边界
          '艾草有什么用', '荠菜能吃吗', '莲藕怎么做', '桑葚甜吗']:   # 衍生词后缀
    print('FIX  ', q, '->', [h['record']['中文名'] for h in retrieve(recs, q, limit=3)])
# 只验证“不再硬锁”，故用与植物内容无重叠的词；不要用“艾滋病的防治”——
# “防治”是 艾 记录里的真实内容词，属另一类“内容词噪声”，不在本方案范围内。
for q in ['艾滋病', '桑拿房', '构造地质']:
    print('LOCK?', q, '->', [h['record']['中文名'] for h in retrieve(recs, q, limit=3)])
PY

# ② 全量测试（应仍全绿，且新增 5 项：54 -> 59）
python3 -m unittest discover -s tests
```

预期：

- `FIX` 前四条 Top1 为 槐 / 桃 / 莲 / 桑；带“请问/帮我查”两条命中 槐 / 桃；带衍生词后缀四条
  （艾草/荠菜/莲藕/桑葚）命中 艾 / 荠 / 莲 / 桑；
- `LOCK?` 三条不再把 艾/桑/构 硬锁到候选集（应为空）；
- 单测 54 → 59，全绿；
- finding 1/3 不受影响（未动 `taxonomy_terms`、rank 逻辑、`FIELD_ORDER`）。

> 范围说明（据 Codex 复审）：
> 1. 本方案只消除“单字名子串硬锁”，**不**处理“内容词噪声”（如 `艾滋病的防治` 因 艾 记录含
>    “防治”而命中）。后者若要过滤，需要额外的“非植物/医学问题”识别，属独立话题，不在此方案内。
> 2. 左边界只补了**单字**引导动词（问/查/看/找/搜/说/讲）。以**多字动词**结尾引出的问法
>    （如 `介绍莲…` 的“绍”、`了解桑…` 的“解”）仍可能漏；这类词尾字五花八门，硬加进边界表会
>    过度膨胀且易误伤，故不覆盖。需要时用户可改说 `莲的观赏价值` 这类直接问法。

## 影响面

- 仅改 `_exact_name_match` 及新增两个纯函数 + 两个常量；`retrieve/score_record/_record_mentioned`
  的调用签名不变。
- 多字名、分类阶查询、元数据剔除等既有行为不变，现有 54 测试不受影响。
- 边界字符表可按需增补；如需 `莲蓬→莲` 这类"果实别称"也命中，可把 `蓬` 等加进
  `_NAME_SUFFIX_CHARS`（默认不加，优先保精确）。
```
