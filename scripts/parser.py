import re

SECTIONS = ("分类系统", "物种保护", "分类信息", "形态特征", "生态习性", "功用价值")
_SPLIT_RE = re.compile(r"[、,，]")
_SYN_RE = re.compile(r"[  ]*\(synonym\)\s*$")


def _clean_key(s):
    return s.rstrip("：: ").strip()


def _clean_val(s):
    return s.rstrip("；; ").strip()


def _clean_syn(s):
    return _SYN_RE.sub("", s).strip()


def parse_species(rows, source_file, sheet_name):
    # 预扫描：最后一个含非空 B 的行号。其后的 C-only 文本才是尾部“植物志”；
    # 其前的 C-only 文本是上一子键的续行（或分类系统里的脚注 → 备注）。
    last_labeled = 0
    for row in rows:
        if row.get("B"):
            last_labeled = row["r"]

    name = xueming = None
    desc_lines, common, synonyms, flora, notes = [], [], [], [], []
    sections = {s: {} for s in SECTIONS}   # 各区块的有序子键映射
    section = None                          # 当前所在区块
    last_key = None                         # 当前区块最近写入的子键（用于续行拼接）

    for row in rows:
        rn = row["r"]
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
            section = A; last_key = None
            if B and C:
                last_key = _clean_key(B)
                sections[A][last_key] = _clean_val(C)
            elif B or C:
                notes.append((B or "") + (C or ""))   # 区块标题行的异常内容
            continue

        # A 为空：延续当前区块
        if section == "异名":
            if B:
                synonyms.append(_clean_syn(B))
            elif C:                                    # 异名后、首区块前的无标签段 = 描述
                desc_lines.append(C.strip()); section = "描述"
        elif section == "描述":
            if C:
                desc_lines.append(C.strip())
            elif B:
                notes.append(B)                        # 描述段里的 B-only：兜底
        elif section in SECTIONS:
            if B and C:
                last_key = _clean_key(B)
                sections[section][last_key] = _clean_val(C)
            elif rn > last_labeled and C:              # 尾部无标签文本 → 植物志
                flora.append(C.strip())
            elif C:                                    # 区块内插入的 C-only 文本
                if section == "分类系统" or last_key is None:
                    notes.append(C.strip())            # 分类阶值是原子的，脚注 → 备注
                else:
                    sections[section][last_key] += "\n" + C.strip()   # 续接上一子键
            elif B:
                notes.append(B)                        # B 有值 C 为空 → 兜底，不丢弃
        elif B or C:
            notes.append((B or "") + (C or ""))        # 兜底，不丢弃

    out = {}
    out["学名"] = xueming or "暂无数据"
    out["中文名"] = name or sheet_name
    out["俗名"] = common if common else "无"
    out["异名"] = synonyms if synonyms else "无"
    out["描述"] = "\n".join(desc_lines) if desc_lines else "暂无数据"
    for sec in SECTIONS:
        out[sec] = sections[sec] if sections[sec] else "暂无数据"
    out["植物志"] = "\n".join(flora) if flora else "暂无数据"
    out["元数据"] = {"来源文件": source_file, "来源工作表": sheet_name}
    if notes:
        out["备注"] = "\n".join(notes)
        print(f"WARN: {source_file}/{sheet_name} 有 {len(notes)} 段无法归类，已存入 备注")
    return out
