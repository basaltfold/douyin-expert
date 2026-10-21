#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# 抖音专家 (douyin-expert) — 海外技能脱钩检查
# Copyright (C) 2026 basaltfold
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
"""
CI 检查：海外三个技能必须已脱离付费转售 API（DATA_API_BASE）。

判定用 AST，而不是 grep —— 否则注释和文档字符串里的历史说明会造成误报，
而真正的 bad code 又可能被注释符掩护而漏报。

检查三类痕迹：
  1. 代码里出现 DATA_API_BASE 这个标识符（Name 节点，如 `f"{DATA_API_BASE}/x"`）
  2. 非 docstring 的字符串字面量里出现 {DATA_API_BASE} 占位符
  3. 非 docstring 的字符串字面量恰好等于 DATA_API_BASE
     （即 os.environ.get("DATA_API_BASE", ...) 这种环境变量名，是最常见的残留形态）

用法： python scripts/check_overseas_decoupled.py
退出码：0 = 干净；1 = 发现残留
"""

import ast
import sys
from pathlib import Path

# CI 的 Windows runner 上 Python 默认 stdout 是 cp1252，打印中文会 UnicodeEncodeError。
# 统一改成 UTF-8（Unix 上本身已是 UTF-8，reconfigure 无副作用）。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

ROOTS = [
    "assets/overseas-trending-search",
    "assets/twitter-work-search",
    "assets/youtube-digest",
]

#: 需要检查的目标标识符
TARGET = "DATA_API_BASE"

#: 允许存在的例外（文件名 -> 行号白名单，通常不需要）
ALLOWLIST: set = set()


def collect_docstrings(tree):
    """收集所有 docstring 常量节点的 id，AST walk 时用来排除。"""
    ids = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = getattr(node, "body", [])
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                ids.add(id(body[0].value))
    return ids


def scan_file(path):
    """返回该文件里的违规位置列表 [(line, reason)]。"""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source, str(path))
    except SyntaxError as exc:
        print(f"[错误] 语法解析失败 {path}: {exc}")
        return [(0, "syntax error")]

    docstrings = collect_docstrings(tree)
    problems = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == TARGET:
            problems.append((node.lineno, f"代码引用了 {TARGET} 标识符"))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            # docstring 里的历史说明不算
            if id(node) in docstrings:
                continue
            if "{" + TARGET + "}" in node.value:
                problems.append((node.lineno, f"字符串字面量含 {{{TARGET}}} 占位符"))
            elif node.value.strip() == TARGET:
                problems.append((node.lineno, f"字符串字面量就是环境变量名 {TARGET}"))

    return problems


def main():
    total_files = 0
    bad = []

    for root in ROOTS:
        root_path = Path(root)
        if not root_path.exists():
            print(f"[错误] 目录不存在: {root}")
            return 1
        for path in sorted(root_path.rglob("*.py")):
            total_files += 1
            for line, reason in scan_file(path):
                key = (str(path), line)
                if key in ALLOWLIST:
                    continue
                bad.append((str(path), line, reason))

    print(f"检查了 {total_files} 个海外技能脚本")

    if bad:
        print()
        for path, line, reason in bad:
            print(f"  [残留] {path}:{line} — {reason}")
        print()
        print("海外技能仍在用付费转售 API 的基址变量。这些技能应改成开源实现。")
        return 1

    print("海外技能已脱离付费 API")
    return 0


if __name__ == "__main__":
    sys.exit(main())
