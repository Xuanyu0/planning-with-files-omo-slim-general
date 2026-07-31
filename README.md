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

#### 获取仓库

先克隆本仓库到本地，后续 `<repo>` 即仓库本地路径：

```bash
git clone git@github.com:Xuanyu0/planning-with-files-omo-slim-general.git
```

#### 一键安装 / 更新（推荐）

仓库自带安装脚本，**安装与更新是同一命令**：

```bash
python3 <repo>/install.py <你的项目路径>
```

- **安装**：首次运行即完成全部安装；目标项目路径不存在会自动创建
- **更新**：重复运行同一命令即为更新（幂等，重跑安全）
- 前置依赖见上文

**脚本行为**：

1. 复制 skill 目录 → `<项目>/.opencode/skills/planning-with-files-omo-slim-general/`
2. 合并全局配置 `~/.config/opencode/oh-my-opencode-slim.json`：
   - 写入 `agents.cleaner` 与 `presets.planning-with-files-omo-slim-general`（覆盖式）
   - 自动清理旧命名 `simplifier`（agent 定义与 `simplifier.md`）
   - 覆盖前自动备份为 `oh-my-opencode-slim.json.bak`
   - 保留你现有的顶层 `preset`；若未激活本 skill，会提示手动切换
3. 复制 `cleaner.md` 与 fixer/oracle append 提示词到全局 preset 专属目录
4. 逐项验证并输出 ✅ / ❌

> 若全局配置存在旧命名 `simplifier`，安装/更新时会被自动升级为 `cleaner`。

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

####  工作流

```
启动 -> 探索方案 -> 规划 -> 执行与验证 -> 用户检查 -> 提交 -> Agent 反思
```

详细 Skill 内容及其说明见 [.opencode/skills/planning-with-files-omo-slim-general/SKILL.md](.opencode/skills/planning-with-files-omo-slim-general/SKILL.md)。
