# Repository Guidelines

## 项目结构与模块组织

PlantsDataCenter 是植物知识结构化数据仓库。`data/` 是唯一真相源，当前包含 58 科、165 个 `*.yaml` 物种文件，路径为 `data/<拼音首字母>-<中文科名>/<中文物种名>.yaml`；根目录 `DATA_STATS.md` 记录当前科、属和物种数量，以及松科/柏科与木本/草本生活型统计，各项物种数同时体现大连发现/未发现拆分。本地 `knowledge/` 可保存 58 个 WPS/Excel 物种原始工作簿，`00-基础知识.xlsx` 是本地基础知识参考表；两者均被 `.gitignore` 忽略，不随仓库分发，只在重导、补充来源或核对原文时使用。仓库不再配置或使用 Git LFS。`scripts/` 是 Python 数据管线，CLI 入口为 `import_xlsx.py`、`validate.py`、`export.py`、`retrieve_context.py`，复用模块为 `xlsx_reader.py`、`parser.py`、`yaml_io.py`。`schema/plant.schema.md` 定义字段规范，`tests/` 放 `unittest`，`docs/superpowers/specs/` 与 `docs/superpowers/plans/` 放设计和实现计划。`dist/` 是可重建导出物，已忽略，不作为提交对象。

## Build, Test, and Development Commands

所有命令从仓库根目录运行：

- 从独立备份把 Excel 放入本地 `knowledge/` 和根目录 `00-基础知识.xlsx`：仅在需要重导或核对原文时准备；不要提交这些被忽略的文件。
- `python3 scripts/import_xlsx.py knowledge/*.xlsx`：从 xlsx 重建 `data/**/*.yaml`；覆盖同名记录，但不删除旧文件。
- `python3 scripts/validate.py`：校验全部 YAML 记录。
- `python3 scripts/export.py`：生成 `dist/YYYYMMDD-plants.json`、`dist/YYYYMMDD-plants.md`、`dist/md/*.md`、`dist/YYYYMMDD-plants.sqlite`；`YYYYMMDD` 为运行当天日期，`YYYYMMDD-plants.md` 是保留所有字段的全量单文件 Markdown，`dist/md/*.md` 是逐物种阅读版。
- `python3 scripts/export.py --only json,md`：只导出 JSON 和逐物种 Markdown；`--only fullmd` 只导出全量单文件 Markdown。
- `python3 scripts/retrieve_context.py "臭椿有什么用途" --prompt`：为 AI 问答生成 grounded context；`--json` 供自动化集成，`--fields 分类系统,功用价值` 可限制上下文字段。
- `python3 -m unittest discover -s tests`：运行单元测试。

日常修改优先编辑 `data/*.yaml`，再运行校验和测试；只有本地 Excel 是变更来源时才重跑导入。未准备本地工作簿时，依赖真实 Excel 的测试会自动跳过。

## Coding Style & Naming Conventions

Python 目标环境为 3.11+，运行时依赖 PyYAML 6.x；xlsx 读取使用仓库内 `scripts/xlsx_reader.py` 和标准库，不要求 `openpyxl`。Python 代码使用 4 空格缩进，保持 CLI 可通过 `python3 scripts/<name>.py` 直接运行。代码注释与 Git commit message 使用英文；协作文档和用户沟通默认中文。

YAML 使用 UTF-8，中文不转义，字段顺序保持稳定。每条记录保留 13 个必填字段：`学名`、`中文名`、`俗名`、`异名`、`描述`、`分类系统`、`物种保护`、`分类信息`、`形态特征`、`生态习性`、`功用价值`、`植物志`、`元数据`。可选字段 `是否发现` 只用于标记为对比学习而收录、但尚未在大连发现过的物种；有值时放在 `中文名` 后，当前取值为 `否`，不要给未标记物种补 `暂无数据`。文件名必须与 `中文名` 一致且不带拼音括注。`俗名`、`异名` 缺失时写 `"无"`；映射型区块缺失时写 `"暂无数据"`。

## Testing Guidelines

修改解析、导入、校验、导出、检索或 YAML 序列化逻辑时，在 `tests/test_*.py` 中补充 `unittest`；当前测试套件为 65 项。测试应覆盖真实记录结构、占位归一、可选 `是否发现`、重复中文名、非法 YAML、学名格式、导出 JSON/Markdown/SQLite、问答上下文召回等有业务价值的边界。检索测试要同时保护分类列举查询默认全量返回、`--limit` 的总数/显示数语义，以及单字中文名（如 `槐`、`桃`、`莲`、`桑`、`艾`）在自然问句中的边界匹配，避免 `桑拿`、`艾滋病`、`构造` 这类无关子串误锁。交付前至少运行：

```bash
python3 scripts/validate.py
python3 -m unittest discover -s tests
```

## Commit & Pull Request Guidelines

Git 历史使用简短英文 conventional-style 主题，例如 `docs: ...`、`chore: ...`、`fix: ...`、`data: ...`、`harden: ...`。提交应聚焦一个逻辑变更；不要提交 `knowledge/`、`00-基础知识.xlsx` 或 `dist/`，除非任务明确改变仓库策略。PR 需说明数据或脚本改动、列出已运行的校验/测试命令、注明是否从本地 `knowledge/` 重导，并点名任何重命名或删除的物种，方便检查残留 YAML。

## Codex 文档路径

本项目由 Codex 生成的协作文档统一存放在 `docs/`。

| 路径 | 用途 |
|------|------|
| `docs/` | 普通分析、审查与说明文档 |
| `docs/superpowers/specs/` | 设计文档 |
| `docs/superpowers/plans/` | 实现计划 |

生成文档使用中文和 UTF-8；普通文档文件名使用 `YYYY-MM-DD-<kebab-case-topic>.md`。

## 项目记忆

项目共享协作规则以根目录 `AGENTS.md` 为准。本项目未配置 repo-local 或外部记忆快照；不要引用不存在的 `MEMORY.md`。`enable-ai` 仅服务 Codex；Codex 不读取、创建、修改或同步 `CLAUDE.md`、`.claude/**` 及其它 AI 工具配置。

## Agent-Specific Instructions

以当前代码、`README.md`、`DATA_STATS.md` 和 `schema/plant.schema.md` 为事实源；若文档口径冲突，先用当前文件与命令验证。不要臆造依赖、数据规模或 Git 状态。更新 README、AGENTS 或任何数据规模相关文档时，同步核对并更新根目录 `DATA_STATS.md`。保留用户未要求处理的本地文件，例如未跟踪归档或临时材料。重命名或删除物种后，手动清理旧 `data/<拼音首字母>-<科>/<旧名>.yaml`，再重新校验。
