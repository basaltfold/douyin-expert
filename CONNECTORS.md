# 抖音专家 (douyin-expert) · 凭据与依赖

本插件共 22 个技能，按数据源分三类，**各自的凭据要求完全不同**。

---

## 一、抖音 / 多平台类（19 个）：需要 redfox 数据服务

| 技能 | 说明 |
|---|---|
| `douyin-daily-hot` `douyin-hot-trend` `douyin-content-surge` `douyin-weekly-surge` | 抖音热榜 / 每日榜 / 飙升榜 |
| `douyin-search` `douyin-works-crawler` `douyin-top-account` `douyin-rise-ranking` | 作品查询 / 爬取 / 账号榜 / 涨粉榜 |
| `douyin-similar-account` `douyin-account-diagnosis` `douyin-video-downloader` | 相似账号 / 诊断 / 备份下载 |
| `douyin-ai-feed` `douyin-prohibited-word` | AI 信息源 / 违禁词检测 |
| `bili-ai-feed` `gzh-ai-feed` `ks-ai-feed` `wechat-channels-ai-feed` `xiaohongshu-ai-feed` | 其他五个平台的 AI 信息源 |

**需要两个环境变量**：

| 变量 | 说明 | 示例 |
|---|---|---|
| `REDFOX_API_BASE` | 数据服务基址 | `https://redfox.hk` |
| `REDFOX_API_KEY` | API 密钥（`X-API-Key` 头，`ak_` 前缀） | `ak_xxxxxxxx` |

⚠️ **`REDFOX_API_BASE` 必须显式设置**。这些脚本没有内置默认值，不设会报
`Invalid URL '/story/api/...' : No scheme supplied`。

申请 Key：<https://redfox.hk/settings/api-keys?source=qoder>

设置方式（Windows PowerShell，用户级永久）：

```powershell
[Environment]::SetEnvironmentVariable("REDFOX_API_BASE", "https://redfox.hk", "User")
[Environment]::SetEnvironmentVariable("REDFOX_API_KEY", "ak_xxxxxxxx", "User")
```

设完**重启 DeepSeek Harness**（宿主要重新读环境变量）。

未配置 Key 时，脚本返回明确的鉴权错误（`未找到 REDFOX_API_KEY` 或 `code=3107 API Key无效`），
**不会伪造数据**。

---

## 二、纯本地类（1 个）：无任何依赖

| 技能 | 说明 |
|---|---|
| `multi-copywrite-alchemy` | 复刻蒸馏写作，4 个 markdown 框架文件 + 纯规则分析 |

不联网、不需要 Key、不需要 pip 安装。

---

## 三、海外类（3 个）：开源实现，无付费 API

| 技能 | 数据源 | 需要什么 |
|---|---|---|
| `youtube-digest` | yt-dlp 直连 YouTube | `yt-dlp`（pip 一行） |
| `twitter-work-search` | X 官方 API v2 / 网页 GraphQL | `X_BEARER_TOKEN`，或 `X_AUTH_TOKEN` + `X_CT0` |
| `overseas-trending-search` | YouTube/TikTok 走 yt-dlp；X 走官方接口 | 同上前两项 |

### 装 yt-dlp（一条命令）

```powershell
& "$env:USERPROFILE\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe" -m pip install -U yt-dlp
```

或者跑安装脚本时加参数：

```powershell
.\install.ps1 -WithOverseasDeps
```

### X 凭据（可选，不配则 X 平台自动跳过）

X 已在 2026 年关闭未登录搜索，**没有凭据就拿不到任何推文**。二选一：

| 方式 | 环境变量 | 说明 |
|---|---|---|
| 官方 API v2 | `X_BEARER_TOKEN` | 稳定，需 X 开发者账号付费额度 |
| 浏览器登录态 | `X_AUTH_TOKEN` + `X_CT0` | 免费，可能随时失效 |

浏览器登录态获取：

1. 浏览器登录 <https://x.com>
2. F12 → Application → Cookies → `https://x.com`
3. 复制 `auth_token` 和 `ct0` 两个值
4. `set X_AUTH_TOKEN=...` / `set X_CT0=...`

**未配置时脚本明确报「X 搜索需要凭据」并给出配置指引，不会编造数据。**

---

## 四、TikTok 能力边界（重要）

yt-dlp 的 TikTok extractor **没有关键词搜索**。本实现支持的形态：

| 输入 | 是否可用 |
|---|---|
| `https://www.tiktok.com/@user/video/123` | ✅ 单条视频详情 |
| `@username` | ✅ 该用户最新作品列表（最多 10 条） |
| 任意关键词（如 `AI`） | ❌ 明确报不可用并给出替代方案 |

原因：TikTok 网页搜索 API 需要 `msToken` + `X-Bogus` 签名，未登录返回空 body。
这是平台限制，非实现缺陷。

**抖音（国内）的关键词搜索不受影响** —— 走的是 redfox 数据服务。

---

## 五、网络要求

| 目标 | 协议 | 说明 |
|---|---|---|
| `redfox.hk` | HTTPS | 19 个抖音/多平台技能的取数上游 |
| `www.youtube.com` / `youtu.be` | HTTPS | yt-dlp |
| `www.tiktok.com` | HTTPS | yt-dlp |
| `api.twitter.com` / `x.com` | HTTPS | X 官方接口 |

超时：10–30 秒。境外平台可能需要代理。

---

## 常见问题

**Q：不配任何 Key，哪些技能能用？**
A：`multi-copywrite-alchemy`（纯本地）和 `youtube-digest`（装 yt-dlp 就行）。
其余抖音类需要 redfox Key，X 类需要 X 凭据，TikTok 关键词搜索不可用。

**Q：为什么 YouTube 结果的点赞数是 0？**
A：yt-dlp 的搜索列表接口不返回点赞数。本实现如实显示 0，**不做估算**。
要真实点赞数请用 `youtube-digest` 取单视频详情。

**Q：抖音技能报 `No scheme supplied`？**
A：缺 `REDFOX_API_BASE`。设成 `https://redfox.hk` 即可。

**Q：抖音技能报 `code=3107 API Key无效`？**
A：Key 是假的或已过期。去 <https://redfox.hk/settings/api-keys?source=qoder> 重新申请。
