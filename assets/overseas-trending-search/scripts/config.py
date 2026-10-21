#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
overseas-trending-search — 统一配置（开源实现版）
==================================================

与原版的差异：
  - 原版：BASE_URL = DATA_API_BASE，所有平台走付费转售 API，需要 DATA_API_KEY
  - 本版：三个平台各自走开源实现（yt-dlp / X API v2），**不需要 DATA_API_KEY / DATA_API_BASE**

凭据（全部可选，不配也能跑，只是 X 平台会跳过）：
  X_BEARER_TOKEN    X 官方 API v2 Bearer Token（推荐）
  X_AUTH_TOKEN      X 浏览器 cookie auth_token
  X_CT0             X 浏览器 cookie ct0
"""

import json
import os
from pathlib import Path

# ─── 输出目录 ─────────────────────────────────────────────────────────────────────
DEFAULT_OUTPUT_DIR = Path.home() / "Downloads" / "DouyinExpertOverseasTrending"

# ─── 兼容常量（主流程仍引用，但开源实现下不再使用）──────────────────────────────────
BASE_URL = ""            # 已废弃：不再有统一网关
SUCCESS_CODES = (200, 2000)  # 已废弃：开源实现用 HTTP 状态码判断
ENV_KEY = "DATA_API_KEY"     # 已废弃

#: 各平台的凭据需求说明（打印给用户看）
CREDENTIAL_NOTES = {
    "youtube": "yt-dlp 直连，无需凭据",
    "tiktok": "yt-dlp 直连，无需凭据（仅支持视频链接 / 用户主页，不支持关键词搜索）",
    "x": "需要 X_BEARER_TOKEN 或 X_AUTH_TOKEN + X_CT0（X 已关闭未登录搜索）",
}


def get_api_key(cli_key=None):
    """
    保留函数签名以兼容主流程，但开源实现下始终返回占位值。
    主流程不再因缺少 Key 而退出。
    """
    return cli_key or "__no_key_required__"


def make_session(api_key):
    """
    构造一个通用 requests.Session（不带任何网关认证头）。
    各平台的适配器自己决定要不要额外凭据。
    """
    import requests
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
    })
    return session


def print_no_key_guide():
    """开源实现下不再是错误，改成「凭据说明」。"""
    print("┌──────────────────────────────────────────────────────────┐")
    print("│  本技能走开源实现，不需要 DATA_API_KEY / DATA_API_BASE   │")
    print("├──────────────────────────────────────────────────────────┤")
    print("│  YouTube : yt-dlp 直连，免凭据                            │")
    print("│  TikTok  : yt-dlp 直连，免凭据（仅链接/主页）             │")
    print("│  X       : 需 X_BEARER_TOKEN 或 X_AUTH_TOKEN + X_CT0      │")
    print("│            （X 已关闭未登录搜索，这是平台限制）           │")
    print("└──────────────────────────────────────────────────────────┘")


def x_available():
    """X 平台当前是否具备凭据。"""
    if (os.environ.get("X_BEARER_TOKEN") or "").strip():
        return True
    return bool(
        (os.environ.get("X_AUTH_TOKEN") or "").strip()
        and (os.environ.get("X_CT0") or "").strip()
    )


def x_config_guide():
    """X 平台的配置指引（用户问「怎么让 X 也能用」时打印）。"""
    return (
        "X 平台配置方式（任选一种）：\n"
        "  1. 官方 API v2（稳定，需付费额度）:\n"
        "     set X_BEARER_TOKEN=你的BearerToken\n"
        "  2. 浏览器登录态（免费，但可能随时失效）:\n"
        "     浏览器登录 x.com → F12 → Application → Cookies\n"
        "     复制 auth_token 与 ct0，然后:\n"
        "     set X_AUTH_TOKEN=...\n"
        "     set X_CT0=..."
    )


if __name__ == "__main__":
    print_no_key_guide()
    print()
    print("X 当前可用:", x_available())
