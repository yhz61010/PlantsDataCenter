---
name: enable-ai
description: "初始化或复核当前项目的 Codex 协作配置，包括 AGENTS.md、repo-local skills、AI 文档与 superpowers 目录、可选项目记忆或外部记忆快照、项目级 Git 身份、GitHub 凭据使用规则和可选外部文档 Git。适用于用户提出 enable-ai、初始化 AI 配置、配置 Codex 项目、设置 Codex 文档或记忆、初始化或复核 AGENTS.md 等请求；本 skill 仅服务 Codex，不处理 Claude Code 或其它 AI 工具。"
---

# Enable AI

## 目标

在当前项目中建立可重复执行、可审计的 Codex 协作配置。把项目共享规则写入 `AGENTS.md`，按用户选择配置文档、记忆和 Git；只创建实际启用的目录和文件。

本 skill 仅用于 Codex。不要读取、创建、修改或同步 `CLAUDE.md`、`.claude/**` 及其它 AI 工具配置；这些文件即使存在，也不作为本流程的目标或完成条件。

## 不可违反的规则

- 默认使用中文沟通，生成的协作文档和记忆文件使用中文、UTF-8。
- 不明确时先读取当前状态；仍无法判断且不同选择会改变结果时，再询问用户。不要臆造路径、Git 状态、远端、Token 或工具能力。
- 保持幂等：先读后改，只补充缺失或过期内容，不重复段落，不覆盖无关内容。
- 保留用户现有工作树改动和未跟踪文件。不要因本 skill 在项目代码仓库执行 `git add`、`git commit` 或 `git push`。
- 不修改全局 Codex 配置或全局 Git 配置。项目 Git 身份只用无 `--global` 的 `git config`，且必须先获得用户确认。
- 不要求用户在对话中粘贴 Token、密码、密钥或其它秘密，不保存秘密值。只记录通过环境变量使用凭据的非敏感说明。
- 外部文档目录的 Git 操作只作用于已解析并确认的精确绝对路径；初始化和本地提交必须由用户选择启用，push 必须再次获得明确授权。
- 生成的普通文档使用 `YYYY-MM-DD-<kebab-case-topic>.md`；superpowers 设计文档放 `superpowers/specs/`，实现计划放 `superpowers/plans/`。
- 优先使用当前环境提供的结构化用户输入工具；不可用时使用简短文本问题。不要宣称 Codex 固定具备或不具备某种交互工具。

## 配置状态

在执行期间维护以下已确认值；没有选择的功能保持未启用，不要留下未替换占位符：

- `PROJECT_ROOT`：当前 Git 仓库根目录；非 Git 项目则为用户指定的项目根目录。
- `IS_GIT_REPO`：当前项目是否为 Git 仓库。
- `PROJECT_NAME`：优先取用户参数，其次取 Git 远端仓库名，最后取项目目录名。
- `DOC_MODE`：`local` 或 `external`。
- `DOC_ROOT`：项目内文档目录或外部文档根目录的规范化绝对路径。
- `AI_DOCS_ROOT`：本地模式等于 `DOC_ROOT`；外部模式默认为 `DOC_ROOT/Leo-Documents`。
- `MEMORY_MODE`：`agents-only`、`project` 或 `external`。
- `MEMORY_PATH`：仅 `project` 或 `external` 模式设置。
- `GIT_USER_NAME`、`GIT_USER_EMAIL`：用户确认的项目级 Git 身份。
- `COMMIT_MSG_LANG`、`CODE_COMMENT_LANG`：用户确认的语言约定。
- `PROJECT_TYPE`：`github` 或 `internal`。
- `EXT_GIT_MODE`：`disabled`、`local` 或 `remote`，仅外部文档模式适用。
- `SYNC_AGENTS_MIRROR`：是否把项目根 `AGENTS.md` 同步到外部文档根目录，仅外部文档模式适用。

## 执行流程

### 1. 盘点当前状态

从项目根目录进行只读检查：

- 解析 Git 根目录、当前分支、远端、项目级 `user.name` / `user.email` 和 `git status --short`。
- 读取现有 `AGENTS.md`、`skills/*/SKILL.md`、`skills/*/agents/openai.yaml` 和 `.codex/**`（存在时）。
- 从 `AGENTS.md` 识别已有的 Codex 文档路径、记忆路径、交互规则和代码约定；兼容旧标题 `## 外部文档路径`、`## AI 交互规则`。
- 探测候选路径是否真实存在。不要仅凭旧文档断定当前状态。
- 不读取 `CLAUDE.md` 或 `.claude/**`。

如果配置已完整：先展示当前配置。用户只要求复核时，报告差异并停止；用户要求初始化或更新时，询问是否沿用现有值或重新配置。

### 2. 收集必要选择

先用已验证状态填写默认值，只询问无法安全推断的项目。可以分批提问，但不要逐字段制造不必要的往返。

1. **文档位置**
   - 项目内目录，默认 `docs/`。
   - 外部路径，默认建议 `~/Documents/<PROJECT_NAME>`，展开 `~` 后必须得到绝对路径并去掉尾部 `/`。
   - 自定义项目内目录必须保持在 `PROJECT_ROOT` 下；外部路径必须在创建前展示解析后的绝对路径。
2. **Git 身份与语言**
   - 已有项目级 Git 身份时优先建议沿用；否则展示可用的现有 Git 身份并让用户确认或输入值。不要静默写入硬编码姓名或邮箱。
   - commit message 和代码注释默认英文，可由用户改为中文。
3. **记忆模式**
   - `agents-only`（推荐）：稳定协作规则只写 `AGENTS.md`，不创建项目记忆目录。
   - `project`：详细操作性记忆放 `PROJECT_ROOT/.codex/memory/`。
   - `external`：详细操作性记忆放 `DOC_ROOT/Codex/current-codex-memories/`；仅外部文档模式可选。
   - 不要暗示 repo-local 或外部文件会自动进入 Codex 内置记忆。只有用户明确要求更新 Codex 内置记忆时，才按当前环境的记忆规则另行处理。
4. **项目类型与 GitHub 说明**
   - 能从远端确认 GitHub 时直接建议 `github`；内部 Git、其它平台或无远端建议 `internal`，有歧义再确认。
   - GitHub 项目只询问是否写入 `GH_TOKEN` 环境变量使用说明；永远不索取 Token 值。
5. **外部文档 Git**
   - 仅 `DOC_MODE=external` 时询问：不启用、仅本地 Git、配置远端。
   - 选择配置远端时收集远端地址，但把 push 授权留到实际推送前再次确认。
   - 同时确认是否把项目根 `AGENTS.md` 同步为 `DOC_ROOT/AGENTS.md` 镜像；默认不同步，避免无意复制项目规则到外部位置。

### 3. 生成变更清单

写入前向用户概括：

- 将创建或更新的项目内文件。
- 将创建的目录及其精确绝对路径。
- 将写入项目 `.git/config` 的 Git 身份（如果变化）。
- 将在外部文档仓库执行的 Git 操作（如果启用）。
- 明确说明不会触碰 Claude 配置、项目代码仓库提交历史和任何秘密值。

已有 `AGENTS.md` 的同名段落需要实质改写时，说明替换范围并获得确认；新增缺失条目或修复明显过期路径时，按用户的初始化/更新授权执行最小修改。

### 4. 配置项目级 Git 身份

在任何外部文档 Git 提交之前完成本步骤：

- 再次确认 `GIT_USER_NAME` 和 `GIT_USER_EMAIL` 非空且是用户选择的值。
- `IS_GIT_REPO=true` 时，只在值需要变化时执行项目级 `git config user.name` 和 `git config user.email`。
- `IS_GIT_REPO=false` 时不执行项目级 `git config`；仅在用户启用外部文档 Git 时保留已确认的身份供该外部仓库使用，否则跳过 Git 身份配置。
- 不修改全局 Git 配置。

### 5. 创建所选目录

只创建选中模式需要的目录：

- 本地文档：`AI_DOCS_ROOT/`、`AI_DOCS_ROOT/superpowers/specs/`、`AI_DOCS_ROOT/superpowers/plans/`。
- 外部文档：`DOC_ROOT/`、`AI_DOCS_ROOT/` 及其 `superpowers/specs/`、`superpowers/plans/`。
- 项目记忆：`PROJECT_ROOT/.codex/memory/`。
- 外部记忆：`DOC_ROOT/Codex/current-codex-memories/`。

目录不存在时才创建。外部路径若超出当前写权限，按环境要求请求授权，不要改用其它路径规避授权。

### 6. 更新 AGENTS.md

写入前阅读 [references/agents-sections.md](references/agents-sections.md)，只选取当前模式适用的模板。

- 不存在 `AGENTS.md` 时创建；存在时保留仓库结构、构建、测试、安全和用户自定义规则。
- 优先更新现有等价段落，不在文件末尾重复创建同义标题。
- 写入实际的 `AI_DOCS_ROOT`、superpowers 路径、语言选择和记忆模式。
- `MEMORY_MODE=agents-only` 时明确 `AGENTS.md` 是项目共享规则入口，不引用不存在的 `MEMORY.md`。
- 只有用户选择 GitHub 使用说明时才写非敏感的 `GH_TOKEN` 环境变量规则。
- 外部模式下，仅在用户选择同步副本时把更新后的 `AGENTS.md` 复制到 `DOC_ROOT/AGENTS.md`；该副本是镜像，项目根 `AGENTS.md` 仍是项目规则真相源。

### 7. 写入可选操作性记忆

仅当 `MEMORY_MODE` 为 `project` 或 `external` 时，阅读 [references/memory-files.md](references/memory-files.md) 并创建或更新适用文件：

- `MEMORY.md`：只索引实际存在的操作性记忆文件。
- `feedback_memory_sync_policy.md`：说明敏感信息永不落盘，非敏感内容按当前路径维护。
- `feedback_agents_md_sync.md`：仅外部文档模式且用户选择同步 `AGENTS.md` 副本时创建。
- `feedback_external_docs_git.md`：仅启用外部文档 Git 时创建。
- `feedback_gh_token.md`：仅用户选择 GitHub 使用说明时创建，只记录环境变量用法，不含 Token 值。

相同内容保持不变；更新时保留用户添加的其它有效索引。不要创建模板未定义却被 `MEMORY.md` 引用的文件。

### 8. 配置可选外部文档 Git

仅 `DOC_MODE=external` 且 `EXT_GIT_MODE` 不为 `disabled` 时执行：

1. 验证操作目录与确认过的 `DOC_ROOT` 完全一致，且不是 `PROJECT_ROOT`、用户主目录或其它宽泛目录。
2. 不存在 `.git` 时运行 `git init`；已存在时先检查远端和工作树，不覆盖未知配置。
3. 给外部仓库设置已确认的本地 Git 身份，补充最小 `.gitignore`，忽略系统和编辑器临时文件。
4. 展示将提交的文件；只提交本次创建或更新的外部文档配置。不要把既有无关文件一并加入。
5. `EXT_GIT_MODE=local` 时停在本地提交。
6. `EXT_GIT_MODE=remote` 时校验远端地址；已有 `origin` 不同时先说明差异并确认。执行 push 前再次请求明确授权。

### 9. 验证与交付

- 运行 `quick_validate.py` 验证本仓库内新增或修改的 repo-local skills；至少验证 `skills/enable-ai/`。
- 检查 `AGENTS.md` 没有重复受管段落、未替换占位符或不存在的路径。
- 检查 `MEMORY.md` 的每个相对链接都指向实际文件。
- 检查生成内容不包含真实 Token、密码、密钥、数据库 URL、内部地址或疑似秘密串。
- 检查创建的目录与最终摘要一致，没有为未启用功能创建目录。
- 再次运行项目仓库 `git status --short`，区分本次修改与用户原有修改。
- 用中文报告文档根路径、记忆模式、修改文件、Git 身份变更、GitHub 说明状态、外部 Git 状态、验证结果和刻意跳过的内容。

## Skill 自身维护

- `skills/enable-ai/SKILL.md` 是唯一规范入口；不要维护第二份完整流程。
- 修改本 skill 后同步检查 `agents/openai.yaml`，并运行 `quick_validate.py skills/enable-ai`。
- 保持 `SKILL.md` 只包含核心流程；模板细节放在一层深度的 `references/` 中。
