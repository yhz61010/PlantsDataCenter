---
name: Git 提交身份
description: 本仓库提交一律用 Michael Leo <yhzemail61010@aliyun.com>，勿用旧公司身份
type: feedback
---

本仓库(PlantsDataCenter,公开于 github.com/yhz61010/PlantsDataCenter)的**所有提交**必须使用统一身份:

- `git config user.name`  = `Michael Leo`
- `git config user.email` = `yhzemail61010@aliyun.com`

**切勿**使用旧公司身份提交。

**Why:** 公开的个人项目;历史已统一为该身份,勿用旧身份污染。

**How to apply:**
- 新会话/新机器上,先确认项目级身份:`git config user.name` / `git config user.email`;不对就用
  `git config user.name "Michael Leo"` 和 `git config user.email "yhzemail61010@aliyun.com"` 设为项目级(不加 `--global`)。
- 在其它机器操作前,先 `git fetch origin && git reset --hard origin/main` 对齐历史(避免带回旧身份)。

相关:[[记忆同步策略]]
