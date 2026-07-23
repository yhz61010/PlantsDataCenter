import argparse
import glob
import json
import os
import sqlite3
import sys

# 允许以 `python3 scripts/export.py ...` 直接运行（把仓库根加入 sys.path）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml

from scripts.yaml_io import dump_species  # 复用统一序列化风格（frontmatter）


def _ensure_dir(path):
    # os.path.dirname("plants.json") == ""，makedirs("") 会抛异常；裸文件名跳过建目录。
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)


def load_all(root="data"):
    recs = []
    for path in sorted(glob.glob(os.path.join(root, "**", "*.yaml"), recursive=True)):
        with open(path, encoding="utf-8") as fh:
            rec = yaml.safe_load(fh)
        if not isinstance(rec, dict):
            print(f"WARN: 跳过空/非法 YAML: {path}")
            continue
        recs.append(rec)
    recs.sort(key=lambda r: r.get("中文名") or "")
    return recs


def export_json(records, out="dist/plants.json"):
    _ensure_dir(out)
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


def _as_list(v):
    return v if isinstance(v, list) else []


def _as_map(v):
    return v if isinstance(v, dict) else {}


def export_sqlite(records, out="dist/plants.sqlite"):
    _ensure_dir(out)
    if os.path.exists(out):
        os.remove(out)
    con = sqlite3.connect(out)
    try:
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
    finally:
        con.close()
    print(f"写出 {out}")
    return out


def main():
    ap = argparse.ArgumentParser(description="从 data/ 导出 JSON/Markdown")
    ap.add_argument("--only", default="json,md,sqlite")
    ap.add_argument("--root", default="data")
    ap.add_argument("--dist", default="dist")
    args = ap.parse_args()
    only = set(args.only.split(","))
    records = load_all(args.root)
    if "json" in only:
        export_json(records, os.path.join(args.dist, "plants.json"))
    if "md" in only:
        export_markdown(records, os.path.join(args.dist, "md"))
    if "sqlite" in only:
        export_sqlite(records, os.path.join(args.dist, "plants.sqlite"))


if __name__ == "__main__":
    main()
