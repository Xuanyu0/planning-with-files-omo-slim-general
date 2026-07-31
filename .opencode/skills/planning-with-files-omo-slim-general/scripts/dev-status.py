#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""开发步骤状态检查脚本（Python 版）

dev-status.sh 的等价移植，仅依赖 Python 标准库。
与 bash 版唯一的刻意差异：找不到 "## 开发步骤" 标题时不解析任何步骤行
（bash 版此场景下会从第 4 行继续，属意外行为）。

功能：
    从总纲文档读取步骤列表，交叉验证步骤文件、提示词文件、发现文档，
    汇总输出每步的当前状态和信号标记。

用途：
    开发启动协议的第一步，在 read 步骤/发现文档之前获取全局视图。

用法：python3 dev-status.py <总纲文件路径>
例：  python3 dev-status.py docs/开发文档/P2开发文档/phase2b/00-总纲.md

入口：总纲文件路径（命令行参数 $1 → OUTLINE）
其他所有文件位置通过 OUTLINE 推导：
    BASE/步骤/{文件名}.md    — 步骤文档（由总纲表格"文件"列的 Markdown 链接指向）
    BASE/提示词/{文件名}/    — 提示词目录，与同步骤的步骤文档同名，内含 .md 提示词文件
    BASE/发现/{文件名}.md    — 发现文档，文件名与同步骤的步骤文档相同

输出格式：
    编号  文件                状态  距今    信号
    ────  ──────────────────  ────  ──────  ────────
    01    some-step          ✅     3天前
    02    another-step       🔨    今天    📄⚠1🔥

信号列（可叠加）：
    🔥 — 活跃：步骤文件最近 2 天内修改过，且有提示词文件存在
    📄 — 有提示词：该步骤对应的提示词目录下存在 .md 文件
    ⚠N — N 项待确认：发现文档中有 N 条状态为"⏳ 待确认"的条目
    💀 — 脏/搁置：步骤状态为 🔨（进行中），但超过 2 天未修改
"""

import os
import re
import sys
import time
import unicodedata

def display_width(s: str) -> int:
    """返回字符串的显示宽度。

    基于 unicodedata.east_asian_width：W/F 类字符占 2 格，其余 1 格；
    组合字符与变体选择符 FE0F 占 0 格。与 glibc wcwidth 语义基本一致
    （少数字符如 U+2705✅ 的 EAW 为 W 而 Kuhn 表为 1，本项目无影响）。
    """
    w = 0
    for ch in s:
        if unicodedata.combining(ch) or ch == "\ufe0f":
            continue
        w += 2 if unicodedata.east_asian_width(ch) in "WF" else 1
    return w


def column_widths(rows):
    """计算每列最大显示宽度（输入已 strip 的二维数组）。"""
    ncols = max(len(r) for r in rows)
    return [max(display_width(r[i]) if i < len(r) else 0 for r in rows)
            for i in range(ncols)]


def column_table(rows, sep="  "):
    """按列对齐输出，模拟 column -t -s '|' -o sep 的行为。

    字段首尾空白会被去掉，最后一列不补空格。返回逐行字符串列表。
    """
    if not rows:
        return []
    rows = [[f.strip() for f in r] for r in rows]
    widths = column_widths(rows)
    out = []
    for r in rows:
        cells = []
        for i in range(len(r)):
            cell = r[i]
            if i < len(widths) - 1:
                cell = cell + " " * max(0, widths[i] - display_width(cell))
            cells.append(cell)
        out.append(sep.join(cells))
    return out


def render_table(header, rows, sep="  "):
    """渲染带表头的表格：表头与数据参与同一列宽计算，分隔行动态生成。

    返回行字符串列表（含表头行和分隔行）。
    """
    all_rows = [header] + rows
    stripped = [[f.strip() for f in r] for r in all_rows]
    widths = column_widths(stripped)
    lines = column_table(all_rows)
    sep_line = sep.join("─" * w for w in widths)
    return [lines[0], sep_line] + lines[1:]


def count_prompts(prompt_dir):
    """统计目录下 *.md 文件数（非递归，含隐藏文件，与 find -name '*.md' 一致）。"""
    n = 0
    try:
        for e in os.scandir(prompt_dir):
            if e.name.endswith(".md"):
                n += 1
    except OSError:
        n = 0
    return n


def find_prompt_dir(base, dir_name):
    """返回 提示词 下名为 dir_name 的目录，不存在则返回 None。

    精确匹配（非前缀）：避免步骤间因相同编号前缀串用提示词目录。
    """
    pdir = os.path.join(base, "提示词", dir_name)
    return pdir if os.path.isdir(pdir) else None


def count_pending(disc_path):
    """统计发现文档中包含 '状态：⏳' 的行数。"""
    n = 0
    try:
        with open(disc_path, encoding="utf-8") as f:
            for ln in f:
                if "状态：⏳" in ln:
                    n += 1
    except OSError:
        n = 0
    return n


def mtime_or_now(path, now):
    try:
        return int(os.stat(path).st_mtime)
    except OSError:
        return now


def main():
    if len(sys.argv) != 2:
        print(f"用法: {sys.argv[0]} <总纲文件路径>")
        print(f"例:   {sys.argv[0]} docs/开发文档/P2开发文档/phase2b/00-总纲.md")
        sys.exit(1)

    outline = sys.argv[1]
    if not os.path.isfile(outline):
        print(f"错误: 文件不存在 — {outline}", file=sys.stderr)
        sys.exit(1)
    if os.path.basename(outline) != "00-总纲.md":
        print("错误: 文件名必须是 00-总纲.md", file=sys.stderr)
        sys.exit(1)

    base = os.path.dirname(os.path.abspath(outline))
    now = int(time.time())

    # ── 1. 从总纲提取步骤表格 ──────────────────────────────────────────────
    # 定位 "## 开发步骤" 标题，跳过 4 行（标题+空行+表头+分隔线），
    # 逐行读取，只保留 "| 数字" 开头的数据行，遇到空行或新标题停止。
    with open(outline, encoding="utf-8") as f:
        lines = f.read().splitlines()

    start = None
    for i, ln in enumerate(lines):
        if ln.startswith("## 开发步骤"):
            start = i
            break
    rows_text = []
    if start is not None:
        for ln in lines[start + 4:]:
            if ln.startswith("| ") and ln[2:3].isdigit():
                rows_text.append(ln)
            elif ln == "" or ln.startswith("#"):
                break

    # ── 2. 逐行解析步骤表格，生成状态输出 ───────────────────────────────────
    # 表格行格式：| 编号 | [文字](步骤文件.md) | 名称 | 状态 |
    # f2=编号  f3=Markdown 链接(提取文件名)  f5=状态
    data_rows = []
    for row in rows_text:
        fields = row.split("|")
        num = fields[1].strip() if len(fields) > 1 else ""
        # Markdown 链接 [文字](文件名.md)：取 ]( 之后到行末最后一个 ) 的内容。
        # 与 bash 版的 sed 's/.*(//;s/).*//' 不同：后者遇含 ) 的文件名会截断
        # （如 06-(修订)-测试.md → 修订）导致整行被跳过；此处完整提取。
        file_md = fields[2].strip() if len(fields) > 2 else ""
        m = re.search(r"\]\((.+)\)$", file_md)
        file = m.group(1) if m else ""
        file_disp = file[:-3] if file.endswith(".md") else file
        st = fields[4].strip() if len(fields) > 4 else ""
        if not st:
            st = "-"

        sf = os.path.join(base, "步骤", file)
        if not os.path.isfile(sf):
            continue

        # 2a. 距今天数
        mt = mtime_or_now(sf, now)
        days = (now - mt) // 86400
        if days == 0:
            ds = "今天"
        elif days == 1:
            ds = "1天前"
        else:
            ds = f"{days}天前"

        # 2b. 提示词文件数量（目录与步骤文件同名，file_disp 已含编号）
        ic = 0
        pdir = find_prompt_dir(base, file_disp)
        if pdir:
            ic = count_prompts(pdir)

        # 2c. 发现文档待确认项
        pc = count_pending(os.path.join(base, "发现", file))

        # 2d. 信号列（信号间单空格分隔，无前导/尾随空格）
        parts = []
        if ic > 0:
            parts.append("📄")
        if pc > 0:
            parts.append(f"⚠ {pc}")
        if st == "🔨" and days > 2:
            parts.append("💀")
        if days <= 2 and ic > 0:
            parts.append("🔥")
        sig = " ".join(parts)

        data_rows.append([num, file_disp, st, ds, sig])

    # ── 3. 输出主表格 ─────────────────────────────────────────────────────
    header = ["编号", "文件", "状态", "距今", "信号"]
    print("\n".join(render_table(header, data_rows)))

    # ── 4. 检测总纲未列出的活跃步骤 ─────────────────────────────────────────
    extra = []
    steps_dir = os.path.join(base, "步骤")
    if os.path.isdir(steps_dir):
        try:
            step_entries = sorted(os.scandir(steps_dir), key=lambda e: e.name)
        except OSError:
            step_entries = []
        for e in step_entries:
            if not e.name.endswith(".md"):
                continue
            sf = os.path.join(steps_dir, e.name)
            if not os.path.isfile(sf):
                continue
            nm = e.name[:-3]
            # 总纲已涵盖则跳过（grep -qF 子串匹配）
            if any(nm in rt for rt in rows_text):
                continue
            # 只显示最近 2 天内修改的游离步骤
            mt = mtime_or_now(sf, now)
            if (now - mt) // 86400 > 2:
                continue

            m = re.match(r"^\d+", nm)
            nu = m.group(0) if m else ""

            ic = 0
            pdir = find_prompt_dir(base, nm)
            if pdir:
                ic = count_prompts(pdir)
            pc = count_pending(os.path.join(base, "发现", f"{nm}.md"))

            # 游离步骤已筛选为 2 天内活跃（days<=2），按注释意图必带 🔥；
            # 有提示词叠加 📄，有待确认叠加 ⚠N。
            parts = ["🔥"]
            if ic > 0:
                parts.append("📄")
            if pc > 0:
                parts.append(f"⚠ {pc}")
            sig = " ".join(parts)
            extra.append([nu, nm, "?", "今天", sig])

    if extra:
        print("")
        print("⚠ 以下步骤存在于步骤/目录但未被总纲表格涵盖：")
        print("\n".join(column_table(extra)))

    # ── 5. 输出图例 ───────────────────────────────────────────────────────
    print("")
    print("🔥 = 活跃 📄 = 有提示词 ⚠ N = N 项待确认 💀 = 脏(🔨 但超 2 日未改)")


if __name__ == "__main__":
    main()
