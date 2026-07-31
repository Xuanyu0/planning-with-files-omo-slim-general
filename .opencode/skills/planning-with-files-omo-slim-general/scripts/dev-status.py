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
    BASE/提示词/{编号}-*/    — 提示词目录，内含 .md 提示词文件
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

# ── 显示宽度表 ─────────────────────────────────────────────────────────────────
# 与 glibc wcwidth（Markus Kuhn 表）对齐，用于列对齐。
# 宽字符（显示宽度 2）：
_WIDE_RANGES = [
    (0x1100, 0x115F), (0x2329, 0x232A), (0x2E80, 0x303E),
    (0x3041, 0x33FF), (0x3400, 0x4DBF), (0x4E00, 0x9FFF),
    (0xA000, 0xA4CF), (0xA960, 0xA97F), (0xAC00, 0xD7A3),
    (0xF900, 0xFAFF), (0xFE10, 0xFE19), (0xFE30, 0xFE6F),
    (0xFF00, 0xFF60), (0xFFE0, 0xFFE6), (0x1F300, 0x1F64F),
    (0x1F900, 0x1F9FF), (0x20000, 0x3FFFD),
]
# 零宽字符（组合字符等）：
_ZERO_RANGES = [
    (0x0300, 0x036F), (0x0483, 0x0489), (0x0591, 0x05BD),
    (0x05BF, 0x05BF), (0x05C1, 0x05C2), (0x05C4, 0x05C5),
    (0x0610, 0x061A), (0x064B, 0x065F), (0x0670, 0x0670),
    (0x06D6, 0x06DC), (0x06DF, 0x06E4), (0x06E7, 0x06E8),
    (0x06EA, 0x06ED), (0x0711, 0x0711), (0x0730, 0x074A),
    (0x07A6, 0x07B0), (0x07EB, 0x07F3), (0x0816, 0x0819),
    (0x081B, 0x0823), (0x0825, 0x0827), (0x0829, 0x082D),
    (0x0859, 0x085B), (0x08E3, 0x0902), (0x093A, 0x093A),
    (0x093C, 0x093C), (0x0941, 0x0948), (0x094D, 0x094D),
    (0x0951, 0x0957), (0x0962, 0x0963), (0x0981, 0x0981),
    (0x09BC, 0x09BC), (0x09C1, 0x09C4), (0x09CD, 0x09CD),
    (0x0A01, 0x0A02), (0x0A3C, 0x0A3C), (0x0A41, 0x0A42),
    (0x0A47, 0x0A48), (0x0A4B, 0x0A4D), (0x0A70, 0x0A71),
    (0x0A81, 0x0A82), (0x0ABC, 0x0ABC), (0x0AC1, 0x0AC5),
    (0x0AC7, 0x0AC8), (0x0ACD, 0x0ACD), (0x0B01, 0x0B01),
    (0x0B3C, 0x0B3C), (0x0B3F, 0x0B3F), (0x0B41, 0x0B44),
    (0x0B4D, 0x0B4D), (0x0B56, 0x0B56), (0x0B82, 0x0B82),
    (0x0BC0, 0x0BC0), (0x0BCD, 0x0BCD), (0x0C00, 0x0C00),
    (0x0C3E, 0x0C40), (0x0C46, 0x0C48), (0x0C4A, 0x0C4D),
    (0x0C55, 0x0C56), (0x0CBC, 0x0CBC), (0x0CBF, 0x0CBF),
    (0x0CC6, 0x0CC6), (0x0CCC, 0x0CCD), (0x0D41, 0x0D44),
    (0x0D4D, 0x0D4D), (0x0DCA, 0x0DCA), (0x0DD2, 0x0DD4),
    (0x0DD6, 0x0DD6), (0x0E31, 0x0E31), (0x0E34, 0x0E3A),
    (0x0E47, 0x0E4E), (0x0EB1, 0x0EB1), (0x0EB4, 0x0EB9),
    (0x0EBB, 0x0EBC), (0x0EC8, 0x0ECD), (0x0F18, 0x0F19),
    (0x0F35, 0x0F35), (0x0F37, 0x0F37), (0x0F39, 0x0F39),
    (0x0F71, 0x0F7E), (0x0F80, 0x0F84), (0x0F86, 0x0F87),
    (0x0F8D, 0x0F97), (0x0F99, 0x0FBC), (0x0FC6, 0x0FC6),
    (0x102D, 0x1030), (0x1032, 0x1037), (0x1039, 0x103A),
    (0x103D, 0x103E), (0x1058, 0x1059), (0x105E, 0x1060),
    (0x1071, 0x1074), (0x1082, 0x1082), (0x1085, 0x1086),
    (0x108D, 0x108D), (0x109D, 0x109D), (0x135D, 0x135F),
    (0x1712, 0x1714), (0x1732, 0x1734), (0x1752, 0x1753),
    (0x1772, 0x1773), (0x17B4, 0x17B5), (0x17B7, 0x17BD),
    (0x17C6, 0x17C6), (0x17C9, 0x17D3), (0x17DD, 0x17DD),
    (0x180B, 0x180D), (0x18A9, 0x18A9), (0x1920, 0x1922),
    (0x1927, 0x1928), (0x1932, 0x1932), (0x1939, 0x193B),
    (0x1A17, 0x1A18), (0x1A1B, 0x1A1B), (0x1A56, 0x1A56),
    (0x1A58, 0x1A5E), (0x1A60, 0x1A60), (0x1A62, 0x1A62),
    (0x1A65, 0x1A6C), (0x1A73, 0x1A7C), (0x1A7F, 0x1A7F),
    (0x1AB0, 0x1ABE), (0x1B00, 0x1B03), (0x1B34, 0x1B34),
    (0x1B36, 0x1B3A), (0x1B3C, 0x1B3C), (0x1B42, 0x1B42),
    (0x1B6B, 0x1B73), (0x1B80, 0x1B81), (0x1BA2, 0x1BA5),
    (0x1BA8, 0x1BA9), (0x1BAB, 0x1BAD), (0x1BE6, 0x1BE6),
    (0x1BE8, 0x1BE9), (0x1BED, 0x1BED), (0x1BEF, 0x1BF1),
    (0x1C2C, 0x1C33), (0x1C36, 0x1C37), (0x1CD0, 0x1CD2),
    (0x1CD4, 0x1CE0), (0x1CE2, 0x1CE8), (0x1CED, 0x1CED),
    (0x1CF4, 0x1CF4), (0x1CF8, 0x1CF9), (0x1DC0, 0x1DF5),
    (0x1DFC, 0x1DFF), (0x20D0, 0x20F0), (0x2CEF, 0x2CF1),
    (0x2D7F, 0x2D7F), (0x2DE0, 0x2DFF), (0x302A, 0x302D),
    (0x3099, 0x309A), (0xA66F, 0xA672), (0xA674, 0xA67D),
    (0xA69E, 0xA69F), (0xA6F0, 0xA6F1), (0xA802, 0xA802),
    (0xA806, 0xA806), (0xA80B, 0xA80B), (0xA825, 0xA826),
    (0xA8C4, 0xA8C5), (0xA8E0, 0xA8F1), (0xA926, 0xA92D),
    (0xA947, 0xA951), (0xA980, 0xA982), (0xA9B3, 0xA9B3),
    (0xA9B6, 0xA9B9), (0xA9BC, 0xA9BC), (0xA9E5, 0xA9E5),
    (0xAA29, 0xAA2E), (0xAA31, 0xAA32), (0xAA35, 0xAA36),
    (0xAA43, 0xAA43), (0xAA4C, 0xAA4C), (0xAA7C, 0xAA7C),
    (0xAAB0, 0xAAB0), (0xAAB2, 0xAAB4), (0xAAB7, 0xAAB8),
    (0xAABE, 0xAABF), (0xAAC1, 0xAAC1), (0xAAEC, 0xAAED),
    (0xAAF6, 0xAAF6), (0xABE5, 0xABE5), (0xABE8, 0xABE8),
    (0xABED, 0xABED), (0xFB1E, 0xFB1E), (0xFE00, 0xFE0F),
    (0xFE20, 0xFE2F), (0xFEFF, 0xFEFF), (0xFFF9, 0xFFFB),
    (0x101FD, 0x101FD), (0x102E0, 0x102E0), (0x10376, 0x1037A),
    (0x10A01, 0x10A03), (0x10A05, 0x10A06), (0x10A0C, 0x10A0F),
    (0x10A38, 0x10A3A), (0x10A3F, 0x10A3F), (0x10AE5, 0x10AE6),
    (0x11001, 0x11001), (0x11038, 0x11046), (0x1107F, 0x11081),
    (0x110B3, 0x110B6), (0x110B9, 0x110BA), (0x11100, 0x11102),
    (0x11127, 0x1112B), (0x1112D, 0x11134), (0x11173, 0x11173),
    (0x11180, 0x11181), (0x111B6, 0x111BE), (0x111CA, 0x111CC),
    (0x1122F, 0x11231), (0x11234, 0x11234), (0x11236, 0x11237),
    (0x112DF, 0x112DF), (0x112E3, 0x112EA), (0x11300, 0x11301),
    (0x1133C, 0x1133C), (0x11340, 0x11340), (0x11366, 0x1136C),
    (0x11370, 0x11374), (0x11438, 0x1143F), (0x11442, 0x11444),
    (0x11446, 0x11446), (0x114B3, 0x114B8), (0x114BA, 0x114BA),
    (0x114BF, 0x114C0), (0x114C2, 0x114C3), (0x115B2, 0x115B5),
    (0x115BC, 0x115BD), (0x115BF, 0x115C0), (0x115DC, 0x115DD),
    (0x11633, 0x1163A), (0x1163D, 0x1163D), (0x1163F, 0x11640),
    (0x116AB, 0x116AB), (0x116AD, 0x116AD), (0x116B0, 0x116B5),
    (0x116B7, 0x116B7), (0x1171D, 0x1171F), (0x11722, 0x11725),
    (0x11727, 0x1172B), (0x16AF0, 0x16AF4), (0x16B30, 0x16B36),
    (0x16F8F, 0x16F92), (0x1BC9D, 0x1BC9E), (0x1BCA0, 0x1BCA3),
    (0x1D167, 0x1D169), (0x1D173, 0x1D182), (0x1D185, 0x1D18B),
    (0x1D1AA, 0x1D1AD), (0x1D242, 0x1D244), (0x1DA00, 0x1DA36),
    (0x1DA3B, 0x1DA6C), (0x1DA75, 0x1DA75), (0x1DA84, 0x1DA84),
    (0x1DA9B, 0x1DA9F), (0x1DAA1, 0x1DAAF), (0x1E000, 0x1E006),
    (0x1E008, 0x1E018), (0x1E01B, 0x1E021), (0x1E023, 0x1E024),
    (0x1E026, 0x1E02A), (0x1E8D0, 0x1E8D6), (0x1E944, 0x1E94A),
    (0xE0001, 0xE0001), (0xE0020, 0xE007F), (0xE0100, 0xE01EF),
]


def display_width(s: str) -> int:
    """返回字符串的显示宽度（glibc wcwidth 语义，emoji 按宽处理）。"""
    w = 0
    for ch in s:
        cp = ord(ch)
        if any(lo <= cp <= hi for lo, hi in _ZERO_RANGES):
            continue
        if any(lo <= cp <= hi for lo, hi in _WIDE_RANGES):
            w += 2
        else:
            w += 1
    return w


def column_table(rows, sep="  "):
    """按列对齐输出，模拟 column -t -s '|' -o sep 的行为。

    字段首尾空白会被去掉（与 column 默认行为一致），最后一列不补空格。
    """
    if not rows:
        return ""
    rows = [[f.strip() for f in r] for r in rows]
    ncols = max(len(r) for r in rows)
    widths = []
    for i in range(ncols):
        widths.append(max(display_width(r[i]) if i < len(r) else 0 for r in rows))
    out = []
    for r in rows:
        cells = []
        for i in range(ncols):
            cell = r[i] if i < len(r) else ""
            if i < ncols - 1:
                cell = cell + " " * max(0, widths[i] - display_width(cell))
            cells.append(cell)
        out.append(sep.join(cells))
    return "\n".join(out)


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


def find_prompt_dir(base, prefix):
    """返回 提示词 下第一个名字以 prefix 开头的目录（对应 find ... | head -1）。"""
    pdir = os.path.join(base, "提示词")
    if not os.path.isdir(pdir):
        return None
    try:
        for e in os.scandir(pdir):
            if e.is_dir() and e.name.startswith(prefix):
                return e.path
    except OSError:
        pass
    return None


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
        # sed 's/.*(//;s/).*//'：最后一个 ( 之后、第一个 ) 之前的内容
        file_md = fields[2] if len(fields) > 2 else ""
        file = file_md.rsplit("(", 1)[-1].split(")", 1)[0]
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

        # 2b. 提示词文件数量
        ic = 0
        pdir = find_prompt_dir(base, num + "-")
        if pdir:
            ic = count_prompts(pdir)

        # 2c. 发现文档待确认项
        pc = count_pending(os.path.join(base, "发现", file))

        # 2d. 信号列（拼接顺序与 bash 版一致）
        sig = ""
        if ic > 0:
            sig = "📄 "
        if pc > 0:
            sig = f" {sig}⚠ {pc}"
        if st == "🔨" and days > 2:
            sig = f" {sig} 💀 "
        if days <= 2 and ic > 0:
            sig = f" {sig} 🔥 "

        data_rows.append([num, file_disp, st, ds, sig])

    # ── 3. 输出主表格 ─────────────────────────────────────────────────────
    print("编号  文件                状态  距今    信号")
    print("────  ──────────────────  ────  ──────  ────────")
    if data_rows:
        print(column_table(data_rows))

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
            pdir = find_prompt_dir(base, nu + "-")
            if pdir:
                ic = count_prompts(pdir)
            pc = count_pending(os.path.join(base, "发现", f"{nm}.md"))

            # 游离步骤必为最近活跃（days<=2），有提示词则标 📄，有待确认叠加 ⚠+🔥
            sig = ""
            if ic > 0:
                sig = " 📄 "
            if pc > 0:
                sig = f"{sig} ⚠ {pc} 🔥"
            extra.append([nu, nm, "?", "今天", sig])

    if extra:
        print("")
        print("⚠ 以下步骤存在于步骤/目录但未被总纲表格涵盖：")
        print(column_table(extra))

    # ── 5. 输出图例 ───────────────────────────────────────────────────────
    print("")
    print("🔥 = 活跃 📄 = 有提示词 ⚠ N = N 项待确认 💀 = 脏(🔨 但超 2 日未改)")


if __name__ == "__main__":
    main()
