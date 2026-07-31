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

将 `.config/opencode/oh-my-opencode-slim.json` 的 cleaner 定义整合到你自己的 `~/.config/opencode/oh-my-opencode-slim.json` 中，同时将 `.config/opencode/oh-my-opencode-slim/cleaner.md` 复制到 `~/.config/opencode/oh-my-opencode-slim/cleaner.md`。

#### 3. Agent append 提示词

**如果只想提示词在 `planning-with-files-omo-slim-general` preset 激活时生效**，可以放进omo-slim下的 preset 专属目录：

```bash
cp <repo>/.config/opencode/planning-with-files-omo-slim-general/fixer_append.md ~/.config/opencode/oh-my-opencode-slim/planning-with-files-omo-slim-general/
cp <repo>/.config/opencode/planning-with-files-omo-slim-general/oracle_append.md ~/.config/opencode/oh-my-opencode-slim/planning-with-files-omo-slim-general/
```

#### 4. 验证安装

在目标项目根目录执行，按安装步骤逐一验证：

```bash
# Step 1: Skill 文件
test -f .opencode/skills/planning-with-files-omo-slim-general/SKILL.md \
  -a .opencode/skills/planning-with-files-omo-slim-general/scripts/dev-status.py \
  && echo "✅ Step 1: Skill 文件就绪" || echo "❌ Step 1: Skill 文件缺失"

# Step 2: Cleaner 配置
test -f ~/.config/opencode/oh-my-opencode-slim/cleaner.md \
  && grep -q '"cleaner"' ~/.config/opencode/oh-my-opencode-slim.json \
  && echo "✅ Step 2: Simplifier 配置就绪" || echo "❌ Step 2: Simplifier 配置缺失"

# Step 3: Agent append 提示词
test -f ~/.config/opencode/oh-my-opencode-slim/planning-with-files-omo-slim-general/fixer_append.md \
  -a ~/.config/opencode/oh-my-opencode-slim/planning-with-files-omo-slim-general/oracle_append.md \
  && echo "✅ Step 3: Append 提示词就绪" || echo "❌ Step 3: Append 提示词缺失"
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

####  工作流

```
启动 -> 探索方案 -> 规划 -> 执行与验证 -> 用户检查 -> 提交 -> Agent 反思
```

详细 Skill 内容及其说明见 [.opencode/skills/planning-with-files-omo-slim-general/SKILL.md](.opencode/skills/planning-with-files-omo-slim-general/SKILL.md)。
