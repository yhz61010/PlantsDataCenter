import re

SECTIONS = ("分类系统", "物种保护", "分类信息", "形态特征", "生态习性", "功用价值")
_SPLIT_RE = re.compile(r"[、,，]")
_SYN_RE = re.compile(r"[  ]*\(synonym\)\s*$")


def _clean_key(s):
    return s.rstrip("：: ").strip()


def _clean_val(s):
    return s.rstrip("；; ").strip()


def _clean_syn(s):
    return _SYN_RE.sub("", s).strip()


def parse_species(rows, source_file, sheet_name):
    name = xueming = desc = None
    common, synonyms, flora, notes = [], [], [], []
    sections = {s: {} for s in SECTIONS}   # 各区块的有序子键映射
    section = None                          # 当前所在区块
    seen_section = False                    # 是否已进入过任一区块（用于区分 描述 vs 植物志）

    for row in rows:
        A = row.get("A")
        B = row.get("B")
        C = row.get("C")

        if A == "学名":
            section = "学名"; xueming = (B or "").strip(); continue
        if A == "中文名":
            section = "中文名"; name = (B or "").strip(); continue
        if A == "俗名":
            section = "俗名"
            if B:
                common = [p.strip() for p in _SPLIT_RE.split(B) if p.strip()]
            continue
        if A == "异名":
            section = "异名"
            if B:
                synonyms.append(_clean_syn(B))
            continue
        if A in SECTIONS:
            section = A; seen_section = True
            if B and C:
                sections[A][_clean_key(B)] = _clean_val(C)
            continue

        # A 为空：延续当前区块
        if section == "异名":
            if B:
                synonyms.append(_clean_syn(B))
            elif C:
                if not seen_section:          # 异名后、首区块前的无标签段 = 描述
                    desc = C.strip(); section = "描述"
                else:
                    flora.append(C.strip())
        elif section == "描述":
            if C:
                desc = (desc or "") + C.strip()
        elif section in SECTIONS:
            if B and C:
                sections[section][_clean_key(B)] = _clean_val(C)
            elif C:                           # 区块后无标签文本 = 植物志
                flora.append(C.strip())
        elif B or C:
            notes.append((B or "") + (C or ""))   # 兜底，不丢弃

    out = {}
    out["学名"] = xueming or "暂无数据"
    out["中文名"] = name or sheet_name
    out["俗名"] = common if common else "无"
    out["异名"] = synonyms if synonyms else "无"
    out["描述"] = desc if desc else "暂无数据"
    for sec in SECTIONS:
        out[sec] = sections[sec] if sections[sec] else "暂无数据"
    out["植物志"] = "\n".join(flora) if flora else "暂无数据"
    out["元数据"] = {"来源文件": source_file, "来源工作表": sheet_name}
    if notes:
        out["备注"] = "\n".join(notes)
        print(f"WARN: {source_file}/{sheet_name} 有 {len(notes)} 段无法归类，已存入 备注")
    return out
