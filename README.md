# PlantsDataCenter · 植物知识结构化数据仓库

一个植物学参考知识库。以**逐物种的 YAML** 为唯一真相源，可一键导出为 JSON / Markdown / SQLite，
供程序读取、二次开发与 AI/RAG 使用。

- **19 科 · 42 物种**
- **零第三方依赖**：Python 3.11 标准库 + 系统预装 PyYAML（无需 `pip`/`openpyxl`）
- **单向管线**：`knowledge/*.xlsx`（历史原始数据）→ `data/**/*.yaml`（真相源）→ `dist/*`（派生物）

## 目录结构

```
PlantsDataCenter/
├── knowledge/          # 原始 WPS xlsx（每科一个工作簿，内嵌照片），导入后退役、仅作历史来源
├── data/               # ★ 唯一真相源：每物种一个 YAML，data/<中文科名>/<中文物种名>.yaml
├── dist/               # 派生导出物（.gitignore，可随时由 export.py 重建）
│   ├── plants.json
│   ├── plants.sqlite
│   └── md/<物种>.md
├── scripts/            # 零依赖 Python 管线（3 个 CLI + 3 个复用模块）
├── schema/             # 字段规范（人读的权威定义）
├── tests/              # 单元测试（python3 -m unittest）
├── docs/               # 设计文档与实现计划（superpowers 产物）
└── CLAUDE.md           # 面向 AI 协作者的项目说明
```

## 数据模型

每个物种是 **13 个固定字段**（顺序固定，缺失补占位）：

`学名` `中文名` `俗名` `异名` `描述` `分类系统` `物种保护` `分类信息` `形态特征`
`生态习性` `功用价值` `植物志` `元数据`

- **占位规则**：`俗名`/`异名` 缺失或字面为 `无` → 标量字符串 `"无"`；其余映射型区块缺失 → `"暂无数据"`。
- **命名规则**：`中文名`（及据其派生的文件名）不含拼音括注；含中文的别名注释（如 `槐（别名国槐）`）保留。
- **分类阶格式**：`拉丁名-中文(拼音)`，如 `Sapindales-无患子目(wú huàn zǐ mù)`（拼音可选）。

完整字段定义见 [`schema/plant.schema.md`](schema/plant.schema.md)。

## 快速开始

环境：Python 3.11+ 与系统 PyYAML（`python3 -c "import yaml"` 能通过即可）。所有脚本自带 `sys.path` 引导，
从仓库根直接运行。

```bash
# 从 xlsx 导入 / 重建真相源（幂等，重跑覆盖同名文件）
python3 scripts/import_xlsx.py knowledge/*.xlsx

# 校验 data/ 全部记录（有问题逐条打印并以非 0 退出）
python3 scripts/validate.py

# 导出 JSON / Markdown / SQLite 到 dist/
python3 scripts/export.py                 # 全部
python3 scripts/export.py --only json,md  # 仅部分

# 运行测试
python3 -m unittest discover -s tests
```

> 重命名或删除物种后，建议先 `rm -rf dist` 再重新导出，避免残留旧文件名。

## 脚本

| 脚本 | 作用 |
|------|------|
| `scripts/import_xlsx.py` | 从 WPS xlsx 解析物种记录并写出 `data/**/*.yaml`；同科中文名重复不静默覆盖，改带序号文件名并告警 |
| `scripts/validate.py`    | 校验 13 字段齐全、占位放行、`学名`/`中文名` 为真实值、分类阶格式合规；空/非映射 YAML 报错而非崩溃 |
| `scripts/export.py`      | 导出 `dist/plants.json`、`dist/md/*.md`、`dist/plants.sqlite`；占位区块不渲染进 Markdown、不入库 |
| `scripts/xlsx_reader.py` | 读 WPS xlsx 的 A/B/C 列网格（跳过内嵌图片工作表与 `=DISPIMG(` 公式） |
| `scripts/parser.py`      | 区块状态机：把行网格解析为 13 字段记录（gap 判定植物志、占位补全、无法归类段落兜底进 `备注`） |
| `scripts/yaml_io.py`     | 统一 YAML 序列化（中文不转义、字段顺序稳定、长行不折断） |

## 数据来源与说明

`knowledge/` 中的 xlsx 是 **WPS Office** 工作簿，内嵌 JPEG 照片（故文件较大）；日常修订应直接改
`data/` 下的 YAML，`knowledge/` 仅在需要重新导入或核对原文时使用。

面向 AI 协作者的详细工作流与约定见 [`CLAUDE.md`](CLAUDE.md)。
