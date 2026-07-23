# PlantsDataCenter · 植物知识结构化数据仓库

一个植物学参考知识库。以**逐物种的 YAML** 为唯一真相源，可一键导出为 JSON / Markdown / SQLite，
供程序读取、二次开发与 AI/RAG 使用。

- **44 科 · 107 物种**
- **一个运行时依赖**：Python 3.11+ + PyYAML（无需 `openpyxl`）
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
├── scripts/            # Python 数据管线（4 个 CLI + 3 个复用模块）
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

## 环境与依赖

默认环境需要 Python 和 PyYAML。除 YAML 读写外，其余能力使用 Python 标准库
（`zipfile` / `xml.etree` / `json` / `sqlite3` / `unittest` 等）。

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | 3.11+ | 运行全部脚本 |
| PyYAML | 6.x | 读写 `data/**/*.yaml` |

**安装 PyYAML（任选一种）：**

```bash
# ① pip（最通用）
pip3 install pyyaml
#    若 pip3 找不到，用：python3 -m pip install pyyaml

# ② Debian/Ubuntu 系统包
sudo apt update && sudo apt install python3-yaml

# ③ 若 pip 报 "externally-managed-environment"（较新 Debian/Ubuntu）
sudo apt install python3-yaml            # 推荐用系统包
# 或（仅个人环境）：pip3 install --break-system-packages pyyaml

# ④ 虚拟环境（不想污染系统 Python 时）
python3 -m venv .venv && source .venv/bin/activate && pip install pyyaml
```

**验证：**

```bash
python3 -c "import yaml; print('PyYAML', yaml.__version__)"   # 打印版本号即 OK
```

## Git LFS 数据文件

`knowledge/*.xlsx` 由 Git LFS 管理。新 clone 的用户需要先安装并初始化 Git LFS，否则这些文件可能只是
指针文件，无法被 `scripts/import_xlsx.py` 正常读取。

```bash
# 首次使用 Git LFS
git lfs install

# clone 后下载 knowledge/ 下的 Excel 实体文件
git lfs pull --include="knowledge/*.xlsx"

# 若已经 clone 过，也可以重新拉取缺失的 LFS 对象
git lfs fetch --include="knowledge/*.xlsx"
git lfs checkout
```

检查文件是否已经下载为真实 xlsx：

```bash
file knowledge/KM-苦木科.xlsx
```

## 快速开始

所有脚本自带 `sys.path` 引导，可从仓库根直接运行（无需 `cd` 进 `scripts/` 或设置 `PYTHONPATH`）。

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

# 为 AI 问答检索上下文
python3 scripts/retrieve_context.py "臭椿有什么形态特征和用途" --prompt
```

> 重命名或删除物种后，建议先 `rm -rf dist` 再重新导出，避免残留旧文件名。

## 脚本

分两类：**4 个直接运行的 CLI 入口** + **3 个被复用、不单独运行的模块**。

### 直接运行的 CLI（`python3 scripts/<名>.py`）

| 脚本 | 何时使用 | 作用 |
|------|---------|------|
| `import_xlsx.py` | **一次性/偶尔**：需要从 `knowledge/*.xlsx` 重新生成或核对 `data/` 真相源时。日常不用（日常直接编辑 `data/*.yaml`）。 | 解析 xlsx 写出 `data/**/*.yaml`；同科中文名重复不静默覆盖，改带序号文件名并告警 |
| `validate.py`    | **每次改完 `data/` 之后**：把关字段与格式（适合接 CI / pre-commit）。 | 校验 13 字段齐全、占位放行、`学名`/`中文名` 为真实值、分类阶格式合规；空/非映射 YAML 报错而非崩溃 |
| `export.py`      | **对外发布 / 供程序或 AI 消费时**：把真相源导出为多种格式。 | 生成 `dist/plants.json`、`dist/md/*.md`、`dist/plants.sqlite`；占位区块不渲染进 Markdown、不入库 |
| `retrieve_context.py` | **AI 问答前**：从 `data/` 检索与问题相关的物种资料。 | 输出 Markdown 上下文；`--prompt` 输出可直接发给 AI 的完整提示词；`--json` 输出结构化命中；`--limit` 控制显示条数 |

**典型工作流**：改 `data/*.yaml` → `validate.py`（把关）→ `export.py`（重建 `dist/`）。AI 问答时用 `retrieve_context.py` 生成 grounded context；`import_xlsx.py` 只在从 xlsx 重来时才用。

## AI 问答上下文检索

`retrieve_context.py` 不调用外部 AI，也不需要额外依赖；它只负责从本地 `data/` 找出相关记录，并把资料整理成可复制给 AI 的上下文。

```bash
# 默认输出 Markdown 上下文
python3 scripts/retrieve_context.py "木兰科有哪些植物" --limit 5

# 分类列举查询不写 --limit 时默认返回全部命中
python3 scripts/retrieve_context.py "蔷薇科植物有哪些？"

# 显式限量时会同时显示总命中和显示记录数
python3 scripts/retrieve_context.py "蔷薇科植物有哪些？" --limit 5

# 输出完整提示词，适合直接复制到 ChatGPT / Claude / 其他大模型
python3 scripts/retrieve_context.py "臭椿有什么形态特征和用途" --prompt

# 程序集成时使用 JSON
python3 scripts/retrieve_context.py "玉兰的生态习性" --json

# 只输出指定字段
python3 scripts/retrieve_context.py "臭椿有什么用途" --fields 分类系统,功用价值,植物志
```

建议向 AI 提问时要求“只根据资料回答，资料中没有的信息请说明未提供”，避免模型补充未收录内容。

### 被复用的模块（不单独运行，被上面的 CLI `import` 调用）

| 模块 | 作用 | 谁在用 |
|------|------|--------|
| `xlsx_reader.py` | 读 WPS xlsx 的 A/B/C 列网格（跳过内嵌图片工作表与 `=DISPIMG(` 公式） | `import_xlsx.py` |
| `parser.py`      | 区块状态机：把行网格解析为 13 字段记录（gap 判定植物志、占位补全、无法归类段落兜底进 `备注`、中文名去拼音） | `import_xlsx.py` |
| `yaml_io.py`     | 统一 YAML 序列化（中文不转义、字段顺序稳定、长行不折断） | `import_xlsx.py`、`export.py` |

## 新增或修改 Excel 后如何重跑

Excel 原始数据在 `knowledge/`，文件名须遵循 `<拼音首字母>-<中文科名>.xlsx`（如 `KM-苦木科.xlsx`）——
科目录名就是文件名去掉拼音前缀的部分。改动 xlsx 后按下面重跑三步：**导入 → 校验 → 重建导出**。

**A. 新增一个科（放入一个新 xlsx）**

```bash
python3 scripts/import_xlsx.py knowledge/XX-新科.xlsx   # 只导这一个
python3 scripts/validate.py
rm -rf dist && python3 scripts/export.py
```

**B. 修改已有科的 xlsx（增 / 删 / 改物种）**

```bash
python3 scripts/import_xlsx.py knowledge/XX-某科.xlsx   # 重导该科
python3 scripts/validate.py
rm -rf dist && python3 scripts/export.py
```

**C. 一次性重导全部**

```bash
python3 scripts/import_xlsx.py knowledge/*.xlsx
python3 scripts/validate.py
rm -rf dist && python3 scripts/export.py
```

> ⚠️ **两个要点**
> 1. **导入会覆盖 `data/`**：`import_xlsx.py` 以 xlsx 为准重写对应物种的 YAML。若你之前**手工改过** `data/` 里这些物种，重导会覆盖掉那些改动。只有当 xlsx 才是你这次更新的地方时才重导；日常微调建议直接改 `data/*.yaml`，不必走 xlsx。
> 2. **导入只覆盖/新增、不删除**：若你在 xlsx 里**删除或重命名**了某物种，旧的 `data/<科>/<旧名>.yaml` 会残留。请手动删除它，或先 `rm -rf data/<科>` 再重导该科，保证 `data/` 与 xlsx 一致。

## 数据来源与说明

`knowledge/` 中的 xlsx 是 **WPS Office** 工作簿，内嵌 JPEG 照片（故文件较大）；日常修订应直接改
`data/` 下的 YAML，`knowledge/` 仅在需要重新导入或核对原文时使用。

面向 AI 协作者的详细工作流与约定见 [`CLAUDE.md`](CLAUDE.md)。
