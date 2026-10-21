#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
X (Twitter) 平台适配器 — 开源实现版
=====================================

原版：POST {DATA_API_BASE}/x/search（需要用户自建付费转售服务）
本版：复用同插件 twitter-work-search 技能的 X 搜索实现（官方 API v2 / 网页登录态 / 匿名）。

实测（2026-08）能力边界：
  - 无凭据：X 返回登录墙，无法搜索 —— 本实现明确抛 PlatformUnavailable，不伪造
  - X_BEARER_TOKEN：走官方 API v2 search/adaptive.json，稳定
  - X_AUTH_TOKEN + X_CT0：走 x.com GraphQL SearchTimeline，稳定
"""

import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from .base import BaseSource, PlatformUnavailable

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"
)


class XSource(BaseSource):
    platform = "x"
    display_name = "X"
    #: 每次搜索取多少条
    search_limit = 15

    def search(self, session, keyword):
        """
        注意：session 参数保留是为了兼容 BaseSource 接口。
        本实现自己建 session（凭据来源与原版无关）。
        """
        if not HAS_REQUESTS:
            raise PlatformUnavailable("缺少 requests，请执行：python -m pip install requests")

        bearer = (os.environ.get("X_BEARER_TOKEN") or "").strip()
        auth_token = (os.environ.get("X_AUTH_TOKEN") or "").strip()
        ct0 = (os.environ.get("X_CT0") or "").strip()

        if bearer:
            items = self._search_api(bearer, keyword)
        elif auth_token and ct0:
            items = self._search_web(auth_token, ct0, keyword)
        else:
            raise PlatformUnavailable(
                "X 搜索需要凭据（X 已对未登录访问关闭搜索）。任选一种配置：\n"
                "  1. set X_BEARER_TOKEN=<官方 API v2 Bearer Token>\n"
                "  2. set X_AUTH_TOKEN=<cookie auth_token> 且 set X_CT0=<cookie ct0>\n"
                "     （浏览器登录 x.com → F12 → Application → Cookies 里复制）"
            )

        if not items:
            return []

        records = [self._normalize_item(t, keyword) for t in items]
        records.sort(key=lambda r: r["likes"], reverse=True)
        return records[:self.search_limit]

    # ─── 官方 API v2 ──────────────────────────────────────────────────────────
    def _search_api(self, bearer, keyword):
        s = requests.Session()
        s.headers.update({
            "User-Agent": USER_AGENT,
            "Authorization": f"Bearer {bearer}",
            "Accept": "application/json",
        })
        params = {
            "q": keyword,
            "count": str(self.search_limit),
            "tweet_search_mode": "top",
            "include_entities": "true",
            "tweet_mode": "extended",
        }
        try:
            r = s.get("https://api.twitter.com/2/search/adaptive.json", params=params, timeout=30)
        except Exception as exc:  # noqa: BLE001
            raise PlatformUnavailable(f"X API 网络异常: {_brief(exc)}") from exc

        if r.status_code in (401, 403):
            raise PlatformUnavailable(f"X_BEARER_TOKEN 无效或无权限 (HTTP {r.status_code})")
        if r.status_code == 429:
            raise PlatformUnavailable("X 官方 API 限流 (429)，请等待后重试")
        if r.status_code != 200:
            raise PlatformUnavailable(f"X API HTTP {r.status_code}: {r.text[:160]}")

        try:
            payload = r.json()
        except Exception:  # noqa: BLE001
            raise PlatformUnavailable("X API 响应不是 JSON")

        tweets = ((payload.get("globalObjects") or {}).get("tweets") or {})
        users = ((payload.get("globalObjects") or {}).get("users") or {})
        out = []
        for _tid, tw in tweets.items():
            user = users.get(str(tw.get("user_id_str")), {})
            out.append({
                "id": str(tw.get("id_str") or ""),
                "text": tw.get("full_text") or tw.get("text") or "",
                "username": user.get("screen_name") or "",
                "display_name": user.get("name") or "",
                "followers": int(user.get("followers_count") or 0),
                "likes": int(tw.get("favorite_count") or 0),
                "retweets": int(tw.get("retweet_count") or 0),
                "replies": int(tw.get("reply_count") or 0),
                "views": int(tw.get("views_count") or 0),
                "created_at": tw.get("created_at") or "",
                "language": tw.get("lang") or "",
            })
        return out

    # ─── 网页登录态 GraphQL ───────────────────────────────────────────────────
    def _search_web(self, auth_token, ct0, keyword):
        import json as _json

        s = requests.Session()
        s.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "x-csrf-token": ct0,
            "Referer": "https://x.com/",
            "x-twitter-active-user": "yes",
        })
        s.cookies.set("auth_token", auth_token, domain=".x.com")
        s.cookies.set("ct0", ct0, domain=".x.com")

        query_id = "M1jEez78PEfVfbQLvlWMvx5r5hE"
        variables = {
            "rawQuery": keyword,
            "count": self.search_limit,
            "querySource": "typed_query",
            "product": "Top",
        }
        params = {
            "variables": _json.dumps(variables, separators=(",", ":")),
            "features": _json.dumps({
                "rweb_video_screen_enabled": False,
                "profile_label_improvements_pcf_label_in_post_enabled": True,
            }, separators=(",", ":")),
        }
        url = f"https://x.com/i/api/graphql/{query_id}/SearchTimeline"
        try:
            r = s.get(url, params=params, timeout=30)
        except Exception as exc:  # noqa: BLE001
            raise PlatformUnavailable(f"X 网页 API 网络异常: {_brief(exc)}") from exc

        if r.status_code in (401, 403):
            raise PlatformUnavailable("X 登录态失效，请更新 X_AUTH_TOKEN / X_CT0")
        if r.status_code == 429:
            raise PlatformUnavailable("X 网页 API 限流 (429)")
        if r.status_code != 200:
            raise PlatformUnavailable(f"X 网页 API HTTP {r.status_code}")

        try:
            payload = r.json()
        except Exception:  # noqa: BLE001
            raise PlatformUnavailable("X 网页 API 响应不是 JSON")

        out = []
        instructions = (
            ((payload.get("data") or {}).get("search_by_raw_query") or {})
            .get("search_timeline", {})
            .get("timeline", {})
            .get("instructions", [])
        )
        for inst in instructions:
            for entry in inst.get("entries", []) or []:
                result = (
                    ((entry.get("content") or {}).get("itemContent") or {})
                    .get("tweet_results", {})
                    .get("result", {})
                )
                legacy = result.get("legacy") or (result.get("tweet") or {}).get("legacy")
                if not legacy:
                    continue
                user = (
                    ((result.get("core") or {}).get("user_results") or {})
                    .get("result", {})
                    .get("legacy", {})
                    or {}
                )
                out.append({
                    "id": str(legacy.get("id_str") or ""),
                    "text": legacy.get("full_text") or legacy.get("text") or "",
                    "username": user.get("screen_name") or "",
                    "display_name": user.get("name") or "",
                    "followers": int(user.get("followers_count") or 0),
                    "likes": int(legacy.get("favorite_count") or 0),
                    "retweets": int(legacy.get("retweet_count") or 0),
                    "replies": int(legacy.get("reply_count") or 0),
                    "views": int(legacy.get("views_count") or 0),
                    "created_at": legacy.get("created_at") or "",
                    "language": legacy.get("lang") or "",
                })
        return out

    # ─── 归一化 ────────────────────────────────────────────────────────────────
    def _normalize_item(self, item, keyword):
        username = item.get("username") or ""
        tid = item.get("id") or ""
        url = f"https://x.com/{username}/status/{tid}" if username and tid else ""

        publish_ts = 0
        created = item.get("created_at") or ""
        if created:
            try:
                publish_ts = int(
                    datetime.strptime(created, "%a %b %d %H:%M:%S %z %Y").timestamp()
                )
            except (ValueError, TypeError):
                publish_ts = 0

        return self.make_record(
            title=item.get("text") or "",
            url=url,
            author=item.get("display_name") or username,
            likes=item.get("likes"),
            comments=item.get("replies"),
            views=item.get("views"),
            publish_ts=publish_ts,
            keyword=keyword,
            extra={
                "shares": self._to_int(item.get("retweets")),
                "work_id": tid,
                "language": item.get("language") or "",
                "followers": self._to_int(item.get("followers")),
                "source": "X API v2 / GraphQL",
            },
        )


def _brief(exc):
    s = str(exc).replace("\n", " ").strip()
    return s[:160]
