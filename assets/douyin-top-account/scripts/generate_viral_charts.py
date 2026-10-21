#!/usr/bin/env python3
"""
生成抖音周榜 HTML 可视化报告
- 适配 3:4 小红书卡片比例 (1080px 宽)
- 深色主题，大字体，紧凑布局
- 两个榜单：热门账号 TOP20 + 点赞飙升 TOP20（作品维度）
"""
import json
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "output"


def parse_num(val) -> int:
    if val is None or val == "-" or val == "":
        return 0
    s = str(val).strip()
    if not s:
        return 0
    if 'w' in s.lower() or '万' in s:
        try:
            return int(float(s.lower().replace('w', '').replace('万', '')) * 10000)
        except:
            return 0
    if '亿' in s:
        try:
            return int(float(s.replace('亿', '')) * 100000000)
        except:
            return 0
    try:
        return int(float(s))
    except:
        return 0


def fmt_w(val) -> str:
    if val is None or val == "-" or val == "":
        return "-"
    s = str(val).strip()
    if not s:
        return "-"
    if 'w' in s.lower():
        try:
            n = float(s.lower().replace('w', '')) * 10000
            return f"{int(n) // 10000}w+"
        except:
            return "-"
    if '亿' in s:
        return s if '+' in s else s + "+"
    try:
        n = int(float(s))
    except:
        return "-"
    if n == 0:
        return "-"
    if n >= 10000:
        return f"{n // 10000}w+"
    return str(n)


def fmt_followers(val) -> str:
    if val is None or val == "-" or val == "":
        return "-"
    s = str(val).strip()
    if not s:
        return "-"
    if '亿' in s:
        return s
    if 'w' in s.lower():
        return s
    try:
        n = int(float(s))
    except:
        return s
    if n >= 100000000:
        return f"{n/100000000:.1f}亿"
    if n >= 10000:
        return f"{n/10000:.1f}w"
    return str(n)


def fmt_num(val) -> str:
    if val is None or val == 0 or val == "-":
        return "-"
    try:
        n = int(val)
    except:
        return str(val)
    if n >= 100000000:
        return f"{n/100000000:.1f}亿+"
    if n >= 10000:
        return f"{n // 10000}w+"
    return str(n)


CSS = """
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
    background: linear-gradient(160deg, #0A0E2B 0%, #141852 40%, #1A1D4C 70%, #0D1033 100%);
    width: 1080px;
    color: #fff;
  }
  .container { padding: 32px 36px 24px; }
  .badge {
    display: inline-block;
    background: linear-gradient(135deg, #ff6b35, #ff4500);
    color: #fff; padding: 4px 14px; border-radius: 16px;
    font-size: 15px; font-weight: 700; margin-bottom: 10px;
  }
  .title {
    font-size: 32px; font-weight: 800; color: #FFD700;
    margin-bottom: 6px; text-shadow: 0 2px 10px rgba(255,215,0,0.3);
  }
  .subtitle {
    font-size: 14px; color: rgba(255,255,255,0.55); margin-bottom: 20px;
  }
  table { width: 100%; border-collapse: collapse; }
  thead th {
    background: rgba(255,255,255,0.07);
    color: rgba(255,255,255,0.65);
    padding: 10px 8px; font-size: 16px; font-weight: 600;
    white-space: nowrap; letter-spacing: 0.5px;
    border-bottom: 2px solid rgba(255,255,255,0.12);
  }
  tbody tr { border-bottom: 1px solid rgba(255,255,255,0.05); }
  td {
    padding: 9px 8px; font-size: 17px;
    vertical-align: middle; white-space: nowrap;
  }
  .rank-badge {
    display: inline-flex; align-items: center; justify-content: center;
    width: 28px; height: 28px; border-radius: 50%;
    font-weight: 700; font-size: 15px;
  }
  .footer {
    display: flex; justify-content: space-between;
    margin-top: 14px; font-size: 12px; color: rgba(255,255,255,0.3);
  }
"""


def _rank_html(rank):
    if rank == 1:
        bg, color = "#FFD700", "#5d4000"
    elif rank == 2:
        bg, color = "#C0C0C0", "#3d3d3d"
    elif rank == 3:
        bg, color = "#CD7F32", "#fff"
    else:
        bg, color = "rgba(255,255,255,0.1)", "#999"
    return f'<span class="rank-badge" style="background:{bg};color:{color}">{rank}</span>'


def generate_account_html(data, output_path):
    """热门账号榜 — 列: # 账号名 综合评分 总粉丝 新增粉丝 新增点赞 新增评论 新增分享"""
    items = sorted(data.get("list", []), key=lambda x: x.get('comprehensiveScore', 0), reverse=True)[:20]
    date_start = data.get("dateStart", "")
    date_end = data.get("dateEnd", "")
    date_display = f"{date_start} — {date_end}".replace("-", ".")

    rows = ""
    for i, item in enumerate(items, 1):
        name = item.get('accountName', '')
        score = item.get('comprehensiveScore', 0)
        followers = fmt_followers(item.get('followers'))
        new_fans = fmt_w(item.get('newFans'))
        new_likes = fmt_w(item.get('newLikes'))
        new_comments = fmt_w(item.get('newComments'))
        new_shares = fmt_w(item.get('newShares'))

        score_badge = f'<span style="background:rgba(255,215,0,0.15);color:#FFD700;padding:2px 10px;border-radius:10px;font-weight:700;font-size:16px">{score}</span>'

        rows += f"""<tr>
<td style="text-align:center">{_rank_html(i)}</td>
<td style="font-weight:600;color:#fff;max-width:140px;overflow:hidden;text-overflow:ellipsis">{name}</td>
<td style="text-align:center">{score_badge}</td>
<td style="text-align:right;color:#bbb">{followers}</td>
<td style="text-align:right;color:#bbb">{new_fans}</td>
<td style="text-align:right;color:#ff4757;font-weight:700;font-size:18px">{new_likes}</td>
<td style="text-align:right;color:#bbb">{new_comments}</td>
<td style="text-align:right;color:#bbb">{new_shares}</td>
</tr>
"""

    thead = """<tr>
<th style="text-align:center;width:40px">#</th>
<th style="text-align:left">账号名</th>
<th style="text-align:center">评分</th>
<th style="text-align:right">总粉丝</th>
<th style="text-align:right">新增粉丝</th>
<th style="text-align:right">新增点赞</th>
<th style="text-align:right">新增评论</th>
<th style="text-align:right">新增分享</th>
</tr>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<style>{CSS}</style></head>
<body><div class="container">
<div class="badge">🔥 周度热榜</div>
<div class="title">抖音每周热门账号 TOP20</div>
<div class="subtitle">数据周期：{date_display} · 全品类 · 综合评分排名</div>
<table><thead>{thead}</thead><tbody>{rows}</tbody></table>
<div class="footer">
<span>数据来源：数据服务 API · 周度新增互动统计</span>
<span>完整榜单 50 条 · 关注获取更多</span>
</div></div></body></html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] {output_path}")


def generate_works_html(data, output_path):
    """点赞飙升榜 — 列: # 作品标题 作者 新增评论 新增分享 新增点赞"""
    items = sorted(data.get("list", []), key=lambda x: x.get('likeCount', 0) or 0, reverse=True)[:20]
    date_start = data.get("dateStart", "")
    date_end = data.get("dateEnd", "")
    date_display = f"{date_start} — {date_end}".replace("-", ".")

    rows = ""
    for i, item in enumerate(items, 1):
        title = (item.get('title', '') or '无标题')[:35]
        author = item.get('author', '')
        new_comments = fmt_num(item.get('commentCount'))
        new_shares = fmt_num(item.get('shareCount'))
        new_likes = fmt_num(item.get('likeCount'))

        rows += f"""<tr>
<td style="text-align:center">{_rank_html(i)}</td>
<td style="font-weight:600;color:#fff;max-width:300px;overflow:hidden;text-overflow:ellipsis">{title}</td>
<td style="color:#8888bb;font-size:15px">{author}</td>
<td style="text-align:right;color:#bbb">{new_comments}</td>
<td style="text-align:right;color:#bbb">{new_shares}</td>
<td style="text-align:right;color:#ff4757;font-weight:700;font-size:18px">{new_likes}</td>
</tr>
"""

    thead = """<tr>
<th style="text-align:center;width:40px">#</th>
<th style="text-align:left">作品标题</th>
<th style="text-align:left">作者</th>
<th style="text-align:right">新增评论</th>
<th style="text-align:right">新增分享</th>
<th style="text-align:right">新增点赞</th>
</tr>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<style>{CSS}</style></head>
<body><div class="container">
<div class="badge">🔥 周度飙升榜</div>
<div class="title">抖音每周点赞飙升 TOP20</div>
<div class="subtitle">数据周期：{date_display} · 全品类 · 周度新增互动排名</div>
<table><thead>{thead}</thead><tbody>{rows}</tbody></table>
<div class="footer">
<span>数据来源：数据服务 API · 周度新增互动统计</span>
<span>完整榜单 50 条 · 关注获取更多</span>
</div></div></body></html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[OK] {output_path}")


def main():
    # 账号榜
    with open(OUTPUT_DIR / "week_rank.json", "r", encoding="utf-8") as f:
        account_data = json.load(f)
    generate_account_html(account_data, str(OUTPUT_DIR / "douyin_weekly_hot_accounts.html"))

    # 飙升榜（作品维度）
    works_path = OUTPUT_DIR / "week_likes_surge_works.json"
    if works_path.exists():
        with open(works_path, "r", encoding="utf-8") as f:
            works_data = json.load(f)
        generate_works_html(works_data, str(OUTPUT_DIR / "douyin_weekly_likes_surge.html"))
    else:
        print(f"[WARN] 作品数据文件不存在: {works_path}")


if __name__ == "__main__":
    main()
