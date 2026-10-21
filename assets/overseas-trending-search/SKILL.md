---
name: overseas-trending-search
display_name: 海外跨平台热文搜索
display_name_en: Overseas Trending Search
description: 海外跨平台热文搜索 — 输入任意关键词（中文/英文），一次搜索 X / TikTok / YouTube 三平台热门内容，每平台 Top N（默认5）统一列表（平台/标题/作者/播放/点赞/评论/发布时间/链接），终端分组表格 + CSV 导出 + 交互式 HTML 报告（卡片/表格双视图）。按关键词语言智能优先同语言内容（中文词→中文优先，英文词→英文优先，其余语言兜底）。当用户需要搜索海外平台热点、跨平台内容对比、话题/品牌舆情监控、技术情报采集时使用。
description_zh: 输入关键词（中英文均可），一次搜索 X / TikTok / YouTube 三平台热门内容，每平台 Top N 统一字段列表（平台/标题/作者/播放/点赞/评论/发布时间），中文关键词优先中文内容、英文关键词优先英文内容，终端分组表格 + CSV + 交互式 HTML 报告（卡片/表格双视图），适合热点追踪、跨平台对比与素材采集。
description_en: "Search any keyword (Chinese or English) across X / TikTok / YouTube and get each platform's Top N trending posts in one unified list (platform/title/author/views/likes/comments/date). Language-aware ranking: a Chinese keyword surfaces Chinese content first, an English keyword surfaces English content first, other languages as fallback. Grouped terminal table + CSV export + interactive HTML report (card/table views) — ideal for trend tracking, cross-platform comparison and content research."
category: data-analysis
version: 1.3.0
author: Qoder
permissions:
  - network
  - filesystem-write
---

# 海外跨平台热文搜索

输入任意关键词（中文/英文），一键搜索 X / TikTok / YouTube 三平台热门内容，每平台按点赞/播放/评论/发布时间取 Top N（默认 5），输出统一字段列表：平台、标题、作者、播放数、点赞数、评论数、发布时间、链接。

> 本技能已改为开源实现（yt-dlp + X 官方接口），**不需要付费转售 API**。若只需 YouTube，装个 yt-dlp 就能跑。
> 架构为平台适配器模式：新平台（如 YouTube）只需新增适配器文件，主流程零改动。

---

## 使用场景

| 场景 | 示例 |
|------|------|
| **每日热点追踪** | 每天跑一次 "AI"，掌握三平台当日最热内容 |
| **跨平台对比** | 同一关键词对比 X / TikTok / YouTube 的热度与内容形态差异 |
| **话题事件追踪** | 搜 "新能源,EV" 追踪特定话题跨平台传播 |
| **品牌/舆情监控** | 搜产品或项目名，看海外用户的真实讨论与热门反馈 |
| **数据导出归档** | 导出 CSV 做技术情报库与数据分析 |
| **账号内容挖掘** | TikTok 侧支持按作者作品列表下钻（userAwemeList） |

---

## 使用方法

```bash
# 基础用法：单关键词（默认最近 24 小时，按播放数降序）
python3 "$SKILL_PATH/scripts/digest.py" "AI"

# 中文关键词 / 多关键词（英文逗号分隔）
python3 "$SKILL_PATH/scripts/digest.py" "人工智能,AI agent"

# 放宽时间窗口到最近 3 天（TikTok 热门多为历史内容，建议放宽）
python3 "$SKILL_PATH/scripts/digest.py" "AI" --days 3

# 只跑指定平台
python3 "$SKILL_PATH/scripts/digest.py" "AI" --platforms tiktok

# 按发布时间排序
python3 "$SKILL_PATH/scripts/digest.py" "AI" --sort time

# 按点赞数排序 / 调整每平台返回条数（默认 5）
python3 "$SKILL_PATH/scripts/digest.py" "AI" --sort likes --top 10

# 仅导出 CSV / 不自动打开浏览器
python3 "$SKILL_PATH/scripts/digest.py" "AI" --csv-only --no-open
```

CSV / HTML 默认保存在 `~/Downloads/DouyinExpertOverseasTrending/`。

---

## 返回结果展示规范

向用户展示结果时，**必须**包含以下字段：

| 字段 | 说明 |
|------|------|
| 平台 | X / TikTok / YouTube（带平台标识色） |
| 标题 | 推文/视频文案摘要，仅展示前 20 字（HTML 表格悬停看全文） |
| 作者 | 作者昵称 |
| 播放数 | 千/万简写（如 47.3w），展示在作者之后 |
| 点赞数 | 千/万简写（如 62.9w） |
| 评论数 | 同上 |
| 发布时间 | `YYYY-MM-DD HH:mm` |
| 链接 | 可点击跳转原文 |

平台状态需在结果前明示：某平台上游故障时优雅降级并在报告中标注，不影响其他平台结果。

- 条数约束：每个平台最多返回 `--top` N 条（默认 5），按 `--sort` 指标在平台组内降序；终端与 HTML 均按平台分组展示。
- 语言优先分层：中文关键词时各平台组内优先展示中文内容、英文关键词优先英文内容，组内中/英文内容不足时以其他语言兜底；层内仍按排序指标降序。
- HTML 报告支持「卡片 / 表格」双视图切换，表格视图含点赞/评论/播放/分享全字段。
- YouTube 点赞数在 ytsearch 列表里不可得，故点赞列显示 0（**不伪造**）；播放数、标题、作者、时长为真实值。

---

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `keywords` | 关键词，中英文均可，多词英文逗号分隔（位置参数） | — |
| `--days` | 时间窗口：最近 N 天（0=不限） | `1` |
| `--platforms` | 平台列表：`x,tiktok,youtube` 任意组合 | `x,tiktok,youtube` |
| `--sort` | 排序：`views` / `likes` / `comments` / `time` | `views` |
| `--top` | 每平台最多返回条数（0=不限） | `5` |
| `--output-dir` | 输出目录 | `~/Downloads/DouyinExpertOverseasTrending` |
| `--csv-only` | 仅生成 CSV，不生成 HTML | — |
| `--no-open` | 不自动打开浏览器 | — |

---

## 凭据与依赖（开源实现版）

本技能已改为**开源实现**，三个平台各自走独立数据源，**不再需要 DATA_API_KEY / DATA_API_BASE**。

| 平台 | 数据源 | 需要什么 |
|------|--------|----------|
| YouTube | yt-dlp 直连 | 装 `yt-dlp`（pip 一行） |
| TikTok | yt-dlp 直连 | 同上。仅支持「视频链接」与「@用户名」，不支持关键词搜索 |
| X | 官方 API v2 / 网页 GraphQL | `X_BEARER_TOKEN`，或 `X_AUTH_TOKEN` + `X_CT0` |

安装 yt-dlp：

```bash
"<DSH 运行时 python>" -m pip install -U yt-dlp
```

X 的凭据获取：

| 方式 | 环境变量 | 说明 |
|------|----------|------|
| 官方 API v2 | `X_BEARER_TOKEN` | 稳定，需付费额度 |
| 浏览器登录态 | `X_AUTH_TOKEN` + `X_CT0` | 免费，可能随时失效 |

未配置 X 凭据时，X 平台会自动跳过并在结果里标注原因，**不影响 YouTube / TikTok**。

---

## 架构说明

```
scripts/
├── digest.py            # 主编排器：关键词×平台采集 → 时间过滤 → 排序 → 输出
├── config.py            # 输出目录 + 凭据探测（不再有网关地址）
└── sources/             # 平台适配器（新增平台只需加一个文件并在 __init__ 登记）
    ├── base.py          # BaseSource：统一 schema + 时间戳兜底
    ├── x_source.py      # X：官方 API v2 / 网页 GraphQL（需 X_BEARER_TOKEN）
    ├── tiktok_source.py # TikTok：yt-dlp（视频链接 / @用户名）
    └── youtube_source.py# YouTube：yt-dlp ytsearch（播放量排序）
```

统一记录 schema：`platform / title / url / author / likes / comments / views / publish_ts / publish_time / keyword / shares`。

### 平台接口状态（2026-07 实测）

| 平台 | 接口 | 状态 |
|------|------|------|
| X | search / tweetDetail / tweetComments | ✅ 全部可用；search 必填 `searchType`（Top/Latest），缺失会误报 3203 |
| TikTok | yt-dlp 的 TikTok extractor | ⚠️ 仅「视频链接」与「@用户名」可用；关键词搜索需要 msToken/X-Bogus 签名，本实现不支持 |
| YouTube | yt-dlp 的 ytsearch | ✅ 可用，返回播放数/标题/作者/时长；列表不含点赞数，故点赞列为 0（不伪造） |

---

## 依赖

```bash
pip3 install requests
```

---

## 常见问题

**Q：X 搜索返回 3203 报错？**
A：X search 接口的 `searchType` 为必填参数（`Top` 热门 / `Latest` 最新），缺失时 data service 会返回误导性的 3203「X能力调用失败」。本技能已内置该参数；另外过期/无效的 tweetId 调 tweetDetail 也会报 3203。

**Q：TikTok 搜索需要调详情接口补数据吗？**
A：YouTube 走 yt-dlp，一次搜索即返回播放数/标题/作者/时长；点赞数列表接口不提供，所以点赞列为 0。

**Q：YouTube 的点赞/评论数据从哪里来的？**
A：yt-dlp 的搜索结果只带播放数，不带点赞/评论。本实现如实把点赞/评论显示为 0，不做估算；要看真实点赞数请用 youtube-digest 技能取单视频详情，或配 X/YouTube 官方 API。

**Q：每平台返回多少条？**
A：默认每平台按排序指标（点赞/播放/评论/发布时间）取 Top 5，`--top N` 可调（0=不限）。各平台独立分组、组内降序，互不影响。

**Q：为什么默认参数下看不到 TikTok 内容？**
A：TikTok 关键词搜索在本实现里不可用（需要 msToken/X-Bogus 签名）。请改用「视频链接」或「@用户名」形态；带 `--days 0` 可取消时间过滤。

**Q：搜中文关键词，为什么 X 上的日文内容被排到后面了？**
A：技能内置语言优先分层：关键词为中文时，各平台组内优先展示中文内容、其次英文，日文等其他语言兜底（解决「南海」命中日文「南海電鉄」这类歧义问题）；英文关键词同理优先英文内容。语言识别基于标题字符集（汉字/假名/谚文/拉丁字母），无第三方依赖。

**Q：想做每日定时运行？**
A：可以让 AI 注册定时任务，每天自动执行 `digest.py` 并生成报告。
