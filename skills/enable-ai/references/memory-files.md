# 操作性记忆文件模板

仅在 `MEMORY_MODE=project` 或 `MEMORY_MODE=external` 时使用。把占位符替换为实际值；只创建当前配置需要的文件。

## feedback_memory_sync_policy.md

```markdown
---
name: 记忆保存策略
description: 非敏感操作性记忆按项目选择的路径维护，敏感信息永不落盘
type: feedback
---

保存或更新项目操作性记忆前，先检查内容是否包含 Token、密码、密钥、个人凭据、数据库连接串、内部地址或其它秘密。

- 无敏感信息：保存到 `<MEMORY_PATH>/`，并按需更新 `MEMORY.md` 索引。
- 有敏感信息：不写入项目、外部目录或记忆文件；告知用户哪些内容因敏感而未保存。

这些文件是项目记忆快照，不代表已自动同步到 Codex 内置记忆。
```

## feedback_agents_md_sync.md

仅外部文档模式且用户选择同步 `AGENTS.md` 副本时创建：

```markdown
---
name: AGENTS.md 外部镜像策略
description: 项目 AGENTS.md 更新后同步到已确认的外部文档根目录
type: feedback
---

项目根 `AGENTS.md` 是项目规则真相源。更新后，把非敏感内容同步到 `<DOC_ROOT>/AGENTS.md`，并用比较命令确认副本一致。

不要从外部副本反向覆盖项目文件，除非用户明确要求并已审查差异。
```

## feedback_external_docs_git.md

仅启用外部文档 Git 时创建：

```markdown
---
name: 外部文档 Git 策略
description: 外部文档仓库默认只本地提交，push 必须单独授权
type: feedback
---

外部文档根目录 `<DOC_ROOT>` 使用独立 Git 仓库记录变化。

- 只提交本次确认的文档与配置文件，不加入既有无关文件。
- 默认停在本地提交。
- 只有远端地址已确认且用户明确授权本次 push 时才推送。
```

## feedback_gh_token.md

仅用户选择 GitHub 使用说明时创建：

```markdown
---
name: GH_TOKEN 使用规则
description: GitHub 操作通过当前进程环境变量认证，不保存 Token 值
type: feedback
---

需要 GitHub API 或 `gh` 认证时，从当前进程的 `GH_TOKEN` 环境变量读取凭据。

不要在项目文件、记忆文件、命令示例、远端 URL 或外部文档中记录真实 Token；不要要求用户在对话中粘贴 Token。
```

## MEMORY.md

只索引已创建的文件，保持每条一行。例如：

```markdown
- [记忆保存策略](feedback_memory_sync_policy.md) — 非敏感记忆按所选路径维护，敏感信息永不落盘
- [AGENTS.md 外部镜像策略](feedback_agents_md_sync.md) — 项目文件是真相源，外部文件仅作镜像
- [外部文档 Git 策略](feedback_external_docs_git.md) — 默认仅本地提交，push 需单独授权
- [GH_TOKEN 使用规则](feedback_gh_token.md) — 只使用环境变量，不保存 Token 值
```

删除未创建文件对应的示例行；保留用户已有的其它有效索引。
