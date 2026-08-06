---
description: 在当前项目中初始化 AI 工具配置（外部文档路径、记忆同步、Git 信息等）
argument-hint: [项目名称(可选)]
---

# /enable-ai

在当前项目中执行 AI 工具初始化配置：设置外部文档路径、记忆同步策略、Git 用户信息、交互规则等。

用户传入的参数（如果有）：`$ARGUMENTS`

## 核心原则

- 若有不明白或不明确的地方，一定要先问我。不要自己幻想或无中生有。
- 用户偏好使用中文对话。
- CLAUDE.md 使用中文编写。
- 所有生成的记忆文件（包括 MEMORY.md 索引及各 feedback_*.md / user_*.md 等）使用中文编写。
- superpowers 生成的文档（`plans/`、`specs/` 及其它 superpowers 产物）一律使用中文编写。
- superpowers 产物分目录存放：brainstorm 技能生成的**设计文档**放到 `superpowers/specs/`，writing-plans 技能生成的**实现计划**放到 `superpowers/plans/`（具体根路径见 Step 10 写入 CLAUDE.md 的规则）。
- 所有生成的文档（包括记忆文件、CLAUDE.md、MEMORY.md 等）编码格式均使用 UTF-8。
- 生成的文档文件名格式：`YYYY-MM-DD-<kebab-case-topic>.md`（日期取今天系统日期；topic 用英文短横线命名，准确描述话题）。
- **交互方式**：所有需要用户做出选择的地方，必须使用 `AskUserQuestion` 工具呈现选项。该工具支持方向键选择、默认选项高亮（推荐项放在第一个并标注 "(推荐)"），并自动提供 "Other" 选项让用户手动输入自定义内容。禁止使用纯文本方式让用户输入数字或 y/N 来选择。**注意**：该工具要求每个问题至少提供 2 个选项（最多 4 个），不足 2 个时需补充一个合理的备选项。
- 每一步先检查已有状态，确保幂等（多次执行不破坏已有配置）。
- 每一步完成后简要汇报结果，再进入下一步。

## 执行步骤

按以下顺序严格执行，**不要跳步**：

### Step 1/13: 幂等性检测

检查当前项目是否已执行过本命令：

1. 读取项目根目录的 `CLAUDE.md`，检查是否包含 `## 外部文档路径` 段落。
2. 检查 `.claude/memory/feedback_memory_sync_policy.md` 是否存在。

**如果以上任一条件成立**：
- 展示当前已有的配置信息（外部路径、记忆位置等）。
- 询问用户："检测到本项目已配置过 AI 工具。是否重新配置？(y/N)"
- 用户回答 N 或不回答 → 停止执行，输出当前配置摘要。
- 用户回答 Y → 继续执行后续步骤（已有文件仅更新，不删除）。

**如果都不成立**：继续执行。

---

### Step 2/13: 询问文档保存路径

向用户询问本项目 AI 工具生成的文档保存在哪里。使用 `AskUserQuestion` 工具呈现选项。

**外部路径推导逻辑**（用于选项 2 的建议路径）：
- 如果 `$ARGUMENTS` 非空，建议路径：`~/yhz61010/Documents/$ARGUMENTS/`
- 如果 `$ARGUMENTS` 为空，尝试从 `git remote get-url origin` 提取仓库名作为项目名建议

**第一步：询问保存位置类型**（使用 `AskUserQuestion`）：
- 选项 1（推荐）：保存到项目内目录
- 选项 2：保存到外部路径（描述中展示推导出的建议路径，如 `~/yhz61010/Documents/<项目名>/`）

**如果用户选择选项 1（项目内）**：
- `$DOC_IS_LOCAL` = `true`
- 继续询问项目内的目录名（使用 `AskUserQuestion`，至少 2 个选项）：
  - 选项 1（推荐）：`docs/`
  - 选项 2：`documents/`
  - 用户也可通过 "Other" 输入其他自定义目录名
- `$EXT_DOC_PATH` = 项目根目录下用户选择的目录（如 `docs/` 或 `documents/`）
- 生成的文档直接放在 `$EXT_DOC_PATH/` 下（如 `docs/2026-06-12-xxx.md`）
- superpowers 产物直接放在 `$EXT_DOC_PATH/superpowers/`（如 `docs/superpowers/specs/`）
- **不创建** Claude/、Codex/、Leo-Documents/ 等子目录（这些仅在外部路径模式下创建）

**如果用户选择选项 2（外部路径）**：
- `$DOC_IS_LOCAL` = `false`
- `$EXT_DOC_PATH` = 推导出的建议路径（用户可通过 "Other" 自定义）
- **验证**：
  - 必须是绝对路径（以 `/` 开头）
  - `~` 需展开为实际 HOME 路径
  - 去除尾部 `/`
  - 如果路径不存在，询问是否创建

将结果记为 `$EXT_DOC_PATH` 和 `$DOC_IS_LOCAL`，后续步骤使用。

---

### Step 3/13: 创建目录结构

根据 Step 2 的选择，创建不同的目录结构。

**如果 `$DOC_IS_LOCAL` = `true`（项目内 docs/ 模式）**：

仅创建 superpowers 子目录，生成的文档直接放在 `$EXT_DOC_PATH/` 下：

```
$EXT_DOC_PATH/                      # 即 docs/
├── superpowers/                    # superpowers 插件产物
│   ├── plans/                      # 实现计划
│   └── specs/                      # 设计规范
└── (生成的文档直接放在这里)        # 如 2026-06-12-xxx.md
```

**如果 `$DOC_IS_LOCAL` = `false`（外部路径模式）**：

创建标准目录结构：

```
$EXT_DOC_PATH/
├── Claude/                         # Claude Code 记忆同步目录
├── Codex/                          # Codex 记忆同步目录（可选，需先询问）
│   └── current-codex-memories/     # Codex 当前记忆
├── Leo-Documents/                  # AI 生成的文档
│   └── superpowers/                # superpowers 插件产物
│       ├── plans/                  # 实现计划
│       └── specs/                  # 设计规范
```

**先询问是否创建 Codex 目录**（使用 `AskUserQuestion`）：并非所有机器都安装/使用 Codex（例如远端机器仅有 Claude Code，Codex 只在本地机器上），因此 `Codex/` 与 `Codex/current-codex-memories/` 为可选目录。

```
是否在外部路径下创建 Codex 记忆同步目录？
1. 创建（默认）—— 本机使用 Codex，或需与本地 Codex 共享记忆
2. 不创建 —— 本机无 Codex（如远端机器仅运行 Claude Code）
```

将用户选择记录为 `$CREATE_CODEX_DIR`（`true` 或 `false`）。

- `$CREATE_CODEX_DIR` = `true` → 创建包括 `Codex/`、`Codex/current-codex-memories/` 在内的全部目录。
- `$CREATE_CODEX_DIR` = `false` → 跳过 `Codex/` 及其子目录，仅创建 `Claude/`、`Leo-Documents/` 及 superpowers 子目录。

使用 `mkdir -p` 创建（已存在的目录保持幂等，不重复创建）。

> **下游影响（Step 10 / Step 12）**：当 `$CREATE_CODEX_DIR` = `false` 时，Step 10 写入 CLAUDE.md「外部文档路径」表时**不要列出** `$EXT_DOC_PATH/Codex/` 行；Step 12 最终总结的目录树中也**省略** Codex 相关条目，保持文档与实际目录一致。

**执行后汇报**：列出哪些目录是新创建的，哪些已经存在，以及 Codex 目录是否按选择创建/跳过。

#### Step 3 补充：外部文档目录 Git 管理（仅 `$DOC_IS_LOCAL` = `false` 时执行）

外部文档目录独立于项目代码仓库。询问用户是否为该目录开启 Git，用于在本地记录文档变化。**默认仅本地管理，不推送远端**；只有用户显式给出远端仓库地址并授权时，才 commit and push 到远端。

> **如果 `$DOC_IS_LOCAL` = `true`（项目内模式）**：跳过本补充节，外部目录即项目自身的 `docs/`，已纳入项目代码仓库，无需单独管理。

使用 `AskUserQuestion` 询问（至少 2 个选项）：

- 选项 1（推荐）：启用 Git（仅本地）—— 在 `$EXT_DOC_PATH` 初始化本地仓库记录文档变化，**不推送远端**
- 选项 2：启用 Git 并配置远端 —— 需提供远端仓库地址，允许 commit and push 到远端
- 选项 3：不启用 Git

将选择记录为 `$EXT_GIT_ENABLED`（`true`/`false`）与 `$EXT_GIT_REMOTE`（远端地址，未配置则为空）。

**如果选项 1 或 2（`$EXT_GIT_ENABLED` = `true`）**：

1. 初始化（幂等）：若 `$EXT_DOC_PATH/.git` 不存在则在 `$EXT_DOC_PATH` 下 `git init`；已存在则跳过。
2. 设置该仓库的本地 Git 身份（不加 `--global`）：复用 Step 4 的 `$GIT_USER_NAME` / `$GIT_USER_EMAIL`；若本步骤先于 Step 4 执行，则用默认值（Michael Leo / yhzemail61010@aliyun.com）或继承已有全局配置。
3. 写入/补充 `$EXT_DOC_PATH/.gitignore`（排除系统垃圾文件，如 `.DS_Store`、`Thumbs.db`、临时文件等）。敏感记忆按既有同步策略本就不会写入此目录，故无需额外排除。
4. 首次提交：`git add .` 后提交，提交信息按 `$COMMIT_MSG_LANG`（默认英文）：
   - 英文：`docs: initialize external documentation repository`
   - 中文：`docs: 初始化外部文档仓库`
   - 若无文件可提交则跳过提交并汇报。

**如果选项 2（额外配置远端）**：

5. 询问并校验远端地址 `$EXT_GIT_REMOTE`（非空、形如 `git@...` 或 `https://...`）。
6. 配置远端：`git remote add origin <地址>`；若已存在 origin 则改用 `git remote set-url origin <地址>`。
7. **再次确认**用户授权推送后，执行 `git push -u origin <当前分支>`。未明确授权则**不推送**，仅保留本地提交并提示用户后续可手动推送。

**如果选项 3（`$EXT_GIT_ENABLED` = `false`）**：跳过所有 Git 操作。

**执行后汇报**：外部文档目录 Git 是否启用、是否已初始化/首次提交、远端是否配置与是否推送。

---

### Step 4/13: 询问 Git 用户信息

1. 先运行 `git config user.name` 和 `git config user.email` 读取当前项目配置。
2. **如果已设置**，展示当前值并询问："当前 Git 用户为 `<name> <email>`，是否沿用？(Y/n)"
   - 用户确认 → 记录并继续
   - 用户要修改 → 进入询问流程
3. **如果未设置**，使用默认值询问：
   ```
   请输入 Git 提交时使用的用户信息：
   - 用户名 (git user.name)（默认：Michael Leo）：
   - 邮箱 (git user.email)（默认：yhzemail61010@aliyun.com）：
   ```
   用户直接回车则使用默认值。
4. 通过 `git config user.name "<name>"` 和 `git config user.email "<email>"` 设置（**项目级**，不加 `--global`）。

将用户名记为 `$GIT_USER_NAME`，邮箱记为 `$GIT_USER_EMAIL`。

5. 询问 commit message 语言：
   ```
   Git commit message 使用什么语言编写？
   1. 英文（默认）
   2. 中文

   请选择 (1/2，默认 1)：
   ```
   将用户选择记录为 `$COMMIT_MSG_LANG`（`english` 或 `chinese`）。

6. 询问代码注释语言：
   ```
   代码注释使用什么语言编写？
   1. 英文（默认）
   2. 中文

   请选择 (1/2，默认 1)：
   ```
   将用户选择记录为 `$CODE_COMMENT_LANG`（`english` 或 `chinese`）。

这两项选择将在 Step 10 写入 CLAUDE.md 的"代码约定"段落中。

---

### Step 5/13: 询问项目类型与 GH_TOKEN 配置

首先询问项目类型：

```
本项目是 GitHub 项目还是内部项目？
1. GitHub 项目（代码托管在 GitHub）（默认）
2. 内部项目（代码托管在内部 GitLab/其他平台，或无远程仓库）

请选择 (1/2，默认 1)：
```

将用户选择记录为 `$PROJECT_TYPE`（`github` 或 `internal`）。

**如果用户选择"内部项目"** → 记录 `$GH_TOKEN_CONFIGURED = false`，跳到下一步。

**如果用户选择"GitHub 项目"**，继续询问 GH_TOKEN：

```
是否需要配置 GH_TOKEN 环境变量用于 GitHub API 操作？（默认：否）(y/N)
```

**如果用户选择"否"** → 记录 `$GH_TOKEN_CONFIGURED = false`，跳到下一步。

**如果用户选择"是"**：

1. 先展示 Token 生成指南：

```
如何在 GitHub 生成 Personal Access Token：

前往 https://github.com/settings/tokens

=== Fine-grained tokens（推荐，权限更精细） ===
1. 点击 "Generate new token" → "Fine-grained token"
2. 设置 Token name、Expiration（建议 90 天）
3. Resource owner：选择你的账户或组织
4. Repository access：选择 "Only select repositories" 并选中目标仓库
5. Permissions 设置：
   - Contents：Read and write（代码推送）
   - Pull requests：Read and write（创建/更新 PR）
   - Actions：Read and write（触发/查看 workflow）
   - Metadata：Read-only（自动授予）
6. 点击 "Generate token"

=== Tokens (classic)（传统方式，权限较粗） ===
1. 点击 "Generate new token" → "Generate new token (classic)"
2. 设置 Note、Expiration
3. 勾选以下 scope：
   - repo（全部子项：repo:status, repo_deployment, public_repo, repo:invite, security_events）
   - workflow（更新 GitHub Actions workflow）
   - read:org（读取组织成员信息，仅在组织仓库需要时勾选）
4. 点击 "Generate token"
```

2. 询问用户 Token：
```
请输入你的 GitHub Token（输入后会保存为敏感记忆，不会同步到外部路径）：
```

3. **安全处理**：
   - 将 Token 保存为项目记忆，**标记为敏感信息**，**绝不同步到外部路径**
   - 提醒用户使用方式：
     ```
     使用方法：
     - gh 命令：设置环境变量 GH_TOKEN=<your-token>，gh 会自动读取
     - git push：GH_TOKEN=<your-token> git push https://<username>@github.com/<owner>/<repo>.git <branch>
     ```

记录 `$GH_TOKEN_CONFIGURED = true`。

---

### Step 6/13: 询问记忆存储位置

**如果 `$DOC_IS_LOCAL` = `true`（项目内模式）**：

跳过询问，自动设置：
- `$MEMORY_LOCATION` = `project`
- `$MEMORY_PATH` = 项目根目录下 `.claude/memory/`
- 无额外同步目标（记忆已在项目内，不创建 `$EXT_DOC_PATH/Claude/` 目录）

汇报："项目内模式，记忆自动存放在 `.claude/memory/`"，然后继续。

**如果 `$DOC_IS_LOCAL` = `false`（外部路径模式）**：

```
项目记忆（记录协作约定、工作流偏好等）保存在哪里？

1. 外部路径（$EXT_DOC_PATH/Claude/）（默认）
   - 记忆独立于代码管理，不进入 git 仓库
   - 项目内 .claude/memory/MEMORY.md 仅保留指向外部路径的说明

2. 项目内（.claude/memory/）
   - 记忆跟随代码仓库，可被 git 管理和协作者共享
   - 同时会同步到外部路径 $EXT_DOC_PATH/Claude/

请选择 (1/2，默认 1)：
```

将用户选择记录为 `$MEMORY_LOCATION`（`external` 或 `project`），对应路径记为 `$MEMORY_PATH`：
- 选 1（默认） → `$MEMORY_PATH` = `$EXT_DOC_PATH/Claude/`
- 选 2 → `$MEMORY_PATH` = 项目根目录下 `.claude/memory/`

---

### Step 7/13: （已合并到 Step 10）

交互规则、语言偏好、文档路径、记忆位置等内容已直接写入 CLAUDE.md（Step 10），不再创建独立记忆文件。跳过此步骤。

---

### Step 8/13: 写入操作性记忆

仅创建无法写入 CLAUDE.md 的操作性记忆文件（敏感信息处理流程、凭据使用方式等）。每个文件写入前检查是否已存在（已存在且内容相同则跳过）。

**8a. `feedback_memory_sync_policy.md`**：

**如果 `$DOC_IS_LOCAL` = `true`（项目内模式）**：

```markdown
---
name: 记忆同步策略
description: 保存记忆时，无敏感信息保存到项目记忆；有敏感信息不写入并醒目告知
type: feedback
---

保存新记忆时，执行敏感信息检查。

**敏感信息定义：** API Token、密码、密钥、个人凭据、内部 IP/域名、数据库连接串、
以及包含 token/password/secret/key/credential 等关键词或疑似 Base64 编码的长字符串。

**无敏感信息 →** 保存到 `.claude/memory/`，并更新 MEMORY.md 索引。

**有敏感信息 →** 不写入可被 git 追踪的文件，并以如下格式醒目告知用户：

> **含敏感信息，未写入项目记忆**
> 文件：`<文件名>`
> 原因：检测到敏感信息类型 — <具体类型，如 API Token、数据库连接串等>
> 记忆仅保留在 Claude Code 内部记忆中。

**Why:** 防止凭据、密钥等敏感内容泄露。

**How to apply:** 每次保存记忆前，扫描内容是否含敏感关键词。无敏感 → 写入。有敏感 → 仅存内部并告知。
```

**如果 `$DOC_IS_LOCAL` = `false`（外部路径模式）**：

```markdown
---
name: 记忆同步策略
description: 保存记忆时，无敏感信息自动同步到外部路径；有敏感信息不同步并醒目告知
type: feedback
---

保存新记忆时，执行敏感信息检查后决定是否同步到外部路径 `$EXT_DOC_PATH/Claude/`。

**敏感信息定义：** API Token、密码、密钥、个人凭据、内部 IP/域名、数据库连接串、
以及包含 token/password/secret/key/credential 等关键词或疑似 Base64 编码的长字符串。

**无敏感信息 →** 自动同步到 `$EXT_DOC_PATH/Claude/`，并同步更新 MEMORY.md 索引。

**有敏感信息 →** 不同步，并以如下格式醒目告知用户：

> **未同步到外部路径**
> 文件：`<文件名>`
> 原因：检测到敏感信息类型 — <具体类型，如 API Token、数据库连接串等>
> 记忆仅保留在 Claude Code 内部记忆中，未写入 `$EXT_DOC_PATH/Claude/`。

**Why:** 防止凭据、密钥等敏感内容泄露到外部共享路径。

**How to apply:** 每次保存记忆前，扫描内容是否含敏感关键词。无敏感 → 同步。有敏感 → 仅存本地并告知。
```

**8b. `feedback_claude_md_sync.md`**：

**如果 `$DOC_IS_LOCAL` = `true`** → 跳过此文件，不创建。项目内模式无需同步 CLAUDE.md。

**如果 `$DOC_IS_LOCAL` = `false`**：

```markdown
---
name: CLAUDE.md 同步到外部路径
description: 每次更新项目中的 CLAUDE.md 时，同时复制一份到外部文档路径
type: feedback
---

每次更新项目中的 CLAUDE.md 时，同时复制到 `$EXT_DOC_PATH/CLAUDE.md`。

**Why:** 用户希望项目关键文件统一管理在外部文档目录下，便于不同 AI 工具共享。

**How to apply:** 修改 CLAUDE.md 后，执行复制到 `$EXT_DOC_PATH/CLAUDE.md`。
```

**8c. `feedback_external_docs_git.md`**：

**仅当 `$DOC_IS_LOCAL` = `false` 且 `$EXT_GIT_ENABLED` = `true`（Step 3 补充）时创建**，否则跳过。

```markdown
---
name: 外部文档目录 Git 策略
description: 外部文档目录默认仅本地 Git 记录变化，未经授权不推送远端
type: feedback
---

外部文档目录 `$EXT_DOC_PATH` 已启用独立的本地 Git 仓库，仅用于记录文档变化。

**默认行为：** 文档有变化时可在 `$EXT_DOC_PATH` 本地 `git add` / `git commit`，**不执行 `git push`**。

**推送远端的前提（两者同时满足）：** 用户显式给出远端仓库地址，且明确授权 commit and push 到该远端。
（本次配置的远端：`$EXT_GIT_REMOTE`，为空表示未配置远端、仅本地管理。）

**Why:** 外部文档可能含尚未公开或仅供本地留档的内容，默认不外推可避免误推送到远端泄露。

**How to apply:** 在 `$EXT_DOC_PATH` 提交文档后，除非满足上述前提，否则停在本地提交，不要 push。
```

**重要**：以上文件中的 `$EXT_DOC_PATH`、`$MEMORY_PATH`、`$EXT_GIT_REMOTE` 替换为前面步骤获取的**实际值**。

---

### Step 9/13: 创建 MEMORY.md 索引

在 `$MEMORY_PATH` 下创建（或更新）`MEMORY.md` 索引文件。

**格式**（每条一行，仅列出操作性记忆文件）：
```markdown
- [记忆同步策略](feedback_memory_sync_policy.md) — 无敏感信息保存到项目记忆，有敏感信息不写入并告知
```

如果 GH_TOKEN 已配置（Step 5），还需添加：
```markdown
- [GH_TOKEN 配置](feedback_gh_token.md) — 使用 GH_TOKEN 环境变量进行 GitHub 操作（敏感，未同步）
```

如果外部文档目录 Git 已启用（Step 3 补充，`$EXT_GIT_ENABLED` = `true`），还需添加：
```markdown
- [外部文档目录 Git 策略](feedback_external_docs_git.md) — 外部文档目录默认仅本地 Git，未授权不推送远端
```

**注意**：交互规则、语言偏好、文档路径、记忆位置等信息已直接写入 CLAUDE.md（Step 10），不需要在 MEMORY.md 中重复索引。

**同步逻辑**：

**如果 `$DOC_IS_LOCAL` = `true`**：无需额外同步，记忆已在项目内 `.claude/memory/`。

**如果 `$DOC_IS_LOCAL` = `false`**：
- 如果记忆在项目内 → 将非敏感的记忆文件和 MEMORY.md 同步到 `$EXT_DOC_PATH/Claude/`
- 如果记忆在外部 → 在项目内 `.claude/memory/MEMORY.md` 写入以下内容：
  ```markdown
  本项目记忆存储在外部路径，请读取以下文件获取完整记忆：
  $EXT_DOC_PATH/Claude/MEMORY.md
  ```

---

### Step 10/13: 更新/创建项目 CLAUDE.md

在项目根目录的 `CLAUDE.md` 中**追加**以下段落。如果 CLAUDE.md 不存在，创建新文件。如果已存在同名段落（`## 外部文档路径` 等），询问用户是否覆盖。

**追加内容（根据 `$DOC_IS_LOCAL` 分化）**：

**如果 `$DOC_IS_LOCAL` = `true`（项目内模式）**：

```markdown
## 外部文档路径

本项目的 AI 生成文档统一管理在项目 `$EXT_DOC_PATH/` 目录下：

| 路径 | 用途 |
|------|------|
| `$EXT_DOC_PATH/superpowers/specs/` | superpowers 设计文档（brainstorm 产物） |
| `$EXT_DOC_PATH/superpowers/plans/` | superpowers 实现计划（writing-plans 产物） |

> **superpowers 产物存放规则**（覆盖 skill 默认的 `docs/superpowers/` 路径）：
> - 使用 brainstorm（`superpowers:brainstorming`）技能生成的**设计文档**保存到 `$EXT_DOC_PATH/superpowers/specs/`
> - 使用 `superpowers:writing-plans` 技能生成的**实现计划**保存到 `$EXT_DOC_PATH/superpowers/plans/`
> - 文件名格式 `YYYY-MM-DD-<topic>.md`，superpowers 生成的所有文档一律使用中文编写。

## AI 交互规则

- 若有不明白或不明确的地方，一定要先问我。不要自己幻想或无中生有。
- 用户偏好使用中文对话。
- 如需派发代理（subagent）让工作并行进行，代理一律使用与当前会话相同的模型，不要指定其它模型。

## 项目记忆

项目级记忆存储在 `.claude/memory/` 目录中，包含跨会话的协作约定和工作流偏好。

新会话开始时，请先读取 `.claude/memory/MEMORY.md` 了解已有的记忆内容。
```

**如果 `$DOC_IS_LOCAL` = `false`（外部路径模式）**：

```markdown
## 外部文档路径

本项目的 AI 生成文档统一管理在：`$EXT_DOC_PATH/`

| 路径 | 用途 |
|------|------|
| `$EXT_DOC_PATH/Claude/` | Claude Code 记忆同步 |
| `$EXT_DOC_PATH/Codex/` | Codex 记忆同步（仅当 Step 3 `$CREATE_CODEX_DIR` = `true` 时列出，否则删除本行） |
| `$EXT_DOC_PATH/Leo-Documents/` | AI 生成的文档 |
| `$EXT_DOC_PATH/Leo-Documents/superpowers/specs/` | superpowers 设计文档（brainstorm 产物） |
| `$EXT_DOC_PATH/Leo-Documents/superpowers/plans/` | superpowers 实现计划（writing-plans 产物） |
| `$EXT_DOC_PATH/CLAUDE.md` | 同步的 CLAUDE.md 副本 |

> **superpowers 产物存放规则**（覆盖 skill 默认的 `docs/superpowers/` 路径）：
> - 使用 brainstorm（`superpowers:brainstorming`）技能生成的**设计文档**保存到 `$EXT_DOC_PATH/Leo-Documents/superpowers/specs/`
> - 使用 `superpowers:writing-plans` 技能生成的**实现计划**保存到 `$EXT_DOC_PATH/Leo-Documents/superpowers/plans/`
> - 文件名格式 `YYYY-MM-DD-<topic>.md`，superpowers 生成的所有文档一律使用中文编写。

> **外部文档目录 Git 策略**（仅当 Step 3 补充已启用外部目录 Git，即 `$EXT_GIT_ENABLED` = `true` 时写入本段，否则删除）：外部文档目录 `$EXT_DOC_PATH` 使用独立的本地 Git 仓库记录文档变化，**默认仅本地提交、不推送远端**；只有用户显式给出远端仓库地址并授权时，才 commit and push 到远端。

## AI 交互规则

- 若有不明白或不明确的地方，一定要先问我。不要自己幻想或无中生有。
- 用户偏好使用中文对话。
- 如需派发代理（subagent）让工作并行进行，代理一律使用与当前会话相同的模型，不要指定其它模型。

## 项目记忆

项目级记忆存储在 `$MEMORY_PATH` 目录中，包含跨会话的协作约定和工作流偏好。

新会话开始时，请先读取 `$EXT_DOC_PATH/Claude/MEMORY.md` 了解已有的记忆内容，便于重新唤醒记忆。
```

**代码约定追加**（独立于上述模板，不要写在代码块内）：

检查 CLAUDE.md 中是否已有 `## 代码约定` 段落：
- **已有** → 在该段落末尾追加以下两行（避免重复）：
  - `- Git commit message 使用 $COMMIT_MSG_LANG 编写`（融入已有的 commit 相关条目，如有）
  - `- 代码注释使用 $CODE_COMMENT_LANG 编写`
- **没有** → 在"项目记忆"段落之前新建 `## 代码约定` 段落，写入以上两行

**写入后**：
- 如果 `$DOC_IS_LOCAL` = `false` → 将 CLAUDE.md 同步复制到 `$EXT_DOC_PATH/CLAUDE.md`
- 如果 `$DOC_IS_LOCAL` = `true` → 跳过同步（CLAUDE.md 已在项目根目录，无需复制到项目内子目录）

---

### Step 11/13: 配置新会话读取外部记忆（已在 Step 10 中完成）

此步骤的内容已包含在 Step 10 的"项目记忆"段落中。确认 CLAUDE.md 中已写入新会话读取指引即可。

---

### Step 12/13: 最终总结输出

执行完毕后，向用户展示完整的配置总结：

**如果 `$DOC_IS_LOCAL` = `true`（项目内模式）**：

```
═══════════════════════════════════════════════════════
  AI 工具初始化配置完成
═══════════════════════════════════════════════════════

文档根路径：$EXT_DOC_PATH/（项目内模式）
├── superpowers/                    → superpowers 插件产物
│   ├── plans/                      → 实现计划
│   └── specs/                      → 设计规范
└── (生成的文档直接放在这里)

记忆存储位置：.claude/memory/（仅操作性记忆）
├── MEMORY.md                       → 记忆索引
├── feedback_memory_sync_policy.md  → 敏感信息检查策略
└── feedback_gh_token.md            → GH_TOKEN 使用方式（如已配置）

项目约定已写入 CLAUDE.md：外部路径、交互规则、代码约定（含语言偏好）、记忆配置

Git 用户：$GIT_USER_NAME <$GIT_USER_EMAIL>
GH_TOKEN：[已配置 / 未配置]

═══════════════════════════════════════════════════════
```

**如果 `$DOC_IS_LOCAL` = `false`（外部路径模式）**：

```
═══════════════════════════════════════════════════════
  AI 工具初始化配置完成
═══════════════════════════════════════════════════════

外部文档根路径：$EXT_DOC_PATH/
├── Claude/                         → Claude Code 记忆同步
├── Codex/                          → Codex 记忆同步（仅当 $CREATE_CODEX_DIR=true，否则省略本节）
│   └── current-codex-memories/     → Codex 当前记忆
├── Leo-Documents/                  → AI 生成的文档
│   └── superpowers/                → superpowers 插件产物
│       ├── plans/                  → 实现计划
│       └── specs/                  → 设计规范
├── CLAUDE.md                       → 同步的 CLAUDE.md 副本
└── [其他项目特定目录]

记忆存储位置：$MEMORY_PATH（仅操作性记忆）
├── MEMORY.md                       → 记忆索引
├── feedback_memory_sync_policy.md  → 敏感信息检查与同步策略
├── feedback_claude_md_sync.md      → CLAUDE.md 同步规则
├── feedback_gh_token.md            → GH_TOKEN 使用方式（如已配置）
└── feedback_external_docs_git.md   → 外部文档目录 Git 策略（如已启用）

项目约定已写入 CLAUDE.md：外部路径、交互规则、代码约定（含语言偏好）、记忆配置

Git 用户：$GIT_USER_NAME <$GIT_USER_EMAIL>
GH_TOKEN：[已配置（敏感，未同步到外部路径） / 未配置]
外部文档目录 Git：[未启用 / 仅本地（已首次提交） / 已配置远端 $EXT_GIT_REMOTE 并推送]

═══════════════════════════════════════════════════════
```

**注意**：总结中的 `$EXT_DOC_PATH`、`$MEMORY_PATH`、`$GIT_USER_NAME`、`$GIT_USER_EMAIL` 等占位符必须替换为实际值。

---

### Step 13/13: 检查并更新 AI 工具入口文件

在最终总结输出后，检查项目中的 AI 工具入口文件，确认是否需要根据本次命令的执行结果进行更新。

**需要检查的入口文件**：
- `CLAUDE.md` — Claude Code 的项目入口文件
- `AGENTS.md` — 多 AI 工具共享的仓库指南文件
- `.claude/settings.local.json` — Claude Code 项目级配置
- 其他项目中已存在的 AI 工具入口文件（如 `.codex/` 相关配置）

**检查逻辑**：

1. 逐一读取上述文件（如果存在），对照本次命令执行的最终结果，检查以下内容是否需要更新：
   - 外部文档路径是否已正确写入
   - 记忆存储位置是否已正确写入
   - AI 交互规则（"若有不明白或不明确的地方..."）是否已写入
   - 新会话读取外部记忆的指引是否已写入
   - Git 用户信息、commit message 语言、代码注释语言等配置是否已体现
   - 项目类型（GitHub/内部）和 GH_TOKEN 使用方式是否已体现

2. 如果发现某个入口文件**需要更新**，使用 `AskUserQuestion` 工具向用户展示：
   - 需要更新的文件名
   - 具体需要新增或修改的内容摘要
   - 选项：立即更新 / 跳过

3. 如果发现某个入口文件**已经是最新**（本次 Step 10 已更新过或内容已一致），跳过并汇报"已是最新"。

4. 如果项目中不存在 `AGENTS.md`，询问用户是否需要创建。

**更新后**：
- 如果 `$DOC_IS_LOCAL` = `false` → 将更新过的入口文件同步到 `$EXT_DOC_PATH/`（如 CLAUDE.md → `$EXT_DOC_PATH/CLAUDE.md`）
- 如果 `$DOC_IS_LOCAL` = `true` → 跳过同步

## 边界与禁止事项

- 不对**项目代码仓库**执行 `git add` / `git commit` / `git push`
- 唯一例外：Step 3 补充中用户显式启用「外部文档目录 Git」时，可对**外部文档目录**（`$EXT_DOC_PATH`，独立于项目代码仓库）执行 `git init` / `git add` / `git commit`；`git push` 仅在用户给出远端地址并授权后执行，默认不推送
- 不将 Token、密码等敏感信息写入可能被提交的文件
- 不覆盖已有记忆文件（仅新增或在用户确认后更新）
- 不修改全局 `~/.claude/CLAUDE.md`（只修改项目级 CLAUDE.md）
- 不安装或配置插件 / skills
- 外部路径使用绝对路径，去除尾部斜杠
- 所有占位符（`$EXT_DOC_PATH` 等）在实际写入文件时必须替换为真实路径
