# Repository Guidelines

## 项目结构与模块组织

PlantsDataCenter 是植物学参考数据仓库，不是传统应用项目。`data/` 是日常维护的唯一真相源，每个物种一个 YAML，路径为 `data/<中文科名>/<中文物种名>.yaml`。`knowledge/` 保存历史 WPS/Excel 原始工作簿，仅在需要按源表重导或核对原文时使用。`scripts/` 是 Python 数据管线：`import_xlsx.py`、`validate.py`、`export.py` 是 CLI 入口，`xlsx_reader.py`、`parser.py`、`yaml_io.py` 是复用模块。`schema/plant.schema.md` 定义字段规范，`tests/` 放单元测试，`dist/` 是可重建导出物并已忽略。

## 构建、测试与开发命令

所有命令从仓库根目录运行：

- `python3 scripts/import_xlsx.py knowledge/*.xlsx`：从 Excel 重建 `data/**/*.yaml`；会覆盖同名记录，但不会删除旧物种文件。
- `python3 scripts/validate.py`：校验 `data/` 下全部记录。
- `python3 scripts/export.py`：生成 `dist/plants.json`、`dist/md/*.md`、`dist/plants.sqlite`。
- `python3 scripts/export.py --only json,md`：只导出指定格式。
- `python3 -m unittest discover -s tests`：运行单元测试。

常规流程是修改 `data/*.yaml`，再校验和导出。只有当 Excel 是本次变更来源时才重跑导入。

## 数据与命名规范

YAML 使用 UTF-8，中文不转义，字段顺序保持稳定。每条记录保留 README 和 schema 中定义的 13 个固定字段。文件名必须与 `中文名` 一致，且不带拼音括注。`俗名`、`异名` 缺失时写 `"无"`；映射型区块缺失时写 `"暂无数据"`。分类阶值使用 `拉丁名-中文(拼音)`，源数据缺拼音时可省略拼音。

## 代码风格

Python 目标环境为 3.11+，当前运行时依赖 PyYAML；读取 xlsx 使用标准库，不要求安装 `openpyxl`。沿用现有小模块风格，使用 4 空格缩进，保持 CLI 可通过 `python3 scripts/<name>.py` 直接运行。按 `CLAUDE.md`，代码注释和 Git commit message 使用英文；协作文档和用户沟通默认中文。

## 测试规范

修改解析、导入、校验、导出或 YAML 序列化逻辑时，在 `tests/test_*.py` 中补充 `unittest`。测试应覆盖真实记录结构、占位归一、重复中文名、非法 YAML、导出内容等有业务价值的边界。交付前至少运行 `python3 scripts/validate.py` 和 `python3 -m unittest discover -s tests`。

## Commit 与 PR 规范

当前历史使用简短英文 conventional-style 主题，例如 `docs: ...`、`chore: ...`、`fix: ...`、`harden: ...`。提交应聚焦一个逻辑变更，不要提交可重建的 `dist/`，除非任务明确要求。PR 需说明数据或脚本改动、列出已运行的校验/测试命令、注明是否从 `knowledge/` 重导，并点名任何重命名或删除的物种，方便检查残留文件。

## Agent 专用说明

默认用中文协作。遇到不确定事实先查当前文件，仍不明确就询问，不要臆造。日常编辑以 `data/` 为准，`knowledge/` 只作历史输入，`dist/` 只作可重建输出。
