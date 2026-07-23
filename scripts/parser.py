import re

SECTIONS = ("分类系统", "物种保护", "分类信息", "形态特征", "生态习性", "功用价值")
_SPLIT_RE = re.compile(r"[、,，]")
_CJK = re.compile(r"[一-鿿]")   # 判断是否含中文（异名应为纯拉丁名）
_IMG = re.compile(r"下图|上图|图片|如图|见图")   # 图片说明文字，不应进入植物志
_SYN_RE = re.compile(r"[  ]*\(synonym\)\s*$")


def _clean_key(s):
    return s.rstrip("：: ").strip()


def _clean_val(s):
    return s.rstrip("；; ").strip()


def _clean_syn(s):
    return _SYN_RE.sub("", s).strip()


def parse_species(rows, source_file, sheet_name):
    name = xueming = None
    desc_lines, common, synonyms, flora, notes = [], [], [], [], []
    sections = {s: {} for s in SECTIONS}   # 各区块的有序子键映射
    section = None                          # 当前所在区块
    last_key = None                         # 当前区块最近写入的子键（用于续行拼接）
    in_flora = False                        # 是否已进入尾部“植物志”文本块
    prev_row = None                         # 上一有内容行的行号（用于探测空行间隔）

    def _add_syn(val):
        # 异名应为纯拉丁名；含中文的行是说明性文字 → 备注，不当作异名。
        if _CJK.search(val):
            notes.append(val)
        else:
            synonyms.append(_clean_syn(val))

    for row in rows:
        rn = row["r"]
        A = row.get("A")
        B = row.get("B")
        C = row.get("C")

        if A == "学名":
            section = "学名"; xueming = (B or "").strip(); prev_row = rn; continue
        if A == "中文名":
            section = "中文名"; name = (B or "").strip(); prev_row = rn; continue
        if A == "俗名":
            section = "俗名"
            if B:
                common = [p.strip() for p in _SPLIT_RE.split(B) if p.strip()]
            prev_row = rn; continue
        if A == "异名":
            section = "异名"
            if B:
                _add_syn(B)
            prev_row = rn; continue
        if A in SECTIONS:
            section = A; last_key = None; in_flora = False
            if B and C:
                last_key = _clean_key(B)
                sections[A][last_key] = _clean_val(C)
            elif B or C:
                notes.append((B or "") + (C or ""))   # 区块标题行的异常内容
            prev_row = rn; continue

        # A 为空：延续当前区块
        if section == "异名":
            if B and C:
                notes.append(_clean_key(B) + "：" + _clean_val(C))   # 异名段内的表格行（如对比表）→ 备注
            elif B:
                _add_syn(B)
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
                in_flora = False
            elif B:
                notes.append(B)                        # B 有值 C 为空 → 兜底，不丢弃
            elif C:
                if section == "分类系统" or last_key is None:
                    notes.append(C.strip())            # 分类阶值是原子的，脚注 → 备注
                elif _IMG.search(C):
                    notes.append(C.strip())            # 图片说明文字 → 备注，不污染植物志
                elif in_flora:
                    flora.append(C.strip())            # 已在植物志块内，继续累积
                elif prev_row is not None and rn > prev_row + 1:
                    in_flora = True                    # 空行间隔后的无标签文本 = 植物志起始
                    flora.append(C.strip())
                else:
                    sections[section][last_key] += "\n" + C.strip()   # 紧接上一行 → 续接子键
        elif B or C:
            notes.append((B or "") + (C or ""))        # 兜底，不丢弃

        prev_row = rn

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
