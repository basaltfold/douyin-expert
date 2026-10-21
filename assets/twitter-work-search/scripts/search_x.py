#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
X(Twitter) 作品搜索 — 开源实现版
==================================

原版：POST {DATA_API_BASE}/x/search（需要用户自建付费转售 API）
本版：直接用 requests 抓 X 的公开搜索页面 / 官方 API v2

现实约束（2026-08 实测）：
  - X 官方 API v2 的免费额度极低，Basic 版 $100/月起
  - Nitter 公共实例 2026 年已全部关闭或反爬
  - snscrape 与 Python 3.12 不兼容（find_module 被移除）
  - 匿名访问 x.com/search 会返回登录墙

因此本实现对「无凭据」与「有凭据」两种情况分别处理：
  1. 有凭据（X_BEARER_TOKEN，或 X_AUTH_TOKEN + X_CT0）：稳定可用
  2. 无凭据：尝试匿名解析，失败时**明确报错并给出配置指引，绝不编造数据**

Usage:
    python search_x.py "AI agent"                          # 默认 Top
    python search_x.py "AI agent" --type Latest            # 最新
    python search_x.py "AI agent" --type Media --limit 10  # 只含媒体
    python search_x.py "AI" --json                         # 原始 JSON

环境变量（可选，有则更稳）：
    X_BEARER_TOKEN   X 官方 API v2 Bearer Token
    X_AUTH_TOKEN     X 登录态 auth_token cookie（配合 X_CT0）
    X_CT0            X 登录态 ct0 cookie
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

DEFAULT_OUTPUT_DIR = Path.home() / "Downloads" / "DouyinExpertXSearch"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
)

GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def info(msg):
    print(f"{GREEN}[OK]{RESET} {msg}")


def warn(msg):
    print(f"{YELLOW}[!]{RESET} {msg}")


def error(msg):
    print(f"{RED}[x]{RESET} {msg}")


def step(msg):
    print(f"{CYAN}[->]{RESET} {msg}")


def normalize_type(raw):
    """把口语/英文/中文都归一到 5 种规范类型。"""
    s = (raw or "").strip().lower()
    if not s:
        return "Top"
    mapping = {
        "top": "Top", "热门": "Top", "热度": "Top", "最火": "Top",
        "latest": "Latest", "最新": "Latest", "最近": "Latest", "新发布": "Latest",
        "media": "Media", "媒体": "Media", "图片": "Media", "视频": "Media", "照片": "Media",
        "people": "People", "用户": "People", "账号": "People", "找人": "People", "作者": "People",
        "lists": "Lists", "列表": "Lists",
    }
    return mapping.get(s, "Top")


def resolve_credentials():
    """
    返回 (mode, creds)：
      mode = 'api'  官方 API v2（有 Bearer）
      mode = 'web'  网页登录态（有 auth_token + ct0）
      mode = 'anon' 匿名抓取（两手空空）
    """
    if os.environ.get("X_BEARER_TOKEN", "").strip():
        return "api", {"bearer": os.environ["X_BEARER_TOKEN"].strip()}
    auth_token = os.environ.get("X_AUTH_TOKEN", "").strip()
    ct0 = os.environ.get("X_CT0", "").strip()
    if auth_token and ct0:
        return "web", {"auth_token": auth_token, "ct0": ct0}
    return "anon", {}


def make_session(creds):
    s = requests.Session()
    s.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
    })
    if creds.get("bearer"):
        s.headers["Authorization"] = f"Bearer {creds['bearer']}"
    if creds.get("auth_token"):
        s.cookies.set("auth_token", creds["auth_token"], domain=".x.com")
        s.cookies.set("ct0", creds["ct0"], domain=".x.com")
        s.headers.update({
            "x-csrf-token": creds["ct0"],
            "Referer": "https://x.com/",
            "Origin": "https://x.com",
            "x-twitter-active-user": "yes",
            "x-twitter-client-language": "en",
        })
    return s


def normalize_item(tw, user):
    """把 API v2 / GraphQL 的推文结构统一成一种 schema。"""
    tid = tw.get("id_str") or str(tw.get("id") or "")
    text = (tw.get("full_text") or tw.get("text") or "").strip()
    username = user.get("screen_name") or user.get("username") or ""
    medias = []
    for ext in (tw.get("extended_entities") or {}).get("media", []) or []:
        variants = (ext.get("video_info") or {}).get("variants") or []
        video_url = variants[-1].get("url", "") if variants else ""
        medias.append({
            "type": ext.get("type", ""),
            "cover_url": ext.get("media_url_https", ""),
            "video_url": video_url,
        })
    return {
        "id": tid,
        "text": text,
        "url": f"https://x.com/{username}/status/{tid}" if username else f"https://x.com/i/status/{tid}",
        "created_at": tw.get("created_at", ""),
        "language": tw.get("lang", ""),
        "likes": int(tw.get("favorite_count") or 0),
        "retweets": int(tw.get("retweet_count") or 0),
        "replies": int(tw.get("reply_count") or 0),
        "quotes": int(tw.get("quote_count") or 0),
        "views": int(tw.get("views_count") or 0),
        "author": {
            "name": user.get("name") or "",
            "username": username,
            "followers": int(user.get("followers_count") or 0),
            "verified": bool(user.get("verified") or user.get("is_blue_verified")),
            "location": user.get("location") or "",
        },
        "media": medias,
    }


def search_api_v2(session, keyword, search_type, limit):
    """GET https://api.twitter.com/2/search/adaptive.json（需要有效 Bearer）。"""
    params = {
        "q": keyword,
        "count": str(min(limit, 100)),
        "tweet_search_mode": "live" if search_type == "Latest" else "top",
        "include_entities": "true",
        "tweet_mode": "extended",
    }
    try:
        r = session.get("https://api.twitter.com/2/search/adaptive.json", params=params, timeout=30)
    except Exception as exc:  # noqa: BLE001
        return None, f"网络异常: {exc}"

    if r.status_code in (401, 403):
        return None, f"Bearer Token 无效或无权限 (HTTP {r.status_code})"
    if r.status_code == 429:
        return None, "触发官方 API 限流 (429)，请等待 15 分钟后重试"
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}: {r.text[:200]}"

    try:
        payload = r.json()
    except Exception:
        return None, "响应不是 JSON"

    tweets = (payload.get("globalObjects") or {}).get("tweets") or {}
    users = (payload.get("globalObjects") or {}).get("users") or {}

    items = []
    for _tid, tw in tweets.items():
        user = users.get(str(tw.get("user_id_str")), {})
        items.append(normalize_item(tw, user))
    items.sort(key=lambda x: x["likes"], reverse=True)
    return items[:limit], None


def search_web(session, keyword, search_type, limit):
    """有 auth_token + ct0 时调 x.com 的 GraphQL SearchTimeline。"""
    query_id = "M1jEez78PEfVfbQLvlWMvx5r5hE"
    variables = {
        "rawQuery": keyword,
        "count": min(limit, 20),
        "querySource": "typed_query",
        "product": "Latest" if search_type == "Latest" else "Top",
    }
    url = f"https://x.com/i/api/graphql/{query_id}/SearchTimeline"
    params = {
        "variables": json.dumps(variables, separators=(",", ":")),
        "features": json.dumps({
            "rweb_video_screen_enabled": False,
            "profile_label_improvements_pcf_label_in_post_enabled": True,
        }, separators=(",", ":")),
    }
    try:
        r = session.get(url, params=params, timeout=30)
    except Exception as exc:  # noqa: BLE001
        return None, f"网络异常: {exc}"

    if r.status_code in (401, 403):
        return None, f"登录态失效 (HTTP {r.status_code})，请更新 X_AUTH_TOKEN / X_CT0"
    if r.status_code == 429:
        return None, "触发限流 (429)，请稍后重试"
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}: {r.text[:200]}"

    try:
        payload = r.json()
    except Exception:
        return None, "响应不是 JSON"

    items = []
    instructions = (
        payload.get("data", {})
        .get("search_by_raw_query", {})
        .get("search_timeline", {})
        .get("timeline", {})
        .get("instructions", [])
    )
    for inst in instructions:
        for entry in inst.get("entries", []) or []:
            result = (
                (entry.get("content", {}) or {})
                .get("itemContent", {})
                .get("tweet_results", {})
                .get("result", {})
            )
            legacy = result.get("legacy") or (result.get("tweet", {}) or {}).get("legacy")
            if not legacy:
                continue
            user = (
                ((result.get("core") or {}).get("user_results") or {})
                .get("result", {})
                .get("legacy", {})
                or {}
            )
            items.append(normalize_item(legacy, user))

    items.sort(key=lambda x: x["likes"], reverse=True)
    return items[:limit], None


def search_anon(session, keyword, search_type, limit):
    """无凭据时抓 x.com/search 的 HTML，尽力解析；拿到登录墙就明确报错。"""
    params = {"q": keyword, "src": "typed_query"}
    if search_type == "Latest":
        params["f"] = "live"
    elif search_type == "Media":
        params["f"] = "media"

    try:
        r = session.get("https://x.com/search", params=params, timeout=30, allow_redirects=True)
    except Exception as exc:  # noqa: BLE001
        return None, f"网络异常: {exc}"

    if r.status_code in (401, 403):
        return None, (
            "X 对未登录访问返回 "
            f"{r.status_code}。请配置 X_BEARER_TOKEN（官方 API）"
            "或 X_AUTH_TOKEN + X_CT0（浏览器登录态）后重试。"
        )
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}"

    html = r.text
    if "Log in" in html or "login" in html[:5000].lower():
        return None, (
            "X 返回了登录墙（未登录无法搜索）。"
            "请配置 X_BEARER_TOKEN 或 X_AUTH_TOKEN + X_CT0 后重试。"
        )

    items = []
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if m:
        try:
            data = json.loads(m.group(1))
            entries = (
                ((data.get("props") or {}).get("pageProps") or {})
                .get("timeline", {})
                .get("entries", [])
            )
            for e in entries:
                tw = (e.get("content") or {}).get("tweet") or {}
                if not tw:
                    continue
                items.append({
                    "id": tw.get("id_str", ""),
                    "text": (tw.get("full_text") or tw.get("text") or "").strip(),
                    "url": f"https://x.com/i/status/{tw.get('id_str', '')}",
                    "created_at": tw.get("created_at", ""),
                    "language": tw.get("lang", ""),
                    "likes": int(tw.get("favorite_count") or 0),
                    "retweets": int(tw.get("retweet_count") or 0),
                    "replies": int(tw.get("reply_count") or 0),
                    "quotes": int(tw.get("quote_count") or 0),
                    "views": int(tw.get("views_count") or 0),
                    "author": {
                        "name": (tw.get("user") or {}).get("name", ""),
                        "username": (tw.get("user") or {}).get("screen_name", ""),
                        "followers": int((tw.get("user") or {}).get("followers_count") or 0),
                        "verified": bool((tw.get("user") or {}).get("verified")),
                    },
                    "media": [],
                })
        except Exception:
            pass

    if not items:
        return None, (
            "未能从 X 页面解析出任何推文。X 对未登录抓取限制极严，"
            "请配置 X_BEARER_TOKEN 或 X_AUTH_TOKEN + X_CT0 后重试。"
        )
    return items[:limit], None


def fmt_num(n):
    try:
        n = int(n)
    except (ValueError, TypeError):
        return "0"
    if n >= 100_000_000:
        return f"{n / 100_000_000:.1f}亿"
    if n >= 10_000:
        return f"{n / 10_000:.1f}万"
    return str(n)


def print_table(items):
    print(f"\n{DIM}{'-' * 78}{RESET}")
    for i, it in enumerate(items, 1):
        author = it["author"]
        verified = " [认证]" if author.get("verified") else ""
        text = it["text"].replace("\n", " ")
        if len(text) > 80:
            text = text[:80] + "..."
        media_tag = ""
        if it["media"]:
            types = {m["type"] for m in it["media"]}
            if "video" in types or "animated_gif" in types:
                media_tag += " [视频]"
            if "photo" in types:
                media_tag += " [图片]"
        print(f"[{i}] @{author.get('username', '?')} ({author.get('name', '')}){verified} · {author.get('followers', 0)} 粉丝")
        print(f"    {text}{media_tag}")
        print(
            f"    点赞 {fmt_num(it['likes'])} · 转发 {fmt_num(it['retweets'])} · "
            f"回复 {fmt_num(it['replies'])} · 引用 {fmt_num(it['quotes'])}"
        )
        print(f"    {it['created_at']} · {it['url']}")
        print()
    print(f"{DIM}{'-' * 78}{RESET}")


def build_markdown(items, keyword, search_type, mode):
    md = [f"# X(Twitter) 搜索结果：{keyword}", ""]
    md.append(f"- 搜索类型：{search_type}")
    md.append(f"- 结果数：{len(items)}")
    md.append(f"- 抓取时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    mode_label = {"api": "官方 API v2", "web": "网页登录态", "anon": "匿名抓取"}.get(mode, mode)
    md.append(f"- 数据来源：{mode_label}（开源实现）")
    md.append("")
    md.append("| # | 作者 | 正文 | 点赞 | 转发 | 时间 | 链接 |")
    md.append("|---|------|------|------|------|------|------|")
    for i, it in enumerate(items, 1):
        text = it["text"].replace("\n", " ").replace("|", "\\|")
        if len(text) > 100:
            text = text[:100] + "..."
        md.append(
            f"| {i} | @{it['author'].get('username', '?')} | {text} | "
            f"{it['likes']} | {it['retweets']} | {it['created_at']} | [打开]({it['url']}) |"
        )
    md.append("")
    return "\n".join(md)


def main():
    parser = argparse.ArgumentParser(description="X(Twitter) 作品搜索 — 开源实现版")
    parser.add_argument("keyword", help="搜索关键词")
    parser.add_argument("--type", default="Top",
                        help="搜索类型：Top / Latest / Media / People / Lists（默认 Top）")
    parser.add_argument("--limit", type=int, default=20, help="返回条数（默认 20）")
    parser.add_argument("--json", action="store_true", help="输出原始 JSON")
    parser.add_argument("--no-save", action="store_true", help="不保存 Markdown")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="输出目录")
    args = parser.parse_args()

    if not HAS_REQUESTS:
        error("缺少 requests，请先执行：python -m pip install requests")
        sys.exit(1)

    keyword = args.keyword.strip()
    if not keyword:
        error("关键词不能为空")
        sys.exit(1)

    search_type = normalize_type(args.type)
    mode, creds = resolve_credentials()
    session = make_session(creds)

    mode_names = {
        "api": "官方 API v2（X_BEARER_TOKEN）",
        "web": "网页登录态（X_AUTH_TOKEN + X_CT0）",
        "anon": "匿名抓取（无凭据）",
    }
    step(f"搜索「{keyword}」· 类型 {search_type} · 模式 {mode_names[mode]}")

    if mode == "api":
        items, err = search_api_v2(session, keyword, search_type, args.limit)
    elif mode == "web":
        items, err = search_web(session, keyword, search_type, args.limit)
    else:
        items, err = search_anon(session, keyword, search_type, args.limit)

    if err:
        error(err)
        if mode == "anon":
            print()
            print("配置方式（任选一种）：")
            print("  1. 官方 API（稳定）: set X_BEARER_TOKEN=你的BearerToken")
            print("  2. 浏览器登录态     : set X_AUTH_TOKEN=... & set X_CT0=...")
            print("     获取方式：浏览器登录 x.com → F12 → Application → Cookies →")
            print("     复制 auth_token 和 ct0 两个值")
        sys.exit(1)

    if not items:
        warn("搜索成功但未返回任何结果（关键词可能过于罕见，或该类型下无内容）")
        sys.exit(0)

    info(f"找到 {len(items)} 条结果")

    if args.json:
        print(json.dumps(items, ensure_ascii=False, indent=2))
    else:
        print_table(items)

    if not args.no_save:
        out_dir = Path(args.output_dir).expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_kw = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", keyword)[:30]
        fpath = out_dir / f"x_{safe_kw}_{search_type}_{stamp}.md"
        fpath.write_text(build_markdown(items, keyword, search_type, mode), encoding="utf-8")
        info(f"结果已保存：{fpath}")


if __name__ == "__main__":
    main()
