# Repository Guidelines

## 项目结构与模块组织

PlantsDataCenter 是植物知识结构化数据仓库。`data/` 是唯一真相源，当前包含 44 科、107 个 `*.yaml` 物种文件，路径为 `data/<中文科名>/<中文物种名>.yaml`。`knowledge/` 保存 44 个 WPS/Excel 原始工作簿，已由 Git LFS 管理，只在重导或核对原文时使用。`scripts/` 是 Python 数据管线，CLI 入口为 `import_xlsx.py`、`validate.py`、`export.py`、`retrieve_context.py`，复用模块为 `xlsx_reader.py`、`parser.py`、`yaml_io.py`。`schema/plant.schema.md` 定义字段规范，`tests/` 放 `unittest`，`docs/superpowers/` 放设计与计划文档。`dist/` 是可重建导出物，已忽略，不作为提交对象。

## Build, Test, and Development Commands

所有命令从仓库根目录运行：

- `git lfs install && git lfs pull --include="knowledge/*.xlsx"`：新 clone 后下载 Excel 实体文件。
- `python3 scripts/import_xlsx.py knowledge/*.xlsx`：从 xlsx 重建 `data/**/*.yaml`；覆盖同名记录，但不删除旧文件。
- `python3 scripts/validate.py`：校验全部 YAML 记录。
- `python3 scripts/export.py`：生成 `dist/plants.json`、`dist/md/*.md`、`dist/plants.sqlite`。
- `python3 scripts/export.py --only json,md`：只导出指定格式。
- `python3 scripts/retrieve_context.py "臭椿有什么用途" --prompt`：为 AI 问答生成 grounded context。
- `python3 -m unittest discover -s tests`：运行单元测试。

日常修改优先编辑 `data/*.yaml`，再运行校验和测试；只有 Excel 是变更来源时才重跑导入。

## Coding Style & Naming Conventions

Python 目标环境为 3.11+，运行时依赖 PyYAML 6.x；xlsx 读取使用标准库，不要求 `openpyxl`。Python 代码使用 4 空格缩进，保持 CLI 可通过 `python3 scripts/<name>.py` 直接运行。代码注释与 Git commit message 使用英文；协作文档和用户沟通默认中文。

YAML 使用 UTF-8，中文不转义，字段顺序保持稳定。每条记录保留 13 个固定字段：`学名`、`中文名`、`俗名`、`异名`、`描述`、`分类系统`、`物种保护`、`分类信息`、`形态特征`、`生态习性`、`功用价值`、`植物志`、`元数据`。文件名必须与 `中文名` 一致且不带拼音括注。`俗名`、`异名` 缺失时写 `"无"`；映射型区块缺失时写 `"暂无数据"`。

## Testing Guidelines

修改解析、导入、校验、导出、检索或 YAML 序列化逻辑时，在 `tests/test_*.py` 中补充 `unittest`。测试应覆盖真实记录结构、占位归一、重复中文名、非法 YAML、学名格式、导出 JSON/Markdown/SQLite、问答上下文召回等有业务价值的边界。交付前至少运行：

```bash
python3 scripts/validate.py
python3 -m unittest discover -s tests
```

## Commit & Pull Request Guidelines

Git 历史使用简短英文 conventional-style 主题，例如 `docs: ...`、`chore: ...`、`fix: ...`、`data: ...`、`harden: ...`。提交应聚焦一个逻辑变更；不要提交 `dist/`，除非任务明确要求。PR 需说明数据或脚本改动、列出已运行的校验/测试命令、注明是否从 `knowledge/` 重导，并点名任何重命名或删除的物种，方便检查残留 YAML。

## Agent-Specific Instructions

以当前代码、`README.md` 和 `CLAUDE.md` 为事实源；若文档口径冲突，先用当前文件与命令验证。不要臆造依赖、数据规模或 Git 状态。保留用户未要求处理的本地文件，例如未跟踪归档或临时材料。重命名或删除物种后，手动清理旧 `data/<科>/<旧名>.yaml`，再重新校验。
