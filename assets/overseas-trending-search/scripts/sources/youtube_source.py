#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube 平台适配器 — 开源实现版（yt-dlp）
============================================

原版：POST {DATA_API_BASE}/youtube/searchVideo + videoDetail（需要用户自建付费转售服务）
本版：调用 yt-dlp 的 `ytsearchN:` 伪 URL，直接拿 YouTube 搜索结果 JSON。

实测（2026-08）：yt-dlp 的 ytsearch 稳定可用，返回的字段包含
  id / title / channel / uploader / view_count / duration / timestamp / thumbnails
无 Key、无凭据、纯本地解析。
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


class YouTubeSource(BaseSource):
    platform = "youtube"
    display_name = "YouTube"
    #: 每次搜索取多少条（yt-dlp 的 ytsearchN 里的 N）
    search_limit = 15

    def search(self, session, keyword):
        """注意：session 参数保留是为了兼容 BaseSource 接口，本实现不使用。"""
        if not HAS_YTDLP:
            raise PlatformUnavailable(
                "缺少 yt-dlp，请执行：python -m pip install -U yt-dlp"
            )

        query = f"ytsearch{self.search_limit}:{keyword}"
        opts = {
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "extract_flat": True,       # 只要列表，不下钻每个视频
            "skip_download": True,
        }

        videos = []
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(query, download=False)
        except Exception as exc:  # noqa: BLE001
            raise PlatformUnavailable(f"YouTube 搜索失败（yt-dlp）: {_brief(exc)}") from exc

        entries = (info or {}).get("entries") or []
        for item in entries:
            if not isinstance(item, dict):
                continue
            videos.append(item)

        if not videos:
            return []

        records = [self._normalize_item(v, keyword) for v in videos]
        # 按播放量排序（本实现拿不到点赞数，用播放量近似热度）
        records.sort(key=lambda r: r["views"], reverse=True)
        return records

    def _normalize_item(self, item, keyword):
        vid = str(item.get("id") or "")
        cover = ""
        thumbs = item.get("thumbnails")
        if isinstance(thumbs, list) and thumbs:
            best = max(
                (t for t in thumbs if isinstance(t, dict)),
                key=lambda t: int(t.get("width") or 0) * int(t.get("height") or 0),
                default=None,
            )
            if best:
                cover = best.get("url") or ""

        # 发布时间：timestamp（秒级）优先，其次 upload_date（YYYYMMDD）
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

        return self.make_record(
            title=item.get("title") or "",
            url=f"https://www.youtube.com/watch?v={vid}" if vid else "",
            author=item.get("channel") or item.get("uploader") or "",
            likes=0,  # ytsearch 列表不含点赞数，不做伪造
            comments=0,
            views=item.get("view_count") or 0,
            publish_ts=publish_ts,
            keyword=keyword,
            extra={
                "shares": 0,
                "work_id": vid,
                "cover": cover,
                "duration": _fmt_duration(item.get("duration")),
                "channel_id": item.get("channel_id") or "",
                "source": "yt-dlp",
            },
        )


def _fmt_duration(seconds):
    """秒 -> MM:SS / HH:MM:SS"""
    try:
        s = int(seconds or 0)
    except (ValueError, TypeError):
        return ""
    if s <= 0:
        return ""
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"


def _brief(exc):
    """把 yt-dlp 的长错误压成一行。"""
    s = str(exc).replace("\n", " ").strip()
    if "429" in s or "Too Many Requests" in s:
        return "YouTube 限流 (429)，请隔几分钟再试"
    return s[:160]
