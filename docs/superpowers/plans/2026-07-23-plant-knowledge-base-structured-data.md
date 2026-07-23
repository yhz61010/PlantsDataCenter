# 植物知识库 · 结构化数据仓库 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `knowledge/` 下的 WPS xlsx 一次性导入为每物种一个 YAML 的纯文本真相源，并提供校验与 JSON/Markdown/SQLite 导出。

**Architecture:** 单向管线（方案 A）。`import_xlsx.py` 一次性把 xlsx 转成 `data/<科>/<物种>.yaml`；`validate.py` 校验源；`export.py` 从源派生 `dist/` 下的 JSON/Markdown/SQLite。底层 xlsx 解析拆成 `xlsx_reader.py`（读单元格网格）与 `parser.py`（网格 → 物种字典）两个可独立测试的模块。

**Tech Stack:** Python 3.11 标准库（`zipfile`、`xml.etree`、`sqlite3`、`json`、`unittest`）+ 系统预装 `PyYAML 6.0`。零第三方安装。测试用 `python3 -m unittest`。

- 仅用 Python 3.11 stdlib + 系统预装 `PyYAML 6.0`；**不得** `pip install` 任何包。
- 所有源码放 `scripts/`，测试放 `tests/`，数据源放 `data/`，派生物放 `dist/`（git 忽略）。
- YAML 写出统一用 `yaml.safe_dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False, width=4096)`——中文不转义、字段顺序稳定、长行不折断。
- 遍历工作表时**跳过** `WpsReserved_CellImgList`；只用 A/B/C 列，忽略 D 列 `DISPIMG` 图片公式。
- `sharedStrings.xml` 按 `<si>` **合并其内所有 `<t>` run** 为一个字符串。
- 清洗：子键去尾部 `：`/`:`，值去尾部 `；`/`;` 与首尾空白；异名去尾部 `\xa0(synonym)` / ` (synonym)`。保留拼音声调符号。
- **固定字段与顺序**（每个 YAML 必须全含）：`学名 中文名 俗名 异名 描述 分类系统 物种保护 分类信息 形态特征 生态习性 功用价值 植物志 元数据`。
- **区块标题集合**（A 列）：`分类系统 物种保护 分类信息 形态特征 生态习性 功用价值`（`植物志` 无标题，来自尾部无标签文本）。
- **缺失即补占位**：`俗名`/`异名` 缺失 → 字符串 `"无"`；`描述` 与六个区块、`植物志` 缺失 → 字符串 `"暂无数据"`。
- **两处无标签自由文本**：`异名` 后、首个区块前的 C 段 → `描述`；进入区块后出现的 C 段（B 空）→ `植物志`（多行合并）。
- 遇无法归类的结构**不静默丢弃**：保留原文到 `备注` 字段并 `print` 一条 `WARN`。
- 中文物种名做文件名；**中文科名从源 xlsx 文件名派生**（`KM-苦木科.xlsx` → `苦木科`），不依赖可能缺失的 `分类系统.科`。
- 全部 19 个 xlsx 可读，共 42 个物种；第一阶段图片忽略，不导出图片文件。

---

### Task 1: 仓库脚手架与 git 初始化

**Files:**
- Create: `.gitignore`
- Create: `scripts/__init__.py`（空）
- Create: `tests/__init__.py`（空）
- Create: `schema/plant.schema.md`

**Interfaces:**
- Consumes: 无
- Produces: 目录骨架 `scripts/`、`tests/`、`schema/`、`data/`、`dist/`；git 仓库。

- [ ] **Step 1: 初始化 git 并建目录**

Run:
```bash
cd /home/coding04/yhz61010/Documents/PlantsDataCenter
git init
mkdir -p scripts tests schema data dist
touch scripts/__init__.py tests/__init__.py
```
Expected: `Initialized empty Git repository`。

- [ ] **Step 2: 写 `.gitignore`**

```gitignore
# 派生导出物，可由 export.py 重建
dist/
# Python
__pycache__/
*.pyc
# subagent-driven 执行台账（scratch）
.superpowers/
```

- [ ] **Step 3: 写 `schema/plant.schema.md`**（人读的权威字段定义）

````markdown
# 物种 YAML 字段规范

每个 `data/<中文科名>/<中文物种名>.yaml` **必须包含以下全部字段，顺序固定**。
缺失字段也要补出占位值（俗名/异名 → `"无"`；其余 → `"暂无数据"`）。

| 顺序 | 字段 | 类型 | 缺失占位 | 说明 |
| --- | --- | --- | --- | --- |
| 1 | 学名 | str | （必填真实值） | 拉丁二名法，如 `Ailanthus altissima (Mill.) Swingle` |
| 2 | 中文名 | str | （必填真实值） | 中文名称，等于文件名 |
| 3 | 俗名 | list[str] 或 str | `"无"` | 别名，按 `、`/`,` 拆分 |
| 4 | 异名 | list[str] 或 str | `"无"` | 拉丁异名，已去除 `(synonym)` 标记，每个一行 |
| 5 | 描述 | str | `"暂无数据"` | 异名后、首区块前的无标签概述段 |
| 6 | 分类系统 | map 或 str | `"暂无数据"` | 键为 `界 门 纲 目 科 属`，值为 `拉丁名-中文(拼音)` |
| 7 | 物种保护 | map 或 str | `"暂无数据"` | 开放子键（濒危等级…） |
| 8 | 分类信息 | map 或 str | `"暂无数据"` | 开放子键（属种数/模式产地…） |
| 9 | 形态特征 | map 或 str | `"暂无数据"` | 开放子键（识别要点/生活型/株/茎/枝/叶/花/果/种子…） |
| 10 | 生态习性 | map 或 str | `"暂无数据"` | 开放子键（产地/分布/生境/海拔/物候…） |
| 11 | 功用价值 | map 或 str | `"暂无数据"` | 开放子键（经济价值/植物文化…） |
| 12 | 植物志 | str | `"暂无数据"` | 尾部无标签文本合并（文献引证、变种描述、下级分类） |
| 13 | 元数据 | map | （必填） | `来源文件`、`来源工作表` |
| — | 备注 | str | （仅异常时出现） | 导入时无法归类的原文兜底 |

分类阶元值格式正则：`^[A-Z][A-Za-z ]+-.+\(.+\)$`
````

- [ ] **Step 4: Commit**

```bash
git add .gitignore scripts/__init__.py tests/__init__.py schema/plant.schema.md CLAUDE.md knowledge/ docs/
git commit -m "chore: scaffold structured-data repo (dirs, gitignore, schema)"
```

---

### Task 2: xlsx 单元格网格读取器

**Files:**
- Create: `scripts/xlsx_reader.py`
- Test: `tests/test_xlsx_reader.py`

**Interfaces:**
- Consumes: 无
- Produces:
  - `col_letter(ref: str) -> str` —— `"C11"` → `"C"`。
  - `read_sheets(path: str) -> list[tuple[str, list[dict]]]` —— 返回 `[(sheet_name, rows), ...]`，已跳过 `WpsReserved_CellImgList`。每个 `row` 是 `{'r': int, 'A': str, 'B': str, ...}`，只含非空单元格，按行号升序。

- [ ] **Step 1: 写失败测试 `tests/test_xlsx_reader.py`**

```python
import unittest
from scripts.xlsx_reader import col_letter, read_sheets

KM = "knowledge/KM-苦木科.xlsx"

class TestXlsxReader(unittest.TestCase):
    def test_col_letter(self):
        self.assertEqual(col_letter("A1"), "A")
        self.assertEqual(col_letter("C11"), "C")
        self.assertEqual(col_letter("AB123"), "AB")

    def test_read_sheets_skips_image_sheet_and_reads_grid(self):
        sheets = read_sheets(KM)
        names = [n for n, _ in sheets]
        self.assertEqual(names, ["臭椿"])            # 图片表已跳过（KM 无图片表，仍应只有臭椿）
        rows = dict((r["r"], r) for _, rows in sheets for r in rows)
        self.assertEqual(rows[1]["A"], "学名")
        self.assertEqual(rows[1]["B"], "Ailanthus altissima (Mill.) Swingle")
        self.assertEqual(rows[17]["C"], "Simaroubaceae-苦木科(kǔ mù kē)")
        self.assertEqual(rows[4]["B"], "Toxicodendron altissimum\xa0(synonym)")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m unittest tests.test_xlsx_reader -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'scripts.xlsx_reader'`

- [ ] **Step 3: 实现 `scripts/xlsx_reader.py`**

```python
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
                    v = c.find(NS + "v")
                    if v is None or v.text is None:
                        continue
                    val = strings[int(v.text)] if c.get("t") == "s" else v.text
                    if val != "":
                        cells[col_letter(c.get("r"))] = val
                if len(cells) > 1:
                    rows.append(cells)
            result.append((name, rows))
    return result
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m unittest tests.test_xlsx_reader -v`
Expected: PASS（2 tests）

- [ ] **Step 5: Commit**

```bash
git add scripts/xlsx_reader.py tests/test_xlsx_reader.py
git commit -m "feat: xlsx cell-grid reader (stdlib zip+xml, skips image sheet)"
```

---

### Task 3: 物种网格解析器

**Files:**
- Create: `scripts/parser.py`
- Test: `tests/test_parser.py`

**Interfaces:**
- Consumes: `read_sheets` 产出的 `rows`（list[dict]，每行 `{'r':int,'A':..,'B':..,'C':..}`）。
- Produces: `parse_species(rows: list[dict], source_file: str, sheet_name: str) -> dict` —— 返回**固定顺序且字段齐全**的字典，键顺序：`学名, 中文名, 俗名, 异名, 描述, 分类系统, 物种保护, 分类信息, 形态特征, 生态习性, 功用价值, 植物志, 元数据[, 备注]`。缺失字段补占位（俗名/异名→`"无"`，其余→`"暂无数据"`）。

- [ ] **Step 1: 写失败测试 `tests/test_parser.py`**

```python
import os
import unittest
from scripts.xlsx_reader import read_sheets
from scripts.parser import parse_species

def load(path, sheet):
    for name, rows in read_sheets(path):
        if name == sheet:
            return parse_species(rows, os.path.basename(path), name)
    raise AssertionError(f"未找到工作表 {sheet}")

class TestParser(unittest.TestCase):
    def test_km_scalars_desc_and_field_order(self):
        r = load("knowledge/KM-苦木科.xlsx", "臭椿")
        self.assertEqual(r["学名"], "Ailanthus altissima (Mill.) Swingle")
        self.assertEqual(r["中文名"], "臭椿")
        self.assertEqual(len(r["俗名"]), 9)
        self.assertEqual(len(r["异名"]), 6)
        self.assertTrue(r["描述"].startswith("落叶乔木，高可达20米"))
        self.assertEqual(
            list(r.keys())[:13],
            ["学名","中文名","俗名","异名","描述","分类系统","物种保护",
             "分类信息","形态特征","生态习性","功用价值","植物志","元数据"],
        )

    def test_km_taxonomy_and_morphology(self):
        r = load("knowledge/KM-苦木科.xlsx", "臭椿")
        self.assertEqual(r["分类系统"]["科"], "Simaroubaceae-苦木科(kǔ mù kē)")
        self.assertEqual(list(r["分类系统"].keys()), ["界","门","纲","目","科","属"])
        self.assertEqual(r["形态特征"]["生活型"], "落叶乔木")
        self.assertEqual(r["形态特征"]["叶"][:6], "奇数羽状复叶")
        self.assertNotIn("：", "".join(r["形态特征"].keys()))

    def test_km_synonym_marker_stripped(self):
        r = load("knowledge/KM-苦木科.xlsx", "臭椿")
        self.assertEqual(r["异名"][0], "Toxicodendron altissimum")
        self.assertNotIn("synonym", "".join(r["异名"]))

    def test_km_missing_sections_get_placeholder(self):
        r = load("knowledge/KM-苦木科.xlsx", "臭椿")
        self.assertEqual(r["物种保护"], "暂无数据")
        self.assertEqual(r["分类信息"], "暂无数据")
        self.assertEqual(r["功用价值"], "暂无数据")
        self.assertEqual(r["生态习性"]["物候"], "花期4-5月，果期8-10月")
        self.assertTrue(r["植物志"].startswith("本种在石灰岩地区"))   # 尾部无标签文本

    def test_hua_full_sections_and_flora(self):
        r = load("knowledge/D-豆科.xlsx", "槐")
        self.assertEqual(r["分类信息"]["模式产地"], "模式标本采自四川成都附近")
        self.assertEqual(r["功用价值"]["经济价值"][:4], "树冠优美")
        self.assertTrue(r["植物志"].startswith("20. 槐"))
        self.assertIn("下级分类", r["植物志"])

    def test_baihe_missing_desc_and_protection(self):
        r = load("knowledge/BH-百合科.xlsx", "百合")
        self.assertEqual(r["描述"], "暂无数据")           # 百合无概述段
        self.assertEqual(r["物种保护"]["濒危等级"], "无")
        self.assertEqual(r["异名"][0], "Lilium odorum")

    def test_metadata(self):
        r = load("knowledge/KM-苦木科.xlsx", "臭椿")
        self.assertEqual(r["元数据"]["来源文件"], "KM-苦木科.xlsx")
        self.assertEqual(r["元数据"]["来源工作表"], "臭椿")

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m unittest tests.test_parser -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'scripts.parser'`

- [ ] **Step 3: 实现 `scripts/parser.py`**

```python
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
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m unittest tests.test_parser -v`
Expected: PASS（7 tests）

- [ ] **Step 5: Commit**

```bash
git add scripts/parser.py tests/test_parser.py
git commit -m "feat: species parser (7 sections, desc/flora split, placeholder defaults)"
```

---

### Task 4: YAML 写出与 import_xlsx.py CLI

**Files:**
- Create: `scripts/yaml_io.py`
- Create: `scripts/import_xlsx.py`
- Test: `tests/test_import.py`

**Interfaces:**
- Consumes: `parse_species`（Task 3）、`read_sheets`（Task 2）。
- Produces:
  - `yaml_io.dump_species(rec: dict) -> str` —— 统一参数序列化。
  - `import_xlsx.family_dir(xlsx_path: str) -> str` —— 从**源文件名**取中文科名（`KM-苦木科.xlsx` → `苦木科`）。
  - `import_xlsx.import_file(xlsx_path, out_root="data") -> list[str]` —— 写出并返回生成的 yaml 路径列表。
  - CLI：`python3 scripts/import_xlsx.py <xlsx...> [--out data] [--dry-run]`。

- [ ] **Step 1: 写失败测试 `tests/test_import.py`**

```python
import os, shutil, tempfile, unittest
import yaml
from scripts.import_xlsx import import_file, family_dir

class TestImport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_family_dir_from_filename(self):
        self.assertEqual(family_dir("knowledge/KM-苦木科.xlsx"), "苦木科")
        self.assertEqual(family_dir("knowledge/MX-木樨科.xlsx"), "木樨科")

    def test_import_writes_yaml_that_roundtrips(self):
        paths = import_file("knowledge/KM-苦木科.xlsx", out_root=self.tmp)
        self.assertEqual(len(paths), 1)
        p = paths[0]
        self.assertTrue(p.endswith(os.path.join("苦木科", "臭椿.yaml")))
        with open(p, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        self.assertEqual(data["中文名"], "臭椿")
        self.assertEqual(data["分类系统"]["属"], "Ailanthus-臭椿属(chòu chūn shǔ)")
        self.assertEqual(data["元数据"]["来源工作表"], "臭椿")

    def test_all_fields_present_with_placeholders(self):
        paths = import_file("knowledge/KM-苦木科.xlsx", out_root=self.tmp)
        data = yaml.safe_load(open(paths[0], encoding="utf-8"))
        self.assertEqual(data["功用价值"], "暂无数据")
        self.assertEqual(data["物种保护"], "暂无数据")
        self.assertEqual(
            list(data.keys())[:5], ["学名","中文名","俗名","异名","描述"])

    def test_yaml_is_unicode_not_escaped(self):
        paths = import_file("knowledge/KM-苦木科.xlsx", out_root=self.tmp)
        text = open(paths[0], encoding="utf-8").read()
        self.assertIn("臭椿", text)
        self.assertNotIn("\\u", text)

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m unittest tests.test_import -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'scripts.import_xlsx'`

- [ ] **Step 3: 实现 `scripts/yaml_io.py`**

```python
import yaml


def dump_species(rec):
    return yaml.safe_dump(
        rec,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=4096,
    )
```

- [ ] **Step 4: 实现 `scripts/import_xlsx.py`**

```python
import argparse
import os

from scripts.xlsx_reader import read_sheets
from scripts.parser import parse_species
from scripts.yaml_io import dump_species


def family_dir(xlsx_path):
    base = os.path.splitext(os.path.basename(xlsx_path))[0]   # "KM-苦木科"
    return base.split("-", 1)[1].strip() if "-" in base else base


def import_file(xlsx_path, out_root="data", dry_run=False):
    src = os.path.basename(xlsx_path)
    fam = family_dir(xlsx_path)
    written = []
    for sheet_name, rows in read_sheets(xlsx_path):
        rec = parse_species(rows, src, sheet_name)
        fname = (rec.get("中文名") or sheet_name) + ".yaml"
        out_path = os.path.join(out_root, fam, fname)
        if dry_run:
            print(f"[dry-run] {out_path}")
            written.append(out_path)
            continue
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            fh.write(dump_species(rec))
        written.append(out_path)
        print(f"写出 {out_path}")
    return written


def main():
    ap = argparse.ArgumentParser(description="导入 WPS xlsx 为物种 YAML")
    ap.add_argument("xlsx", nargs="+")
    ap.add_argument("--out", default="data")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    total = 0
    for x in args.xlsx:
        total += len(import_file(x, out_root=args.out, dry_run=args.dry_run))
    print(f"完成，共 {total} 个物种")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: 跑测试确认通过**

Run: `python3 -m unittest tests.test_import -v`
Expected: PASS（4 tests）

- [ ] **Step 6: 手工验证单科端到端**

Run: `python3 scripts/import_xlsx.py knowledge/KM-苦木科.xlsx && cat data/苦木科/臭椿.yaml`
Expected: 打印 `写出 data/苦木科/臭椿.yaml`；YAML 含全部 13 个固定字段，缺失区块（物种保护/分类信息/功用价值）为 `暂无数据`，尾部文本进入 `植物志`，中文正常、无 `\u` 转义。人工比对与原表一致。

- [ ] **Step 7: Commit**

```bash
git add scripts/yaml_io.py scripts/import_xlsx.py tests/test_import.py data/苦木科/臭椿.yaml
git commit -m "feat: import_xlsx CLI writes per-species YAML source"
```

---

### Task 5: 校验器 validate.py

**Files:**
- Create: `scripts/validate.py`
- Test: `tests/test_validate.py`

**Interfaces:**
- Consumes: `data/**/*.yaml`（Task 4 产物）。
- Produces:
  - `validate_record(rec: dict, path: str) -> list[str]` —— 返回该记录的错误信息列表（空=通过）。
  - `validate_tree(root="data") -> list[str]` —— 汇总全部错误。
  - CLI：`python3 scripts/validate.py [--root data]`，有错以退出码 1 结束。

- [ ] **Step 1: 写失败测试 `tests/test_validate.py`**

```python
import unittest
from scripts.validate import validate_record

GOOD = {
    "学名": "Ailanthus altissima (Mill.) Swingle",
    "中文名": "臭椿",
    "俗名": ["樗"],
    "异名": "无",
    "描述": "暂无数据",
    "分类系统": {
        "界": "Plantae-植物界(zhí wù jiè)",
        "门": "Tracheophyta-维管植物门(wéi guǎn zhí wù mén)",
        "纲": "Magnoliopsida-木兰纲(mù lán gāng)",
        "目": "Sapindales-无患子目(wú huàn zǐ mù)",
        "科": "Simaroubaceae-苦木科(kǔ mù kē)",
        "属": "Ailanthus-臭椿属(chòu chūn shǔ)",
    },
    "物种保护": "暂无数据",
    "分类信息": "暂无数据",
    "形态特征": {"生活型": "落叶乔木"},
    "生态习性": "暂无数据",
    "功用价值": "暂无数据",
    "植物志": "暂无数据",
    "元数据": {"来源文件": "KM-苦木科.xlsx", "来源工作表": "臭椿"},
}

class TestValidate(unittest.TestCase):
    def test_good_record_with_placeholders_passes(self):
        self.assertEqual(validate_record(GOOD, "data/苦木科/臭椿.yaml"), [])

    def test_missing_field_reported(self):
        bad = dict(GOOD); del bad["功用价值"]
        errs = validate_record(bad, "data/苦木科/臭椿.yaml")
        self.assertTrue(any("功用价值" in e for e in errs))

    def test_scientific_name_must_be_real(self):
        bad = dict(GOOD); bad["学名"] = "暂无数据"
        errs = validate_record(bad, "data/苦木科/臭椿.yaml")
        self.assertTrue(any("学名" in e for e in errs))

    def test_bad_taxonomy_format(self):
        bad = dict(GOOD)
        bad["分类系统"] = dict(GOOD["分类系统"], 属="臭椿属")   # 缺拉丁名与拼音
        errs = validate_record(bad, "data/苦木科/臭椿.yaml")
        self.assertTrue(any("属" in e for e in errs))

    def test_taxonomy_placeholder_ok(self):
        ok = dict(GOOD); ok["分类系统"] = "暂无数据"
        self.assertEqual(validate_record(ok, "data/苦木科/臭椿.yaml"), [])

    def test_common_name_list_or_placeholder(self):
        bad = dict(GOOD); bad["俗名"] = 123
        errs = validate_record(bad, "data/苦木科/臭椿.yaml")
        self.assertTrue(any("俗名" in e for e in errs))

    def test_filename_must_match_chinese_name(self):
        errs = validate_record(GOOD, "data/苦木科/错误名.yaml")
        self.assertTrue(any("文件名" in e for e in errs))

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m unittest tests.test_validate -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'scripts.validate'`

- [ ] **Step 3: 实现 `scripts/validate.py`**

```python
import argparse
import glob
import os
import re
import sys

import yaml

RANKS = ("界", "门", "纲", "目", "科", "属")
REQUIRED_FIELDS = ("学名", "中文名", "俗名", "异名", "描述", "分类系统", "物种保护",
                   "分类信息", "形态特征", "生态习性", "功用价值", "植物志", "元数据")
PLACEHOLDERS = ("无", "暂无数据")
_TAX_RE = re.compile(r"^[A-Z][A-Za-z ]+-.+\(.+\)$")
_NAME_RE = re.compile(r"^[A-Z][a-z]+ [a-z]")


def validate_record(rec, path):
    errs = []
    for field in REQUIRED_FIELDS:
        if field not in rec:
            errs.append(f"{path}: 缺字段 {field}")

    for field in ("学名", "中文名"):
        v = rec.get(field)
        if not v or v in PLACEHOLDERS:
            errs.append(f"{path}: {field} 必须为真实值")

    xm = rec.get("学名")
    if isinstance(xm, str) and xm not in PLACEHOLDERS and not _NAME_RE.match(xm):
        errs.append(f"{path}: 学名不像二名法: {xm!r}")

    tax = rec.get("分类系统")
    if isinstance(tax, dict):
        for rank in RANKS:
            val = tax.get(rank)
            if not val:
                errs.append(f"{path}: 分类系统缺 {rank}")
            elif not _TAX_RE.match(val):
                errs.append(f"{path}: 分类阶 {rank} 格式不符 拉丁名-中文(拼音): {val!r}")
    elif tax != "暂无数据":
        errs.append(f"{path}: 分类系统 应为映射或 '暂无数据'")

    for field in ("俗名", "异名"):
        v = rec.get(field)
        if not (isinstance(v, list) or v == "无"):
            errs.append(f"{path}: {field} 应为列表或 '无'")

    name = rec.get("中文名")
    stem = os.path.splitext(os.path.basename(path))[0]
    if name and stem != name:
        errs.append(f"{path}: 文件名 {stem!r} 与 中文名 {name!r} 不一致")
    return errs


def validate_tree(root="data"):
    errs = []
    for path in sorted(glob.glob(os.path.join(root, "**", "*.yaml"), recursive=True)):
        with open(path, encoding="utf-8") as fh:
            rec = yaml.safe_load(fh)
        errs.extend(validate_record(rec, path))
    return errs


def main():
    ap = argparse.ArgumentParser(description="校验 data/ 物种 YAML")
    ap.add_argument("--root", default="data")
    args = ap.parse_args()
    errs = validate_tree(args.root)
    if errs:
        for e in errs:
            print(e)
        print(f"\n共 {len(errs)} 处问题")
        sys.exit(1)
    print("校验通过")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m unittest tests.test_validate -v`
Expected: PASS（7 tests）

- [ ] **Step 5: 对已导入的苦木科跑校验**

Run: `python3 scripts/validate.py`
Expected: `校验通过`

- [ ] **Step 6: Commit**

```bash
git add scripts/validate.py tests/test_validate.py
git commit -m "feat: validate.py schema checker (required fields, taxonomy format)"
```

---

### Task 6: 导出器 export.py（JSON + Markdown）

**Files:**
- Create: `scripts/export.py`
- Test: `tests/test_export.py`

**Interfaces:**
- Consumes: `data/**/*.yaml`。
- Produces:
  - `load_all(root="data") -> list[dict]` —— 载入全部记录（按 中文名 排序）。
  - `export_json(records, out="dist/plants.json") -> str`。
  - `export_markdown(records, out_dir="dist/md") -> list[str]`。
  - `to_markdown(rec: dict) -> str` —— 单条记录转 frontmatter + 正文。
  - CLI：`python3 scripts/export.py [--only json,md,sqlite] [--root data] [--dist dist]`。

- [ ] **Step 1: 写失败测试 `tests/test_export.py`**

```python
import json, os, shutil, tempfile, unittest
from scripts.export import load_all, export_json, to_markdown

class TestExport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_load_all_reads_records(self):
        recs = load_all("data")
        self.assertTrue(any(r["中文名"] == "臭椿" for r in recs))

    def test_export_json_valid_and_unicode(self):
        recs = load_all("data")
        out = export_json(recs, os.path.join(self.tmp, "plants.json"))
        data = json.load(open(out, encoding="utf-8"))
        self.assertEqual(data[0]["中文名"], sorted(r["中文名"] for r in recs)[0])
        raw = open(out, encoding="utf-8").read()
        self.assertIn("臭椿", raw)          # ensure_ascii=False

    def test_markdown_has_frontmatter_body_and_skips_placeholders(self):
        rec = {"学名": "Ailanthus altissima (Mill.) Swingle", "中文名": "臭椿",
               "描述": "落叶乔木。", "分类系统": {"科": "Simaroubaceae-苦木科(kǔ mù kē)"},
               "形态特征": {"叶": "羽状复叶"}, "功用价值": "暂无数据",
               "植物志": "20. 臭椿……"}
        md = to_markdown(rec)
        self.assertTrue(md.startswith("---\n"))
        self.assertIn("学名:", md)
        self.assertIn("# 臭椿", md)
        self.assertIn("## 形态特征", md)
        self.assertIn("羽状复叶", md)
        self.assertIn("## 植物志", md)
        self.assertNotIn("## 功用价值", md)   # 占位区块不渲染

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m unittest tests.test_export -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'scripts.export'`

- [ ] **Step 3: 实现 `scripts/export.py`（本任务只做 json/md，sqlite 在 Task 7 追加）**

```python
import argparse
import glob
import json
import os

import yaml

from scripts.yaml_io import dump_species  # 复用统一序列化风格（frontmatter）


def load_all(root="data"):
    recs = []
    for path in sorted(glob.glob(os.path.join(root, "**", "*.yaml"), recursive=True)):
        with open(path, encoding="utf-8") as fh:
            recs.append(yaml.safe_load(fh))
    recs.sort(key=lambda r: r.get("中文名") or "")
    return recs


def export_json(records, out="dist/plants.json"):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(records, fh, ensure_ascii=False, indent=2)
    print(f"写出 {out}（{len(records)} 条）")
    return out


MAP_SECTIONS = ("物种保护", "分类信息", "形态特征", "生态习性", "功用价值")


def to_markdown(rec):
    fm = {k: rec[k] for k in ("学名", "中文名", "俗名", "异名", "分类系统") if k in rec}
    lines = ["---", dump_species(fm).rstrip(), "---", "", f"# {rec.get('中文名','')}", ""]
    desc = rec.get("描述")
    if desc and desc != "暂无数据":
        lines += [desc, ""]
    for sec in MAP_SECTIONS:
        v = rec.get(sec)
        if isinstance(v, dict):          # 占位字符串（暂无数据）跳过
            lines.append(f"## {sec}")
            for k, val in v.items():
                lines.append(f"- **{k}**：{val}")
            lines.append("")
    flora = rec.get("植物志")
    if flora and flora != "暂无数据":
        lines += ["## 植物志", "", flora, ""]
    return "\n".join(lines)


def export_markdown(records, out_dir="dist/md"):
    os.makedirs(out_dir, exist_ok=True)
    written = []
    for rec in records:
        out = os.path.join(out_dir, (rec.get("中文名") or "unnamed") + ".md")
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(to_markdown(rec))
        written.append(out)
    print(f"写出 {len(written)} 个 Markdown 到 {out_dir}")
    return written


def main():
    ap = argparse.ArgumentParser(description="从 data/ 导出 JSON/Markdown")
    ap.add_argument("--only", default="json,md")
    ap.add_argument("--root", default="data")
    ap.add_argument("--dist", default="dist")
    args = ap.parse_args()
    only = set(args.only.split(","))
    records = load_all(args.root)
    if "json" in only:
        export_json(records, os.path.join(args.dist, "plants.json"))
    if "md" in only:
        export_markdown(records, os.path.join(args.dist, "md"))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python3 -m unittest tests.test_export -v`
Expected: PASS（3 tests）

- [ ] **Step 5: 手工导出验证**

Run: `python3 scripts/export.py --only json,md && head -20 dist/plants.json && echo '---' && cat dist/md/臭椿.md`
Expected: `dist/plants.json` 为合法 JSON、含臭椿；`dist/md/臭椿.md` 有 frontmatter + `# 臭椿` + 形态/生态小节。

- [ ] **Step 6: Commit**

```bash
git add scripts/export.py tests/test_export.py
git commit -m "feat: export.py to JSON and Markdown"
```

---

### Task 7: 导出器追加 SQLite

**Files:**
- Modify: `scripts/export.py`（新增 `export_sqlite`，接入 `--only sqlite` 与 `main`）
- Test: `tests/test_export_sqlite.py`

**Interfaces:**
- Consumes: `load_all`（Task 6）。
- Produces: `export_sqlite(records, out="dist/plants.sqlite") -> str` —— 建表 `plant(学名, 中文名, 科, 属, 描述)` + 关联表 `synonym(学名, 异名)`、`common_name(学名, 俗名)`、`morphology(学名, 器官, 描述)`。

- [ ] **Step 1: 写失败测试 `tests/test_export_sqlite.py`**

```python
import os, shutil, sqlite3, tempfile, unittest
from scripts.export import load_all, export_sqlite

class TestSqlite(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_sqlite_tables_and_query(self):
        recs = load_all("data")
        db = export_sqlite(recs, os.path.join(self.tmp, "plants.sqlite"))
        con = sqlite3.connect(db)
        row = con.execute("SELECT 中文名, 科 FROM plant WHERE 学名 LIKE 'Ailanthus altissima%'").fetchone()
        self.assertEqual(row[0], "臭椿")
        self.assertIn("苦木科", row[1])
        n = con.execute("SELECT COUNT(*) FROM synonym WHERE 学名 LIKE 'Ailanthus altissima%'").fetchone()[0]
        self.assertGreaterEqual(n, 1)
        con.close()

if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python3 -m unittest tests.test_export_sqlite -v`
Expected: FAIL —— `ImportError: cannot import name 'export_sqlite'`

- [ ] **Step 3: 在 `scripts/export.py` 顶部加 `import sqlite3`，并新增辅助与函数**

占位值（`"无"`/`"暂无数据"`）不是列表/映射，入库前必须用辅助函数归一，否则
`.items()` / 迭代字符串会出错：

```python
def _as_list(v):
    return v if isinstance(v, list) else []


def _as_map(v):
    return v if isinstance(v, dict) else {}


def export_sqlite(records, out="dist/plants.sqlite"):
    os.makedirs(os.path.dirname(out), exist_ok=True)
    if os.path.exists(out):
        os.remove(out)
    con = sqlite3.connect(out)
    con.executescript(
        """
        CREATE TABLE plant (学名 TEXT PRIMARY KEY, 中文名 TEXT, 科 TEXT, 属 TEXT, 描述 TEXT);
        CREATE TABLE synonym (学名 TEXT, 异名 TEXT);
        CREATE TABLE common_name (学名 TEXT, 俗名 TEXT);
        CREATE TABLE morphology (学名 TEXT, 器官 TEXT, 描述 TEXT);
        """
    )
    for r in records:
        xm = r.get("学名")
        tax = _as_map(r.get("分类系统"))
        con.execute(
            "INSERT OR REPLACE INTO plant VALUES (?,?,?,?,?)",
            (xm, r.get("中文名"), tax.get("科"), tax.get("属"), r.get("描述")),
        )
        con.executemany("INSERT INTO synonym VALUES (?,?)", [(xm, s) for s in _as_list(r.get("异名"))])
        con.executemany("INSERT INTO common_name VALUES (?,?)", [(xm, c) for c in _as_list(r.get("俗名"))])
        con.executemany(
            "INSERT INTO morphology VALUES (?,?,?)",
            [(xm, k, v) for k, v in _as_map(r.get("形态特征")).items()],
        )
    con.commit()
    con.close()
    print(f"写出 {out}")
    return out
```

- [ ] **Step 4: 在 `main()` 接入 sqlite**

在 `main()` 的 `--only` 处理末尾追加：
```python
    if "sqlite" in only:
        export_sqlite(records, os.path.join(args.dist, "plants.sqlite"))
```
并把默认值改为 `ap.add_argument("--only", default="json,md,sqlite")`。

- [ ] **Step 5: 跑测试确认通过**

Run: `python3 -m unittest tests.test_export_sqlite -v`
Expected: PASS（1 test）

- [ ] **Step 6: Commit**

```bash
git add scripts/export.py tests/test_export_sqlite.py
git commit -m "feat: export.py SQLite output with relational tables"
```

---

### Task 8: 全量导入 19 科（42 物种）并收尾

**Files:**
- Create: `data/**/*.yaml`（全量，19 科共 42 物种）
- Modify: `CLAUDE.md`（补充新工作流）

**Interfaces:**
- Consumes: 全部脚本。
- Produces: 完整 `data/` 源、更新的 `CLAUDE.md`。

- [ ] **Step 1: 全量导入**

Run: `python3 scripts/import_xlsx.py knowledge/*.xlsx`
Expected: 逐个打印 `写出 data/<科>/<物种>.yaml`，结尾 `完成，共 42 个物种`；留意任何 `WARN` 行。

- [ ] **Step 2: 全量校验**

Run: `python3 scripts/validate.py`
Expected: `校验通过`；若有问题，逐条核对：属真实数据缺失则在对应 yaml 补齐，属解析器缺陷则回到 Task 3 修正并加测试。（注：源数据中 `分类系统` 有 1 个物种缺失，届时其值为 `暂无数据`，校验应放行。）

- [ ] **Step 3: 全量导出并抽查**

Run: `python3 scripts/export.py && ls dist/md | head && python3 -c "import json; d=json.load(open('dist/plants.json')); print('物种数', len(d))"`
Expected: 打印 `物种数 42`；随机抽查 2–3 个不同科的 `.md`（如 槐、百合、连翘）与原 xlsx 内容一致，占位区块不出现在正文。

- [ ] **Step 4: 更新 CLAUDE.md**

在 CLAUDE.md 追加「结构化数据工作流」小节，覆盖：`data/` 为真相源（每物种 13 个固定字段、缺失补占位）、`knowledge/` 为历史来源、三脚本用途与命令、`dist/` 可重建。保持中文。

- [ ] **Step 5: Commit**

```bash
git add data/ CLAUDE.md
git commit -m "data: import all 19 families to YAML; document workflow"
```

---

## Self-Review

**Spec coverage：**
- §2 目录结构 → Task 1。
- §3 YAML Schema（13 固定字段 + 缺失补占位 + 描述/植物志）→ Task 3（解析+占位注入）+ Task 4（写出）+ schema/plant.schema.md（Task 1）。
- §4① 导入器（7 区块、描述/植物志、科名从文件名、占位注入）→ Task 2 + Task 3 + Task 4。
- §4② 校验器（全字段在场、占位放行、学名/中文名须真实）→ Task 5。
- §4③ 导出器 JSON/MD/SQLite（占位不渲染/不入库）→ Task 6 + Task 7。
- §5 数据流 → Task 4/5/6/7 串联；Task 8 全量跑通。
- §6 错误处理（WARN 不丢弃/校验非 0 退出/导出对占位归一不崩）→ parser 备注兜底、validate `sys.exit(1)`、export `_as_list`/`_as_map`。
- §7 验证方式（KM 最简→槐 最全→百合 稀疏→全量 42）→ Task 3/4 测试 + Task 8。
- §8 非目标（无图片/网站/双向同步）→ 计划未涉及，符合。
- §9 .gitignore + CLAUDE.md 更新 → Task 1 + Task 8。

**Placeholder scan：** 无 TBD/TODO；每个代码步骤含完整可运行代码。

**Type consistency：**
- `read_sheets`→`list[(name, rows)]`；`parse_species(rows, src, sheet)`→`dict`（13 固定字段齐全）。
- `dump_species(rec)`→`str`；`family_dir(xlsx_path)`→`str`（**参数为文件路径**，Task 4 impl 与测试已同步）。
- `load_all`→`list[dict]`；`export_json/markdown/sqlite(records, out)` 签名在 Task 6/7 一致。
- 区块值为**映射或占位字符串**的异构类型：validate 用 `isinstance` 分支、export 用 `_as_map`/`_as_list` 归一、markdown 用 `isinstance(v, dict)` 跳占位——三处一致处理，无遗漏。
- 测试导入路径均为 `scripts.*`。已核对无名称漂移。
