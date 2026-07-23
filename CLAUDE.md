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
  xlsx 文件名去掉拼音前缀的部分）。全量共 **19 科 42 物种**。每条记录含 **13 个固定字段**：
  `学名` `中文名` `俗名` `异名` `描述` `分类系统` `物种保护` `分类信息` `形态特征`
  `生态习性` `功用价值` `植物志` `元数据`。字段缺失时**补占位**（映射型区块为 `暂无数据`、
  列表型字段为 `无`），保证结构齐整。无法归类的段落会兜底进 `备注` 字段（导入时打印 `WARN`，
  属正常，不代表出错）。
- **`knowledge/` 是历史来源**，仅在需要重新导入或核对原文时使用；日常修订应直接改 `data/` 下的
  YAML。
- **三个脚本**（均以 `python3 scripts/<名>.py` 运行，自带 `sys.path` 引导）：
  - `import_xlsx.py knowledge/*.xlsx` — 从 xlsx 解析并写出 `data/**/*.yaml`（会覆盖同名文件）。
  - `validate.py` — 校验 `data/` 下全部记录：13 字段齐全、占位放行、`学名`/`中文名` 须为真实值、
    分类阶格式为 `拉丁名-中文(拼音)`。有问题时逐条打印并以非 0 退出。
  - `export.py` — 把 `data/` 导出为 `dist/plants.json`、`dist/md/*.md`、`dist/plants.sqlite`；
    占位区块不渲染进 Markdown 正文、不入库。
- **`dist/` 可随时由 `data/` 重建**，不是真相源，已在 `.gitignore` 中忽略。
