import re
import zipfile
import xml.etree.ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_COL_RE = re.compile(r"^([A-Z]+)\d+$")


def col_letter(ref):
    m = _COL_RE.match(ref)
    if not m:
        raise ValueError(f"bad cell ref: {ref}")
    return m.group(1)


def _shared_strings(zf):
    strings = []
    with zf.open("xl/sharedStrings.xml") as fh:
        root = ET.parse(fh).getroot()
    for si in root:
        strings.append("".join(t.text or "" for t in si.iter(NS + "t")))
    return strings


def _sheet_targets(zf):
    """返回 [(sheet_name, worksheet_xml_path), ...]，顺序同 workbook。"""
    wb = ET.fromstring(zf.read("xl/workbook.xml"))
    rels_xml = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
    rns = "{http://schemas.openxmlformats.org/package/2006/relationships}"
    rid_to_target = {r.get("Id"): r.get("Target") for r in rels_xml.findall(rns + "Relationship")}
    r_attr = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
    out = []
    for s in wb.find(NS + "sheets").findall(NS + "sheet"):
        name = s.get("name")
        target = rid_to_target[s.get(r_attr)]
        if not target.startswith("xl/"):
            target = "xl/" + target
        out.append((name, target))
    return out


def read_sheets(path):
    result = []
    with zipfile.ZipFile(path) as zf:
        strings = _shared_strings(zf)
        for name, target in _sheet_targets(zf):
            if name == "WpsReserved_CellImgList":
                continue
            ws = ET.fromstring(zf.read(target))
            sheet_data = ws.find(NS + "sheetData")
            rows = []
            for row in sheet_data.findall(NS + "row"):
                cells = {"r": int(row.get("r"))}
                for c in row.findall(NS + "c"):
                    col = col_letter(c.get("r"))
                    if col not in ("A", "B", "C"):   # 只保留 A/B/C，忽略 D 列起的 DISPIMG 图片公式
                        continue
                    v = c.find(NS + "v")
                    if v is None or v.text is None:
                        continue
                    val = strings[int(v.text)] if c.get("t") == "s" else v.text
                    if val != "":
                        cells[col] = val
                if len(cells) > 1:
                    rows.append(cells)
            rows.sort(key=lambda r: r["r"])   # 保证按行号升序（不依赖文档顺序）
            result.append((name, rows))
    return result
