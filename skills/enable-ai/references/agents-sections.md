# AGENTS.md 受管段落模板

只使用当前配置需要的段落。将所有占位符替换为已验证的实际值；合并到已有等价段落，不重复标题，也不删除仓库原有规则。

## 目录

- [文档路径](#文档路径)
- [交互规则](#交互规则)
- [代码约定](#代码约定)
- [项目记忆](#项目记忆)
- [GitHub 凭据说明](#github-凭据说明)

## 文档路径

项目内模式：

```markdown
## Codex 文档路径

本项目由 Codex 生成的协作文档统一存放在：`<AI_DOCS_ROOT>/`

| 路径 | 用途 |
|------|------|
| `<AI_DOCS_ROOT>/` | 普通分析、审查与说明文档 |
| `<AI_DOCS_ROOT>/superpowers/specs/` | 设计文档 |
| `<AI_DOCS_ROOT>/superpowers/plans/` | 实现计划 |

生成文档使用中文和 UTF-8；普通文档文件名使用 `YYYY-MM-DD-<kebab-case-topic>.md`。
```

外部模式：

```markdown
## Codex 文档路径

本项目由 Codex 生成的协作文档统一存放在外部目录：`<AI_DOCS_ROOT>/`

| 路径 | 用途 |
|------|------|
| `<AI_DOCS_ROOT>/` | 普通分析、审查与说明文档 |
| `<AI_DOCS_ROOT>/superpowers/specs/` | 设计文档 |
| `<AI_DOCS_ROOT>/superpowers/plans/` | 实现计划 |

生成文档使用中文和 UTF-8；普通文档文件名使用 `YYYY-MM-DD-<kebab-case-topic>.md`。
```

## 交互规则

只有现有 `AGENTS.md` 没有等价规则时才补充：

```markdown
## Codex 交互规则

- 若有不明确且无法从当前代码、文档或命令结果确认的地方，先询问用户，不要臆造。
- 默认使用中文沟通。
- 需要用户选择时，优先使用当前环境提供的结构化输入；不可用时使用简短文本问题。
- 不把 Token、密码、密钥或其它敏感值写入可提交文件或外部共享目录。
```

## 代码约定

优先把缺失条目合并到仓库已有的代码约定段落：

```markdown
## 代码约定

- Git commit message 使用 `<COMMIT_MSG_LANG>`。
- 代码注释使用 `<CODE_COMMENT_LANG>`。
```

把语言占位符替换为“英文”或“中文”。不要覆盖仓库已有、更具体的代码风格。

## 项目记忆

`agents-only` 模式：

```markdown
## 项目记忆

项目共享协作规则以根目录 `AGENTS.md` 为准。本项目未配置 repo-local 或外部记忆快照；不要引用不存在的 `MEMORY.md`。
```

`project` 模式：

```markdown
## 项目记忆

项目操作性记忆存放在：`<MEMORY_PATH>/`。新会话需要相关历史上下文时，先读取 `<MEMORY_PATH>/MEMORY.md`，再按索引加载必要条目。

该目录是项目记忆快照，不代表已自动写入 Codex 内置记忆。
```

`external` 模式：

```markdown
## 项目记忆

项目操作性记忆存放在外部目录：`<MEMORY_PATH>/`。新会话需要相关历史上下文时，先读取 `<MEMORY_PATH>/MEMORY.md`，再按索引加载必要条目。

该目录是外部记忆快照，不代表已自动写入 Codex 内置记忆。
```

## GitHub 凭据说明

仅在用户选择写入 GitHub 使用说明时添加：

```markdown
## GitHub 凭据使用

- GitHub API 或 `gh` 操作通过当前进程的 `GH_TOKEN` 环境变量认证。
- 不在项目文件、记忆文件、命令示例或外部文档中保存 Token 值。
- 需要凭据时由用户在本地安全环境中设置；不要要求用户在对话中粘贴 Token。
```
