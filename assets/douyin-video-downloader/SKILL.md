---
name: douyin-video-downloader
description: 抖音本人账号作品下载备份工具 — 输入本人抖音号，拉取本人账号作品列表并下载到本地，用于个人备份与存档。仅支持下载用户本人拥有著作权的作品。触发词：抖音主页下载、抖音视频下载、下载抖音作品、抖音账号视频提取、抖音视频保存、抖音视频备份。
display_name: 抖音本人作品下载
display_name_en: Douyin Own Works Downloader
description_zh: 输入本人抖音号拉取本人作品并下载到本地，用于个人备份存档
description_en: Fetch and download your own Douyin works locally for personal backup
category: media
version: 1.0.0
author: Douyin Toolkit
---
# 抖音本人作品下载器

> 输入本人抖音号 → 拉取本人作品列表 → 获取下载链接 → 一键下载到本地备份

---

## 简介

抖音本人账号作品下载备份工具。只需提供本人抖音号，自动拉取本人账号近期作品列表，逐条获取视频/图文下载直链，支持一键下载到本地用于个人备份存档。

> ⚠️ **合规声明**：本工具仅限下载用户本人拥有著作权的作品，用于个人备份存档。禁止用于下载他人作品。

---

## 功能特性

| 功能        | 说明                                                   |
| ----------- | ------------------------------------------------------ |
| 📋 作品拉取 | 通过抖音号获取账号近期作品（标题、互动数据、作品链接） |
| 🔗 链接解析 | 逐条调用解析接口，获取视频/图文下载直链                |
| 📥 本地备份 | 一键下载本人全部作品（视频+图文）到本地 `output/` 目录 |
| 📊 数据展示 | Markdown 表格 / JSON 双格式输出，含完整互动数据        |
| 📄 分页翻页 | 支持翻页查看更多作品                                   |
| 📅 日期筛选 | 可按作品发布时间挑选                                   |
| ⚡ 速率保护 | 内置请求间隔，避免触发频率限制                         |

---

## API 说明

本 Skill 调用数据服务 API 的两个接口：

| 步骤        | 接口                                             | 说明                           |
| ----------- | ------------------------------------------------ | ------------------------------ |
| 1. 拉取作品 | `POST /story/api/dy/data/listWorkByAccount`      | 根据抖音号获取作品列表         |
| 2. 解析下载 | `POST /story/api/parseWork/videoDownload/douyin` | 根据作品链接获取下载直链 |

### 认证

自行配置你有权使用的 API Key（环境变量 `REDFOX_API_KEY`）。

```bash
# 环境变量配置（推荐）
export REDFOX_API_KEY=ak_你的密钥

# Windows PowerShell
$env:REDFOX_API_KEY="ak_你的密钥"
```

---

## 使用方式

### CLI 命令行

```bash
# 基础用法：拉取作品并解析下载链接（不下载文件）
python3 "$SKILL_PATH/scripts/douyin_video_downloader.py" --account "Fish688688"

# 下载视频到本地
python3 "$SKILL_PATH/scripts/douyin_video_downloader.py" --account "Fish688688" --download

# 指定下载目录
python3 "$SKILL_PATH/scripts/douyin_video_downloader.py" --account "Fish688688" --download --output-dir./my_videos

# JSON 格式输出
python3 "$SKILL_PATH/scripts/douyin_video_downloader.py" --account "Fish688688" --json

# 多账号（逗号分隔）
python3 "$SKILL_PATH/scripts/douyin_video_downloader.py" --accounts "Fish688688,YuZhouXiaoLi1220" --download

# 指定作品数量（默认10，最多50）
python3 "$SKILL_PATH/scripts/douyin_video_downloader.py" --account "Fish688688" --count 20 --download

# 翻页查看更多作品
python3 "$SKILL_PATH/scripts/douyin_video_downloader.py" --account "Fish688688" --page 2

# 按日期范围筛选作品
python3 "$SKILL_PATH/scripts/douyin_video_downloader.py" --account "Fish688688" --date-start 2026-07-01 --date-end 2026-07-31

# 组合使用：第2页 + 日期过滤 + 下载
python3 "$SKILL_PATH/scripts/douyin_video_downloader.py" --account "Fish688688" --page 2 --count 20 --date-start 2026-06-01 --download
```

### 参数说明

| 参数           | 说明                           |
| -------------- | ------------------------------ |
| `--account`    | 单个抖音号                     |
| `--accounts`   | 多个抖音号，逗号分隔           |
| `--count`      | 拉取作品数量（默认10，最多50） |
| `--page`       | 页码（默认1）                  |
| `--date-start` | 起始日期 YYYY-MM-DD            |
| `--date-end`   | 结束日期 YYYY-MM-DD            |
| `--download`   | 下载视频文件到本地             |
| `--output-dir` | 下载目录（默认 `output/`）     |
| `--json`       | JSON 格式输出                  |
| `--rate-limit` | 请求间隔秒数（默认 1.0）       |
| `--api-key`    | 指定 API Key                   |

### 依赖

| 依赖       | 安装命令                |
| ---------- | ----------------------- |
| `requests` | `pip3 install requests` |

---

## 抖音号要求

接口通过 `uniqueName`（抖音展示ID）查询，脚本将用户提供的抖音号统一按 `uniqueName` 传入，`userId` 和 `shortId` 固定为空字符串。**必须提供抖音号**。

**重要：** 若用户只输入账号名称（如"李佳琦""老高與小茉"）而未提供抖音号，必须提示：

> "抖音账号名称存在多个重名情况，请提供准确的**抖音号**以便精准查询。"

（在抖音 APP → 目标账号主页 → 昵称下方查看抖音号）

> **抖音号**是抖音 APP → 目标账号主页 → 昵称下方显示的唯一 ID（如 `Fish688688`、`YuZhouXiaoLi1220`），非中文昵称。

---

## 数据规则

### 失败阈值保护

- **同一抖音号在 6 小时内累计 5 次 API 调用失败后，后续请求将被拒绝**

- 拒绝时提示：「当前账号下载已超过失败阈值，请稍后再试」

- **距上次失败超过 6 小时**，计数自动归零，恢复正常调用

- **同一账号查询成功**（API 返回正常数据），计数归零，恢复正常调用

- 失败计数持久化至 `~/.qoder/douyin_video_downloader_failures.json`

> **注意：** 仅记录因网络超时、API 错误码（3108/3106/3107/400 等）导致的调用失败；账号暂无作品数据（空数据）不计入失败次数。

---

## Agent 集成指南

### 触发词

- 抖音下载 / 抖音视频下载

- 抖音本人作品下载 / 抖音视频备份

- 下载抖音作品 / 抖音账号视频提取

- 帮我下载 xxx 的抖音视频

### Agent 执行流程

```
Step 1: 确认用户意图与抖音号
  - 若用户提供了抖音号（如 Fish688688），直接执行
  - 若用户只提供了账号名称（中文昵称，如"李佳琦"），必须提示：
    "抖音账号名称存在多个重名情况，请提供准确的抖音号以便精准查询。"

Step 2: 识别用户输入的时间范围（如有）
  - 若用户提到了作品时间范围，自动识别并转换为 --date-start / --date-end：
    - "7.1~7.20" → --date-start 2026-07-01 --date-end 2026-07-20
    - "7月1日到7月20日" → --date-start 2026-07-01 --date-end 2026-07-20
    - "最近一周" → 当前日期往前推 7 天
    - "上个月" → 上个月 1 日到上个月最后一天
    - "7月份的作品" → --date-start 2026-07-01 --date-end 2026-07-31
  - 日期格式固定为 YYYY-MM-DD，年份默认为当前年份
  - 若用户要求"继续"/"下一页"，添加 --page N

Step 3: 调用脚本拉取作品 + 解析下载链接
  python3 "$SKILL_PATH/scripts/douyin_video_downloader.py" --account "抖音号"

Step 4: 展示结果 + 询问翻页
  - 展示 Markdown 表格，含可点击的作品链接和下载链接
  - 若有失败：提示「可能是该作品已删除或不可下载」
  - 若可翻页：告诉用户「还有更多作品，是否需要翻看下一页？」，输入下一页翻页
  - 提示用户支持按时间范围提取作品

Step 5: 询问用户是否需要批量保存
  - 使用 AskUserQuestion：「是否需要将可下载的作品保存到本地？」
  - 选项：「下载到本地」/「只看链接即可」

Step 6: 用户确认后执行下载
  python3 "$SKILL_PATH/scripts/douyin_video_downloader.py" --account "抖音号" --download
  - 告知用户文件保存路径
```

### Agent 输出规范

解析完成后按以下格式输出（自然语言风格，面向普通用户）。

#### ⛔ 强制规则：禁止简化输出

> **Agent 必须原样展示脚本返回的完整表格，禁止以下行为：**
>
> - ❌ 禁止删除或合并任何列（发布时间、作品、赞、评论、收藏、分享、资源下载 缺一不可）
> - ❌ 禁止省略翻页提示行（"还有更多作品，输入 `--page 2` 翻看下一页"）
> - ❌ 禁止省略时间范围筛选提示（"💡 支持输入想提取的作品时间范围…"）
> - ❌ 禁止省略下载询问提示（"💾 需要将这 X 条作品批量保存到本地吗？"）
> - ❌ 禁止用「...」或摘要代替完整表格内容
> - ✅ 必须逐行展示所有作品的完整信息（含资源下载链接）

#### 输出模板

```markdown
## 📥 抖音视频下载 — @账号名（粉丝: X）

当前是**第 1 页**，共 10 条作品 | 还有更多作品，输入 `--page 2` 翻看下一页

| #   | 发布时间 | 作品                                       | 赞   | 评论 | 收藏 | 分享 | 资源下载                                      |
| --- | -------- | ------------------------------------------ | ---- | ---- | ---- | ---- | --------------------------------------------- |
| 1   | 07-28    | [作品标题](https://www.iesdouyin.com/...)  | 5.2k | 67   | 689  | 5.8k | [🎬视频](...) · [🖼封面](...) · [🎵音频](...) |
| 2   | 07-24    | [作品标题2](https://www.iesdouyin.com/...) | 3.1k | 22   | 136  | 865  | [🖼封面](...)                                 |
| 3   | …        | …                                          | …    | …    | …    | …    | …                                             |

**合计：** 10 条作品，8 条可下载，2 条下载失败

> ⚠️ 下载失败的作品可能是该作品已删除或不可下载。

> 💡 需要提取特定时间范围的作品？直接告诉我时间范围即可，如「7.1~7.20」「最近一周」

> 💾 需要将这 X 条作品保存到本地吗？直接告诉我即可。
```

---

## 常见问题

**Q：如何获取 API Key？**
A：请自行配置你有权使用的 API 密钥（环境变量 `REDFOX_API_KEY`）。

**Q：下载的作品是否有平台水印？**
A：以平台提供的原始文件为准。本工具仅用于本人作品备份，不提供去水印功能。

**Q：图文作品能下载吗？**
A：可以。图文作品（幻灯片、相册类）会自动下载首张图片，格式为 JPG/PNG/WebP。

**Q：为什么提示「调用频率超限」？**
A：API 返回 code=3108 时表示请求过快触发了限流。可增加 `--rate-limit 2.0` 延长间隔。

**Q：支持哪些抖音号格式？**
A：支持抖音展示 ID（uniqueName），如 `Fish688688`、`YuZhouXiaoLi1`
