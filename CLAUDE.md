# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 仓库性质

PlantsDataCenter 是一个**植物学参考数据集**，而非软件工程项目。仓库中没有源代码、构建系统、
测试或 git 历史，只有 `knowledge/` 目录下的电子表格数据。这里的工作是数据整理：读取、校验、
新增和修正植物记录。

## 目录结构

`knowledge/` 中每个 WPS/Excel 工作簿（`.xlsx`）对应一个**植物科**。文件名遵循
`<拼音首字母>-<中文科名>.xlsx` 格式，前缀是中文科名的拼音首字母——例如
`KM-苦木科.xlsx`（Simaroubaceae）、`ML-木兰科.xlsx`（Magnoliaceae）、
`J-菊科.xlsx`（Asteraceae）。

在一个工作簿内，**每个工作表对应一个物种**（工作表以中文物种名命名，如 `玉兰`、`二乔玉兰`）。
包含照片的工作簿还会带一个名为 `WpsReserved_CellImgList` 的保留工作表——这是 WPS Office
存放单元格内嵌图片的地方，不是物种记录，遍历物种时应跳过。文件体积较大（几十 MB）就是因为
这些内嵌的 JPEG 图片。

## 物种记录字段结构

每个物种工作表是**两列的键/值表单**（一列写字段名，旁边一列写值），而不是常规的行列表格。
从上到下的字段如下：

- `学名` — 拉丁学名（二名法），如 `Ailanthus altissima (Mill.) Swingle`
- `中文名` — 中文名称
- `俗名` — 俗名/别名（多个，逗号分隔）
- `异名` — 异名；每个拉丁名后面跟一个 ` (synonym)` 标记单元格
- 一段自由文本描述
- `分类系统` — 分类阶元：`界` `门` `纲` `目` `科` `属`。每个阶元的值格式为
  `<拉丁名>-<中文>(<拼音>)`，如 `Sapindales-无患子目(wú huàn zǐ mù)`
- `形态特征` — 形态描述，按器官分子键：`生活型` `株` `枝` `叶` `花` 等

新增或修改记录时，要与这套字段集合、字段用词保持一致，并沿用分类行
`拉丁名-中文(拼音)` 的格式。

## 数据操作说明

- 这些文件是 **WPS Office xlsx**（工作簿 XML 使用 `dbsheet` 命名空间，并包含
  `xl/woinfos.xml`）。可用 Excel/WPS/LibreOffice 打开，但注意内嵌图片工作表是 WPS 专有的，
  用其他工具可能无法完整往返转换。
- 当前环境**未安装 `openpyxl`**，且文本内容无法通过普通 `cat` 读取。若不用电子表格软件查看，
  可把 `.xlsx` 当作 zip 处理：
  - 列出工作表/物种：`unzip -p "<文件>.xlsx" xl/workbook.xml | grep -o 'sheet name="[^"]*"'`
  - 单元格文本存放在 `xl/sharedStrings.xml`（提取 `<t>…</t>` 的值）；单元格通过索引引用这些
    字符串，因此需要把 `xl/worksheets/sheetN.xml` 中 `<c t="s"><v>` 的索引与该列表对应起来，
    才能还原出每一行的内容。
- 内容为中文（UTF-8）。用程序编辑时，请保留拼音声调符号，以及异名标记前的 `\xa0`（不间断空格）。

## 结构化数据工作流

在原始 `knowledge/` 电子表格之外，仓库另有一套**结构化数据管线**（`scripts/`），把
xlsx 中的物种记录抽取为逐物种的 YAML，并可再导出为多种格式。

- **`data/` 是真相源**。每个物种一个文件，路径为 `data/<科>/<物种>.yaml`（科名取自
  xlsx 文件名去掉拼音前缀的部分）。全量共 **44 科 107 物种**。每条记录含 **13 个固定字段**：
  `学名` `中文名` `俗名` `异名` `描述` `分类系统` `物种保护` `分类信息` `形态特征`
  `生态习性` `功用价值` `植物志` `元数据`。字段缺失时**补占位**（映射型区块为 `暂无数据`、
  列表型字段为 `无`），保证结构齐整。无法归类的段落会兜底进 `备注` 字段（导入时打印 `WARN`，
  属正常，不代表出错）。
- **命名规则**：`中文名`（以及据其派生的 YAML/Markdown 文件名）**不含拼音括注**。源数据里个别
  物种把拼音写进了中文名（如 `蜀葵 (shǔ kuí)`），导入时会剥离尾部拼音括注得到 `蜀葵`——但仅当
  括注内**不含中文**时才剥，真正的中文别名注释（如 `槐（别名国槐）`）保留不动。
- **占位归一**：`俗名`/`异名` 缺失或源数据字面写 `无` 时，统一存为标量字符串 `"无"`（不是 `["无"]`）；
  校验对两种写法都放行。
- **`knowledge/` 是历史来源**，仅在需要重新导入或核对原文时使用；日常修订应直接改 `data/` 下的
  YAML。
- **脚本**（`scripts/`，均以 `python3 scripts/<名>.py` 运行，自带 `sys.path` 引导）。四个 CLI
  入口 + 三个被复用的模块（`xlsx_reader.py` 读 A/B/C 网格、`parser.py` 区块状态机、`yaml_io.py`
  统一序列化）：
  - `import_xlsx.py knowledge/*.xlsx` — 从 xlsx 解析并写出 `data/**/*.yaml`（幂等，重跑覆盖同名
    文件）。同一次导入内若同科中文名重复，**不静默覆盖**，改写为带序号文件名（`<名>-2.yaml`）并
    告警。
  - `validate.py` — 校验 `data/` 下全部记录：13 字段齐全、占位放行、`学名`/`中文名` 须为真实值、
    分类阶格式为 `拉丁名-中文(拼音)`（拼音可选，`学名` 允许杂交 `×`）。空/非映射 YAML 报错而非崩溃。
    有问题时逐条打印并以非 0 退出。
  - `export.py` — 把 `data/` 导出为 `dist/plants.json`、`dist/md/*.md`、`dist/plants.sqlite`；
    占位区块不渲染进 Markdown 正文、不入库；空 YAML 跳过并告警。
  - `retrieve_context.py "<问题>"` — 从 `data/` 检索与问题相关的物种记录，输出 AI 问答可用的
    Markdown 上下文；`--prompt` 输出完整 grounded prompt，`--json` 输出结构化命中，`--fields` 可限制
    输出字段。
- **典型工作流**：改 `data/*.yaml` → `validate.py`（把关）→ `export.py`（重建 `dist/`）。日常几乎只用这
  两个；AI 问答前用 `retrieve_context.py` 生成上下文；`import_xlsx.py` 仅在从 xlsx 重建真相源时用；
  三个模块是幕后被 CLI 调用的，不单独运行。
- **改动 xlsx 后重跑**：`python3 scripts/import_xlsx.py knowledge/<该文件>.xlsx`（或 `knowledge/*.xlsx`
  全量）→ `validate.py` → `rm -rf dist && export.py`。两个坑：① 导入以 xlsx 为准**覆盖** `data/`，会盖掉
  对应物种的手工改动，故只在 xlsx 是本次更新处时才重导；② 导入只覆盖/新增、**不删除**，xlsx 里删掉或
  改名的物种会在 `data/` 留下旧文件，需手动删或先 `rm -rf data/<科>` 再重导。
- **`dist/` 可随时由 `data/` 重建**，不是真相源，已在 `.gitignore` 中忽略。重命名/删除物种后
  最好 `rm -rf dist` 再重导出，避免残留旧文件名。

## 外部文档路径

本项目的 AI 生成文档统一管理在项目 `docs/` 目录下：

| 路径 | 用途 |
|------|------|
| `docs/superpowers/specs/` | superpowers 设计文档（brainstorm 产物） |
| `docs/superpowers/plans/` | superpowers 实现计划（writing-plans 产物） |

> **superpowers 产物存放规则**（覆盖 skill 默认的 `docs/superpowers/` 路径）：
> - 使用 brainstorm（`superpowers:brainstorming`）技能生成的**设计文档**保存到 `docs/superpowers/specs/`
> - 使用 `superpowers:writing-plans` 技能生成的**实现计划**保存到 `docs/superpowers/plans/`
> - 文件名格式 `YYYY-MM-DD-<topic>.md`，superpowers 生成的所有文档一律使用中文编写。

## AI 交互规则

- 若有不明白或不明确的地方，一定要先问我。不要自己幻想或无中生有。
- 用户偏好使用中文对话。
- 如需派发代理（subagent）让工作并行进行，代理一律使用与当前会话相同的模型，不要指定其它模型。

## 代码约定

- Git commit message 使用英文编写。
- 代码注释使用英文编写。

## 项目记忆

项目级记忆存储在 `.claude/memory/` 目录中，包含跨会话的协作约定和工作流偏好。

新会话开始时，请先读取 `.claude/memory/MEMORY.md` 了解已有的记忆内容。
