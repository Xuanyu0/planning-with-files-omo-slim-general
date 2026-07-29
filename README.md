# planning-with-files-omo-slim-general

## 简介

利用文档 + OMO-slim 进行开发规划的工作流 skill。
借鉴于 [planning-with-files](https://github.com/OthmanAdi/planning-with-files/)
目前仅适用于 [oh-my-opencode-slim](https://github.com/alvinunreal/oh-my-opencode-slim)
根据一个个人的项目开发不断调优得来

## skill 特点

* 人类工程师对 AI Agents 高度可控
* 省 token（也许？）

## 前置依赖

- [OpenCode](https://github.com/alvinunreal/opencode) 已安装
- [oh-my-opencode-slim](https://github.com/alvinunreal/oh-my-opencode-slim) 插件已安装并配置

## 使用说明

以下过程以配置全局 preset 加上项目级 skill 为主要方式

其他配置方式可以参考 [oh-my-opencode-slim](https://github.com/alvinunreal/oh-my-opencode-slim) 仓库

### 安装

#### 1. Skill 文件配置

将 `.opencode/skills/planning-with-files-omo-slim-general/` 复制到你项目的 `.opencode/skills/` 下：

```bash
cp -r <repo>/.opencode/skills/planning-with-files-omo-slim-general 你的项目/.opencode/skills/
```

#### 2. OMO-slim 配置（设置preset）

将 `.config/opencode/oh-my-opencode-slim.json` 的 simplifier 定义整合到你自己的 `~/.config/opencode/oh-my-opencode-slim.json` 中。

#### 3. Agent append 提示词

**如果只想提示词在 `planning-with-files-omo-slim-general` preset 激活时生效**，可以放进omo-slim下的 preset 专属目录：

```bash
cp <repo>/.opencode/fixer_append.md ~/.config/opencode/oh-my-opencode-slim/planning-with-files-omo-slim-general/
cp <repo>/.opencode/oracle_append.md ~/.config/opencode/oh-my-opencode-slim/planning-with-files-omo-slim-general/
```

### 使用

在 OpenCode 会话中触发此 skill：

1. 确保 `oh-my-opencode-slim` 插件已安装并启用
2. 使用以下触发词激活：
   - "制定开发文档" / "记录你的发现"
   - "拆解步骤" / "划分阶段"
   - "按照工作流执行" / "用工作流"

#### 使用 skill 创建的核心文件结构

skill 激活前，需要主动创建 `docs/开发文档/<阶段名>/` ，

例如：

```
docs/开发文档/<阶段名>/
├── 00-总纲.md              ← 总体路线图、步骤总表
├── 步骤/
│   └── 01-<步骤名>.md      ← 步骤规划
├── 发现/
│   └── 01-<步骤名>.md      ← 发现记录
└── 提示词/
    └── 01-<步骤名>/
        └── 1.1-<内容>.md   ← 执行契约
```

#### 典型工作流

```
开发启动协议 → 用户指明方向 → 撰写步骤文档 → 用户确认
→ 撰写提示词文件 → 用户确认（可选） → 执行（@fixer/@designer）
→ 简化（@simplifier，可选） → 验证（@oracle） → 更新文档
→ 用户确认 → git commit
```

详细 Skill 内容及其说明见 [.opencode/skills/planning-with-files-omo-slim-general/SKILL.md](.opencode/skills/planning-with-files-omo-slim-general/SKILL.md)。
