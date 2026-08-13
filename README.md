# PlantsDataCenter · 植物知识结构化数据仓库

一个植物学参考知识库。以**逐物种的 YAML** 为唯一真相源，可一键导出为 JSON / Markdown / SQLite，
供程序读取、二次开发与 AI/RAG 使用。

本知识库主体记录的是在**大连**实际遇到、观察或整理过的植物，不代表完整的区域植物志名录。
少量为物种对比与学习而收录、但尚未在大连发现过的植物，会用可选字段 `是否发现: 否` 标记。

- **55 科 · 159 物种，其中大连已发现 150 物种**
- **数据统计**：当前科数、总物种数与每科物种数见 [`DATA_STATS.md`](DATA_STATS.md)
- **一个运行时依赖**：Python 3.11+ + PyYAML（无需 `openpyxl`）
- **单向管线**：本地 `knowledge/*.xlsx`（物种原始表）→ `data/**/*.yaml`（真相源）→ `dist/*`（派生物）
- **可重建数据层**：日常以 `data/` 为准；维护者可用本地工作簿重新导入，重建对应 YAML。

## 目录结构

```
PlantsDataCenter/
├── data/               # 日常真相源：每物种一个 YAML；data/<拼音首字母>-<中文科名>/<中文物种名>.yaml
├── knowledge/          # 本地原始 WPS xlsx（被忽略，不随仓库分发）
├── 00-基础知识.xlsx     # 本地基础知识参考表（被忽略，不随仓库分发）
├── dist/               # 派生导出物（被 .gitignore 忽略，可由 export.py 重建）
│   ├── YYYYMMDD-plants.json
│   ├── YYYYMMDD-plants.md
│   ├── YYYYMMDD-plants.sqlite
│   └── md/<物种>.md
├── scripts/            # Python 数据管线（4 个 CLI + 3 个复用模块）
├── schema/             # 字段规范（人读的权威定义）
├── tests/              # 单元测试（python3 -m unittest）
├── skills/             # repo-local skills（enable-ai、plants-expert）
├── docs/               # 普通协作文档及 superpowers 设计/实现计划
├── DATA_STATS.md       # data/ 当前科数、总物种数与每科物种数统计
├── .claude/            # Claude Code 命令与共享记忆文件
├── AGENTS.md           # 面向 Codex/自动化协作者的仓库指南
├── CLAUDE.md           # 面向 Claude Code 的项目说明
└── .gitignore          # 忽略 Excel、dist/、缓存等本地文件
```

## 数据模型

每个物种有 **13 个必填字段**（顺序固定，缺失补占位）：

`学名` `中文名` `俗名` `异名` `描述` `分类系统` `物种保护` `分类信息` `形态特征`
`生态习性` `功用价值` `植物志` `元数据`

- **可选字段**：`是否发现`。仅用于标记为对比学习而收录、但尚未在大连发现过的物种；有值时写在 `中文名` 后，值为 `否`，没有该字段的物种不补占位。
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

## 本地 Excel 源文件（不纳入 Git）

本地 `knowledge/` 可保存 WPS/Excel 物种原始工作簿，根目录的 `00-基础知识.xlsx` 是本地基础知识参考表；
两者均被 `.gitignore` 忽略，不随仓库分发，只在重导、补充来源或核对原文时使用。这两类 Excel 已从
Git 历史中移除。新的 clone 只包含可直接使用的 YAML 真相源、脚本、测试和文档，不包含任何 Excel 文件。
本仓库不再配置或使用 Git LFS，新 clone 无需安装 Git LFS，也无法从 GitHub 下载这些工作簿。

维护者需要重导或核对原文时，应从独立备份把工作簿放回本地对应路径。不要使用 `git add -f`
绕过忽略规则，也不要把这些文件重新提交到本仓库。未准备本地工作簿时，导入命令不可用，
依赖真实工作簿的单元测试会自动跳过；YAML 校验、导出和检索不受影响。

## 快速开始

所有脚本自带 `sys.path` 引导，可从仓库根直接运行（无需 `cd` 进 `scripts/` 或设置 `PYTHONPATH`）。

```bash
# 从 xlsx 导入 / 重建真相源（幂等，重跑覆盖同名文件）
python3 scripts/import_xlsx.py knowledge/*.xlsx

# 校验 data/ 全部记录（有问题逐条打印并以非 0 退出）
python3 scripts/validate.py

# 导出 JSON / 全量 Markdown / 逐物种 Markdown / SQLite 到 dist/
# 汇总文件会加运行当天日期前缀，如 20260803-plants.json
python3 scripts/export.py                 # 全部
python3 scripts/export.py --only json,md  # 仅 JSON + 逐物种 Markdown
python3 scripts/export.py --only fullmd   # 仅全量单文件 Markdown

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
| `validate.py`    | **每次改完 `data/` 之后**：把关字段与格式（适合接 CI / pre-commit）。 | 校验 13 个必填字段齐全、可选 `是否发现` 取值、占位放行、`学名`/`中文名` 为真实值、分类阶格式合规；空/非映射 YAML 报错而非崩溃 |
| `export.py`      | **对外发布 / 供程序或 AI 消费时**：把真相源导出为多种格式。 | 生成 `dist/YYYYMMDD-plants.json`、`dist/YYYYMMDD-plants.md`、`dist/md/*.md`、`dist/YYYYMMDD-plants.sqlite`；`YYYYMMDD-plants.md` 是单文件全量数据，保留所有字段；`dist/md/*.md` 是逐物种阅读版，会跳过占位区块 |
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

# 查询为对比学习收录、但尚未在大连发现过的物种
python3 scripts/retrieve_context.py "哪些植物未在大连发现？"
```

输出中的“匹配分数”只用于本地排序，不是准确率或置信度。分数来自关键词在不同字段中的命中情况：
`中文名`、`俗名`、`学名`、`分类系统` 等字段权重较高；明确点名某个植物时会额外加权。判断结果是否可用时，
优先看“匹配字段”和具体上下文内容，不要只看分数大小。不同问题之间的分数也不适合直接比较。

建议向 AI 提问时要求“只根据资料回答，资料中没有的信息请说明未提供”，避免模型补充未收录内容。

### 被复用的模块（不单独运行，被上面的 CLI `import` 调用）

| 模块 | 作用 | 谁在用 |
|------|------|--------|
| `xlsx_reader.py` | 读 WPS xlsx 的 A/B/C 列网格（跳过内嵌图片工作表与 `=DISPIMG(` 公式） | `import_xlsx.py` |
| `parser.py`      | 区块状态机：把行网格解析为 13 个必填字段和可选 `是否发现`（gap 判定植物志、占位补全、无法归类段落兜底进 `备注`、中文名去拼音） | `import_xlsx.py` |
| `yaml_io.py`     | 统一 YAML 序列化（中文不转义、字段顺序稳定、长行不折断） | `import_xlsx.py`、`export.py` |

## 本地新增或修改 Excel 后如何重跑

Excel 原始数据由维护者独立备份，并按需放入本地 `knowledge/`。文件名须遵循
`<拼音首字母>-<中文科名>.xlsx`（如 `KM-苦木科.xlsx`）——
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
> 2. **导入只覆盖/新增、不删除**：若你在 xlsx 里**删除或重命名**了某物种，旧的 `data/<拼音首字母>-<科>/<旧名>.yaml` 会残留。请手动删除它，或先 `rm -rf data/<拼音首字母>-<科>` 再重导该科，保证 `data/` 与 xlsx 一致。

## 数据来源与说明

物种相关知识主要参考 [植物科学数据中心](https://www.plantplus.cn/cn)，并结合在大连的实际观察与整理记录进行结构化。

本地 `knowledge/` 中的 xlsx 是 **WPS Office** 工作簿，内嵌 JPEG 照片（故文件较大），
不随 Git 仓库分发。日常修订应直接改 `data/` 下的 YAML，Excel 文件仅在需要重新导入、
补充来源或核对原文时使用。

Codex 与自动化协作者的详细工作流与约定见 [`AGENTS.md`](AGENTS.md)；Claude Code 的项目说明见
[`CLAUDE.md`](CLAUDE.md)。
