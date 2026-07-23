import argparse
import os
import sys

# 允许以 `python3 scripts/import_xlsx.py ...` 直接运行（把仓库根加入 sys.path）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    seen = set()
    for sheet_name, rows in read_sheets(xlsx_path):
        rec = parse_species(rows, src, sheet_name)
        fname = (rec.get("中文名") or sheet_name) + ".yaml"
        out_path = os.path.join(out_root, fam, fname)
        if out_path in seen:
            # 同科内中文名重复：不静默覆盖，改写为带序号的文件名并告警。
            stem, ext = os.path.splitext(fname)
            n = 2
            while os.path.join(out_root, fam, f"{stem}-{n}{ext}") in seen:
                n += 1
            out_path = os.path.join(out_root, fam, f"{stem}-{n}{ext}")
            print(f"WARN: {src}/{sheet_name} 中文名重复，改写为 {out_path}（勿覆盖）")
        seen.add(out_path)
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
