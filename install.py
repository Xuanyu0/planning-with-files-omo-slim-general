#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""planning-with-files-omo-slim-general 安装 / 更新脚本

将 skill 安装到目标项目，并把 cleaner / preset 配置合并进全局
oh-my-opencode-slim 配置。幂等：重复运行即为更新。

用法：python3 install.py <目标项目路径>
例：  python3 install.py /path/to/my-project

安装内容：
  1. 复制 skill 目录 → <目标项目>/.opencode/skills/
  2. 合并全局配置 ~/.config/opencode/oh-my-opencode-slim.json：
     - agents.cleaner 与 presets.planning-with-files-omo-slim-general 覆盖式写入
     - 自动清理旧命名 simplifier（定义与 simplifier.md）
     - 覆盖前自动备份为 oh-my-opencode-slim.json.bak
     - 保留用户现有顶层 preset，若未激活本 skill 则输出提醒
  3. 复制 cleaner.md 与 fixer/oracle append 提示词
  4. 验证安装结果
"""

import json
import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
SKILL_DIR = REPO / ".opencode" / "skills" / "planning-with-files-omo-slim-general"
CONFIG_JSON = REPO / ".config" / "opencode" / "oh-my-opencode-slim.json"
CLEANER_MD = REPO / ".config" / "opencode" / "oh-my-opencode-slim" / "cleaner.md"
APPEND_DIR = REPO / ".config" / "opencode" / "planning-with-files-omo-slim-general"

OMOS = Path.home() / ".config" / "opencode"
OMOS_JSON = OMOS / "oh-my-opencode-slim.json"
OMOS_AGENT_DIR = OMOS / "oh-my-opencode-slim"
OMOS_APPEND_DIR = OMOS_AGENT_DIR / "planning-with-files-omo-slim-general"
PRESET = "planning-with-files-omo-slim-general"


def check(ok, msg):
    print(f"{'✅' if ok else '❌'} {msg}")
    return ok


def copy_tree(src, dst):
    """复制目录（覆盖已存在文件，保留目标多余文件），幂等。"""
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.rglob("*"):
        rel = item.relative_to(src)
        target = dst / rel
        if item.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(item, target)


def merge_config(src, dst):
    """把 src 的 agents.cleaner / presets 合并进 dst，清理 simplifier，保留顶层 preset。"""
    agents = dst.setdefault("agents", {})
    agents["cleaner"] = src["agents"]["cleaner"]
    agents.pop("simplifier", None)

    presets = dst.setdefault("presets", {})
    presets[PRESET] = src["presets"][PRESET]
    # 顶层 preset 保留用户现有，不做修改


def main():
    if len(sys.argv) != 2:
        print("用法: python3 install.py <目标项目路径>")
        print("例:   python3 install.py /path/to/my-project")
        sys.exit(1)

    target = Path(sys.argv[1])
    target.mkdir(parents=True, exist_ok=True)
    if not target.is_dir():
        print(f"错误: 不是目录 — {target}", file=sys.stderr)
        sys.exit(1)

    ok = True
    print("══ 安装 planning-with-files-omo-slim-general ══")

    # ── 1. 复制 skill 目录 ──────────────────────────────────────────────────
    print("\n[1/3] Skill 文件")
    if not SKILL_DIR.is_dir():
        check(False, f"源 skill 目录缺失: {SKILL_DIR}")
        sys.exit(1)
    copy_tree(SKILL_DIR, target / ".opencode" / "skills" / SKILL_DIR.name)
    ok &= check((target / ".opencode" / "skills" / SKILL_DIR.name / "SKILL.md").is_file(),
                f"skill 已复制到 {target}/.opencode/skills/")

    # ── 2. 合并全局配置 ─────────────────────────────────────────────────────
    print("\n[2/3] 全局 OMO-slim 配置")
    if not CONFIG_JSON.is_file():
        check(False, f"源配置缺失: {CONFIG_JSON}")
        sys.exit(1)

    with open(CONFIG_JSON, encoding="utf-8") as f:
        src_data = json.load(f)

    if OMOS_JSON.is_file():
        backup = OMOS_JSON.with_suffix(".json.bak")
        shutil.copy2(OMOS_JSON, backup)
        with open(OMOS_JSON, encoding="utf-8") as f:
            dst_data = json.load(f)
        merge_config(src_data, dst_data)
        with open(OMOS_JSON, "w", encoding="utf-8") as f:
            json.dump(dst_data, f, ensure_ascii=False, indent=2)
        ok &= check(True, f"配置已合并（备份: {backup.name}）")
    else:
        OMOS.mkdir(parents=True, exist_ok=True)
        shutil.copy2(CONFIG_JSON, OMOS_JSON)
        ok &= check(True, "全局配置不存在，已新建")

    # cleaner.md
    OMOS_AGENT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy2(CLEANER_MD, OMOS_AGENT_DIR / "cleaner.md")
    ok &= check(True, f"cleaner.md → {OMOS_AGENT_DIR}/cleaner.md")

    # 清理旧命名
    old_md = OMOS_AGENT_DIR / "simplifier.md"
    if old_md.exists():
        old_md.unlink()
        ok &= check(True, "已删除旧命名 simplifier.md")
    else:
        ok &= check(True, "无旧命名 simplifier.md，无需清理")

    # ── 3. 复制 append 提示词 ───────────────────────────────────────────────
    print("\n[3/3] Agent append 提示词")
    OMOS_APPEND_DIR.mkdir(parents=True, exist_ok=True)
    for name in ("fixer_append.md", "oracle_append.md"):
        src = APPEND_DIR / name
        if src.is_file():
            shutil.copy2(src, OMOS_APPEND_DIR / name)
            ok &= check(True, f"{name} → {OMOS_APPEND_DIR}/")
        else:
            ok &= check(False, f"源文件缺失: {src}")

    # ── 4. 验证 ─────────────────────────────────────────────────────────────
    print("\n══ 验证 ══")
    dst_skill = target / ".opencode" / "skills" / SKILL_DIR.name
    ok &= check((dst_skill / "SKILL.md").is_file(), "Step 1: Skill 文件就绪")
    ok &= check((dst_skill / "scripts" / "dev-status.py").is_file(), "Step 1: dev-status.py 就绪")
    ok &= check(OMOS_JSON.is_file() and "cleaner" in OMOS_JSON.read_text(encoding="utf-8"),
                "Step 2: cleaner 配置就绪")
    ok &= check((OMOS_AGENT_DIR / "cleaner.md").is_file(), "Step 2: cleaner.md 就绪")
    ok &= check((OMOS_APPEND_DIR / "fixer_append.md").is_file()
                and (OMOS_APPEND_DIR / "oracle_append.md").is_file(),
                "Step 3: append 提示词就绪")

    # ── 5. preset 提醒 ──────────────────────────────────────────────────────
    if OMOS_JSON.is_file():
        try:
            with open(OMOS_JSON, encoding="utf-8") as f:
                cur = json.load(f).get("preset")
        except (json.JSONDecodeError, OSError):
            cur = None
        if cur != PRESET:
            cur_disp = cur if cur else "（未设置）"
            print(f"\n⚠ 当前全局 preset 为 {cur_disp}，未激活本 skill 工作流。")
            print(f"  如需启用，请将 ~/.config/opencode/oh-my-opencode-slim.json 的顶层 "
                  f'"preset" 改为 "{PRESET}"。')

    print()
    print("✅ 安装完成" if ok else "❌ 存在失败项，请检查上方输出")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
