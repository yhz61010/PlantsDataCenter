---
name: Git 推送用 Token
description: 推送用用户当场提供的 PAT 走一次性内联 URL，token 绝不落盘；默认凭证对本仓库 403
type: feedback
---

推送到 GitHub 远端（github.com/yhz61010/PlantsDataCenter）要用**用户当场提供的 Personal Access Token（PAT）**。用户会在对话里发最新 token；token 变更时用户会重新提供。

**Why:** 默认凭证账号（`yhz61010`）对本仓库没有写权限，`git push` 会返回 403；只有用用户提供的 PAT 认证才能推。

**How to apply:**
- 用一次性内联 URL 推送：`git push "https://x-access-token:<TOKEN>@github.com/yhz61010/PlantsDataCenter.git" HEAD:main`
- **绝不**把 token 写进 `.git/config`、remote URL 或任何文件长期保存；每次推送用当次提供的 token。
- 打印/回显命令输出时对 `github_pat_*` 做掩码，避免二次泄露。
- 不要在本文件或任何记忆里存 token 明文——只存流程。

相关：[[Git 提交身份]]
