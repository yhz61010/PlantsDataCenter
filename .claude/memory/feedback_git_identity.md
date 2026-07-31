---
name: Git 提交身份
description: 本仓库提交一律用 Michael Leo <yhzemail61010@aliyun.com>，勿用旧公司身份
type: feedback
---

本仓库(PlantsDataCenter,公开于 github.com/yhz61010/PlantsDataCenter)的**所有提交**必须使用统一身份:

- `git config user.name`  = `Michael Leo`
- `git config user.email` = `yhzemail61010@aliyun.com`

**切勿**使用旧公司身份提交。

**Why:** 这是公开的个人项目;早期曾误用公司邮箱提交,已于 2026-07-29 通过改写全历史 + force-push
统一为上面的个人身份。若再用公司邮箱提交并推送,会把该邮箱重新暴露到公开历史里,前功尽弃。

**How to apply:**
- 新会话/新机器上,先确认项目级身份:`git config user.name` / `git config user.email`;不对就用
  `git config user.name "Michael Leo"` 和 `git config user.email "yhzemail61010@aliyun.com"` 设为项目级(不加 `--global`)。
- 在其它机器操作前,先 `git fetch origin && git reset --hard origin/main` 对齐改写后的历史,避免把旧的
  公司邮箱提交带回来。

相关:[[记忆同步策略]]
