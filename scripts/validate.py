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
# 分类阶：拉丁名-中文，拼音可选（个别物种源数据缺拼音）
_TAX_RE = re.compile(r"^[A-Z][A-Za-z ]+-[^()]+(\(.+\))?$")
# 二名法：允许杂交属种名的 × 记号（如 Yulania × soulangeana）
_NAME_RE = re.compile(r"^[A-Z][a-z]+ (×\s+)?[a-z]")


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
