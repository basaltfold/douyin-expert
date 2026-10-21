# 抖音专家 (douyin-expert)

把 Qoder 上 5 个抖音 / 多平台 / 海外插件的全部能力，去重整合成 **一个 DeepSeek Harness 宿主插件**：
22 个技能、37 个可执行脚本，装好后自动出现在 DSH 技能目录里。

| 来源插件 | 版本 | 贡献技能 |
|---|---|---|
| 抖音爆款内容制造机 | 1.0.0 | 8 个（去重后 6 个独立） |
| 抖音内容灵感专家 | 1.0.0 | 8 个（去重后 4 个独立） |
| 抖音增长黑客 | 1.0.0 | 8 个（去重后 4 个独立） |
| 多平台AI信息源 | 1.0.1 | 6 个 |
| 海外内容创作专家 | 1.0.1 | 3 个（**已改为开源实现**） |

---

## 装了什么

去重后 **22 个技能**（原 33 个技能目录，11 个重名已按「文件最全」原则合并）：

### 抖音核心（13 个）

| 技能 | 干什么 | 需要 Key |
|---|---|---|
| `douyin-daily-hot` | 每日最热作品榜，单日点赞 TOP50 | 是 |
| `douyin-hot-trend` | 实时热榜，每小时更新，支持近 7/30 天 | 是 |
| `douyin-content-surge` | 每日点赞飙升榜 TOP50 | 是 |
| `douyin-weekly-surge` | 七日点赞飙升榜 TOP50 | 是 |
| `douyin-search` | 关键词搜索爆款作品，支持日期范围 | 是 |
| `douyin-works-crawler` | 输入账号名/ID，输出近期作品列表 | 是 |
| `douyin-top-account` | 日/周/月最具影响力账号榜 | 是 |
| `douyin-rise-ranking` | 涨粉账号推荐，日/周/月榜 27 分类 | 是 |
| `douyin-similar-account` | 相似账号推荐，对标分析 | 是 |
| `douyin-account-diagnosis` | 一键诊断账号健康度，四维度打分 | 是 |
| `douyin-video-downloader` | 本人作品下载备份到本地 | 是 |
| `douyin-ai-feed` | 每日扫描抖音 AI 作品，生成 HTML 日报 | 是 |
| `douyin-prohibited-word` | 违禁词检测 + 替换建议 + 改写稿 | 是 |

### 多平台 AI 信息源（5 个）

| 技能 | 平台 |
|---|---|
| `bili-ai-feed` | B 站 |
| `gzh-ai-feed` | 微信公众号 |
| `ks-ai-feed` | 快手 |
| `wechat-channels-ai-feed` | 视频号 |
| `xiaohongshu-ai-feed` | 小红书 |

每个都是「每日扫描 AI 相关内容 → 按互动量筛选 → 聚类 → 生成 HTML 日报」。

### 写作（1 个，纯本地）

| 技能 | 干什么 |
|---|---|
| `multi-copywrite-alchemy` | 复刻蒸馏写作：分析一位作者的多篇文章，还原其思维与文风，生成写作分身 |

**不联网、不需要 Key**，正文引用的四份 markdown 框架（七维分析、写作公式、人格模板、核心工作流）直接读。

### 海外情报（3 个，**已改为开源实现**）

| 技能 | 数据源 | 需要什么 |
|---|---|---|
| `youtube-digest` | yt-dlp 直连 YouTube | 装 `yt-dlp` |
| `twitter-work-search` | X 官方 API v2 / 网页 GraphQL | `X_BEARER_TOKEN` 或 `X_AUTH_TOKEN`+`X_CT0` |
| `overseas-trending-search` | YouTube/TikTok 走 yt-dlp，X 走官方接口 | 同上 |

> **这三个原版依赖 `DATA_API_BASE` 付费转售服务**，本插件把它们全部改成了开源实现：
> - YouTube / TikTok → [yt-dlp](https://github.com/yt-dlp/yt-dlp)（Unlicense，19 万星）
> - X → 官方 API v2（用户自带 Bearer）或网页 GraphQL（用户自带 cookie）
>
> **不再需要 `DATA_API_KEY` / `DATA_API_BASE`。**

---

## 装法

```powershell
cd C:\AI\插件1021\douyin-expert

# 基础安装（22 个技能全部注册）
.\install.ps1

# 顺带装海外技能依赖（yt-dlp）
.\install.ps1 -WithOverseasDeps
```

然后**重启 DeepSeek Harness**。重启后技能目录里会出现 22 个技能。

`install.ps1` 做的事（每步都有备份，`*.dyexbak-<时间戳>`）：

1. `~/.dsh/profiles/desktop/node_modules/` 下建目录联接指向本仓库（改代码即时生效）
2. `profile/package.json` 的 `dependencies` 加 `"douyin-expert": "file:C:/AI/插件1021/douyin-expert"`
3. 同文件 `dsh.profile.bundles` 数组末尾追加 `"douyin-expert"`
4. `cordis.patch.yml` 兜底补一行 `insert`
5. （可选）用 DSH 运行时 Python 装 `yt-dlp`

卸载：

```powershell
.\uninstall.ps1                        # 移除改动 + 删 junction
.\uninstall.ps1 -Restore 20261021-131500   # 或直接还原某次备份
```

---

## 凭据配置

### 抖音 / 多平台类（18 个技能）

需要两个环境变量：

```powershell
[Environment]::SetEnvironmentVariable("REDFOX_API_BASE", "https://redfox.hk", "User")
[Environment]::SetEnvironmentVariable("REDFOX_API_KEY", "ak_xxxxxxxx", "User")
```

Key 申请：<https://redfox.hk/settings/api-keys?source=qoder>（新用户赠免费积分）

设完**重启 DSH**。

> `REDFOX_API_BASE` 现在**有内置默认值 `https://redfox.hk`**（本插件已给 21 处脚本打补丁），
> 所以只设 Key 也能跑。但显式设置更保险，将来换上游时不用改代码。

### 海外类（3 个技能）

见 [`CONNECTORS.md`](./CONNECTORS.md)。要点：

- **YouTube**：`python -m pip install -U yt-dlp`，装完就能用
- **X**：必须配 `X_BEARER_TOKEN` 或 `X_AUTH_TOKEN`+`X_CT0`（X 已关闭未登录搜索）
- **TikTok**：仅支持「视频链接」和「@用户名」，关键词搜索不可用（需要 msTag/X-Bogus 签名）

---

## Python 运行时（重要）

本机 PATH 上的 `python` / `python3` 是 **Microsoft Store 重定向存根**，跑任何脚本都会直接 exit 49。
不要用它。

插件里的脚本一律走 DSH 自带的真 Python（3.12.14）：

```
C:\Users\11781\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe
```

这个路径已经写进每个技能的正文末尾「运行时」区块，模型加载技能时会读到，不会误用系统 python。

调用形态：

```powershell
& "C:\Users\11781\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe" scripts\douyin_daily_hot.py --type 美食
```

脚本输出中文，需 `PYTHONIOENCODING=utf-8`，否则控制台是乱码（不影响输出内容本身）。

已装依赖：`requests` / `beautifulsoup4` / `python-docx` / `yt-dlp`。

---

## 结构

```
douyin-expert/
├── package.json          # DSH 插件清单，dsh.bundle.patch 指向 cordis.patch.yml
├── cordis.patch.yml      # bundle 层：insert 宿主插件
├── lib/index.js          # 宿主逻辑：注册 22 个技能的 provider，按类型注入运行时块
├── assets/
│   ├── douyin-daily-hot/{SKILL.md, README.md, README.en.md, scripts/, references/}
│   ├── ... 共 22 个技能目录
│   └── overseas-trending-search/scripts/sources/{x,tiktok,youtube}_source.py   # 开源实现
├── locale/{zh,en}.json
├── CONNECTORS.md         # 凭据与依赖说明（三类技能分别讲）
├── install.ps1 / uninstall.ps1
├── scripts/selftest.mjs  # 不依赖 DSH 进程的自检
└── .github/workflows/selftest.yml
```

`lib/index.js` 用 `ctx.skills.registerProvider()` 注册一个 provider：

- `list()` 返回 22 个候选
- `get()` 读 `assets/<name>/SKILL.md`，**按技能类型追加不同的运行时区块**：
  - 18 个 redfox 类 → 注入 `REDFOX_API_BASE` / `REDFOX_API_KEY` 说明
  - 1 个本地类 → 声明不联网、无需 Key
  - 3 个海外类 → 声明开源实现、yt-dlp 装法、X 凭据要求
- `resourceBase` 指向技能自己的目录，所以 `references/`、`scripts/` 里的相对路径能正常解析

---

## 海外技能的开源改造说明

原版三个技能都是 `POST {DATA_API_BASE}/...` 的 HTTP 客户端，要求用户自建付费数据服务。
本次改造的实际情况（都实测过）：

| 能力 | 原方案 | 现方案 | 实测结果 |
|---|---|---|---|
| YouTube 搜索 | `POST /youtube/searchVideo` | `yt-dlp ytsearchN:关键词` | ✅ 15 条真实数据，按播放量排序 |
| YouTube 字幕 | `POST /youtube/transcript` | `yt-dlp --write-auto-subs` + json3 解析 | ✅ 248 段带时间戳，zh 429 时自动降级 en |
| TikTok 视频详情 | `POST /tiktok/ability/awemeDetail` | `yt-dlp` 单 URL | ✅ 播放/点赞/评论/时间全有 |
| TikTok 用户作品 | `POST /tiktok/ability/userAwemeList` | `yt-dlp tiktokuser:<secUid>` | ✅ 10 条 |
| TikTok 关键词搜索 | `POST /tiktok/ability/searchVideo` | ❌ 无开源替代 | 明确报不可用（需 msToken/X-Bogus 签名） |
| X 搜索 | `POST /x/search` | 官方 API v2 / 网页 GraphQL | ✅ 有凭据时可用；无凭据明确报错 |

**关键取舍**：拿不到的数据（YouTube 点赞数、TikTok 关键词搜索、无凭据时的 X）一律
**如实标记为不可用或 0**，绝不估算、不伪造。这是这些技能正文里反复强调的纪律。

框架替换：

| 原实现 | 现实现 | 许可证 |
|---|---|---|
| 付费转售 API（无内置基址） | [yt-dlp](https://github.com/yt-dlp/yt-dlp) | Unlicense（公共领域） |
| — | X 官方 API v2（用户自带 Bearer） | X 服务条款 |

### 为什么不用 snscrape / Nitter

调研阶段实测过，全部不可行：

| 方案 | 实测结果 |
|---|---|
| `snscrape` 0.7.0 | `AttributeError: 'FileFinder' object has no attribute 'find_module'` — 与 Python 3.12 不兼容 |
| Nitter 公共实例（11 个） | 全部离线 / SSL 失败 / 403 / 451 / 无内容 |
| X guest token | `403 Forbidden` — X 已关闭匿名 API |
| `TikTokApi`（davidteather） | 需要 playwright + chromium（197MB），且搜索仍受签名限制 |

结论：X 走官方凭据是唯一可靠路径，YouTube/TikTok 走 yt-dlp 是最优解。

---

## 自检

不启动 DSH 也能验：

```powershell
node scripts/selftest.mjs

# 本机验收（要求 python 路径真实存在）
$env:REQUIRE_PYTHON="1"; node scripts/selftest.mjs
```

覆盖：插件名 / inject / apply 是否注册 provider / **技能数 22** / **22 个名字与预期逐一比对** /
无重复 / description 与 content 非空 / **运行时块按技能类型正确注入**（redfox 类必须有
`REDFOX_API_KEY`，本地类必须声明不联网，海外类必须声明开源实现且不得把 `DATA_API_KEY` 当必需项）/
python 路径存在 / resourceBase 是真实目录 / 元数据可 JSON 序列化。

当前结果：**PASS — 6/6**。

---

## 已知边界

1. **无 redfox Key 时，18 个抖音/多平台技能只返回鉴权错误**。这是设计行为，不是 bug。
2. **YouTube 搜索结果的点赞数为 0** —— yt-dlp 列表接口不提供该项，如实显示不估算。
   要真实点赞数请用 `youtube-digest` 取单视频详情。
3. **TikTok 关键词搜索不可用** —— 平台签名限制，仅支持链接与 @用户名。
4. **X 无凭据时不可用** —— 平台限制。
5. **YouTube 字幕可能 429** —— 请求过频触发限流，脚本会自动降级到下一个语言或提示等待。
6. 需要境外网络访问 YouTube / X / TikTok，可能需要代理。
