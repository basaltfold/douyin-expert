#!/usr/bin/env python3
"""
从周榜TOP账号拉取上周作品数据，构建"点赞飙升七日榜"
"""
import os, json, sys, time, urllib.request, urllib.error
from datetime import datetime, date

API_KEY = os.environ.get("REDFOX_API_KEY", "").strip()
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "X-API-KEY": API_KEY,
}

def api_post(url, payload, timeout=20):
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

# 读取周榜数据
with open("douyin-top-account/output/week_rank.json", "r", encoding="utf-8") as f:
    week_data = json.load(f)

date_start = week_data["dateStart"]  # 2026-07-20
date_end = week_data["dateEnd"]      # 2026-07-26
dt_start = datetime.strptime(date_start, "%Y-%m-%d")
dt_end = datetime.strptime(date_end, "%Y-%m-%d").replace(hour=23, minute=59, second=59)

accounts = week_data["list"][:20]  # TOP 20 账号
print(f"数据周期: {date_start} ~ {date_end}")
print(f"查询 {len(accounts)} 个账号的作品...")

all_works = []

for i, acc in enumerate(accounts):
    name = acc["accountName"]
    sys.stdout.buffer.write(f"[{i+1}/{len(accounts)}] 正在获取: {name}...".encode("utf-8"))
    sys.stdout.flush()

    try:
        result = api_post(f"{os.environ.get('REDFOX_API_BASE', 'https://redfox.hk')}/story/api/dyData/queryUserWithWorks", {
            "accountName": name,
            "source": "douyin-top-account-Qoder"
        })
        code = result.get("code")
        d = result.get("data", {})

        if code == 2000 and d:
            works = d.get("workList", [])
            nickname = d.get("nickname", name)

            # 筛选上周发布的作品
            week_works = []
            for w in works:
                pub_time_str = w.get("publishTime", "")
                if not pub_time_str:
                    continue
                try:
                    pub_dt = datetime.strptime(pub_time_str, "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    continue
                if dt_start <= pub_dt <= dt_end:
                    w["_author"] = nickname
                    w["_authorUrl"] = acc.get("profileUrl", "")
                    w["_category"] = acc.get("category", "")
                    week_works.append(w)

            all_works.extend(week_works)
            sys.stdout.buffer.write(f" {len(works)}条作品中筛选出{len(week_works)}条\n".encode("utf-8"))
        else:
            print(f" 失败(code={code})")
    except Exception as e:
        print(f" 异常: {e}")

    time.sleep(0.8)  # 防止限流

# 按点赞数排序，取TOP 20
all_works.sort(key=lambda w: w.get("likeCount", 0) or 0, reverse=True)
top20_works = all_works[:20]

print(f"\n共获取 {len(all_works)} 条上周作品，TOP20 点赞飙升作品:")

# 输出JSON
output_data = {
    "period": "week",
    "dateStart": date_start,
    "dateEnd": date_end,
    "category": "全部",
    "total": len(all_works),
    "list": []
}

for i, w in enumerate(top20_works, 1):
    like = w.get("likeCount", 0) or 0
    comment = w.get("commentCount", 0) or 0
    share = w.get("shareCount", 0) or 0
    collect = w.get("collectCount", 0) or 0
    interactive = w.get("interactiveCount", 0) or 0
    title = w.get("title", "无标题")
    author = w.get("_author", "")
    author_url = w.get("_authorUrl", "")
    category = w.get("_category", "")
    url = w.get("url", "")
    pub_time = w.get("publishTime", "")

    item = {
        "rank": i,
        "title": title,
        "author": author,
        "authorUrl": author_url,
        "category": category,
        "likeCount": like,
        "commentCount": comment,
        "shareCount": share,
        "collectCount": collect,
        "interactiveCount": interactive,
        "publishTime": pub_time,
        "url": url,
    }
    output_data["list"].append(item)
    sys.stdout.buffer.write(f"  #{i} {title[:30]} | {author} | {like:,}赞\n".encode("utf-8"))

# 保存
output_path = "douyin-top-account/output/week_likes_surge_works.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print(f"\n已保存到: {output_path}")
