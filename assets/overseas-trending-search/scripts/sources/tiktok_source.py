#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TikTok 平台适配器 — 开源实现版（yt-dlp）
==========================================

原版：POST {DATA_API_BASE}/tiktok/ability/searchVideo（需要用户自建付费转售服务）
本版：用 yt-dlp 的 TikTok extractor 取视频元数据。

实测（2026-08）能力边界：
  - 单视频详情（URL 直给）：可用，字段含 view/like/comment/timestamp/creator
  - 关键词搜索：yt-dlp 无 tiktok 搜索 extractor，TikTok 网页搜索 API 需 msToken/X-Bogus 签名，
    未登录返回空 body。因此本实现对「关键词搜索」给出明确的不可用提示，而不是伪造数据。
  - 用户作品列表：需要 secUid（channel_id），可从任一视频详情里拿到。
    调用形态 tiktokuser:<secUid>。

因此 search() 的行为是：
  - keyword 形如 https://www.tiktok.com/@x/video/123  -> 直接取该视频详情
  - keyword 形如 @username 或 username               -> 取该用户最新作品列表
  - 其他关键词                                       -> 明确抛 PlatformUnavailable，提示改走官方/付费接口
"""

import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from .base import BaseSource, PlatformUnavailable

try:
    import yt_dlp
    HAS_YTDLP = True
except ImportError:
    HAS_YTDLP = False


class TikTokSource(BaseSource):
    platform = "tiktok"
    display_name = "TikTok"
    #: 用户作品列表取多少条
    user_list_limit = 10

    def search(self, session, keyword):
        """注意：session 参数保留是为了兼容 BaseSource 接口，本实现不使用。"""
        if not HAS_YTDLP:
            raise PlatformUnavailable(
                "缺少 yt-dlp，请执行：python -m pip install -U yt-dlp"
            )

        raw = (keyword or "").strip()
        if not raw:
            return []

        # 形态 1：完整 TikTok 视频 URL
        if re.search(r"tiktok\.com/.*?/video/\d+", raw):
            return self._from_video_url(raw, raw)

        # 形态 2：显式 @username（必须带 @，否则按普通关键词处理，避免把 "AI" 当账号）
        m = re.fullmatch(r"@([A-Za-z0-9_.]{2,24})", raw)
        if m:
            return self._from_username(m.group(1), raw)

        # 形态 3：普通关键词 —— 本实现不支持
        raise PlatformUnavailable(
            "TikTok 关键词搜索需要 msToken/X-Bogus 签名或登录态，yt-dlp 无此 extractor。"
            "可用替代方式：\n"
            "  - 给完整视频链接（https://www.tiktok.com/@user/video/123）取单条详情\n"
            "  - 给 @username 取该用户最新作品列表\n"
            "  - 或用 Douyin（国内抖音）同名技能，其数据服务支持关键词搜索"
        )

    # ─── 单视频详情 ────────────────────────────────────────────────────────────
    def _from_video_url(self, url, keyword):
        info = self._extract(url)
        if not info:
            return []
        return [self._normalize_video(info, keyword)]

    # ─── 用户作品列表 ──────────────────────────────────────────────────────────
    def _from_username(self, username, keyword):
        # 先通过用户页拿不到 secUid 时，尝试 tiktokuser:<username>
        candidates = [
            f"https://www.tiktok.com/@{username}",
            f"tiktokuser:{username}",
        ]
        last_err = None
        for cand in candidates:
            try:
                info = self._extract(cand, flat_playlist=True, playlist_end=self.user_list_limit)
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                continue
            if not info:
                continue
            entries = info.get("entries") or []
            if not entries and info.get("id"):
                entries = [info]
            records = [
                self._normalize_video(e, keyword)
                for e in entries
                if isinstance(e, dict)
            ]
            if records:
                return records

        raise PlatformUnavailable(
            f"取不到 @{username} 的作品列表"
            f"（{_brief(last_err) if last_err else '无法解析 secondary user ID'}）。"
            "请改用完整视频链接，或在浏览器里确认该账号存在。"
        )

    def _extract(self, url, flat_playlist=False, playlist_end=None):
        opts = {
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "skip_download": True,
        }
        if flat_playlist:
            opts["extract_flat"] = True
        if playlist_end:
            opts["playlistend"] = playlist_end
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception as exc:  # noqa: BLE001
            raise PlatformUnavailable(f"yt-dlp 提取失败: {_brief(exc)}") from exc

    # ─── 归一化 ────────────────────────────────────────────────────────────────
    def _normalize_video(self, item, keyword):
        vid = str(item.get("id") or "")
        uploader = item.get("uploader") or item.get("channel") or ""
        uploader_id = item.get("uploader_id") or ""

        url = item.get("webpage_url") or ""
        if not url and uploader_id and vid:
            url = f"https://www.tiktok.com/@{uploader_id}/video/{vid}"
        if not url and vid:
            url = f"https://www.tiktok.com/video/{vid}"

        publish_ts = 0
        if item.get("timestamp"):
            try:
                publish_ts = int(item["timestamp"])
            except (ValueError, TypeError):
                publish_ts = 0
        if not publish_ts and item.get("upload_date"):
            try:
                publish_ts = int(
                    datetime.strptime(str(item["upload_date"]), "%Y%m%d").timestamp()
                )
            except (ValueError, TypeError):
                publish_ts = 0

        cover = item.get("thumbnail") or ""
        if not cover:
            thumbs = item.get("thumbnails")
            if isinstance(thumbs, list) and thumbs:
                cover = (thumbs[-1] or {}).get("url") or ""

        return self.make_record(
            title=item.get("title") or item.get("description") or "",
            url=url,
            author=uploader or uploader_id,
            likes=item.get("like_count"),
            comments=item.get("comment_count"),
            views=item.get("view_count"),
            publish_ts=publish_ts,
            keyword=keyword,
            extra={
                "shares": self._to_int(item.get("repost_count")),
                "work_id": vid,
                "area": "",
                "cover": cover,
                "source": "yt-dlp",
            },
        )


def _brief(exc):
    s = str(exc).replace("\n", " ").strip()
    if "429" in s or "Too Many Requests" in s:
        return "TikTok 限流 (429)，请隔几分钟再试"
    return s[:160]
