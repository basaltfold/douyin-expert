/**
 * 抖音专家 (douyin-expert) — DSH 宿主插件
 * Copyright (C) 2026 basaltfold
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

/**
 * 抖音专家 — Host 半区。
 *
 * 把 assets/ 下 22 个抖音/多平台/海外技能注册进 DSH 技能注册表。
 * 技能源文件来自 Qoder 市场的 5 个插件（抖音爆款内容制造机、抖音内容灵感专家、
 * 抖音增长黑客、多平台AI信息源、海外内容创作专家），去重整合而成。
 *
 * 本插件只做三件事：
 *   1. 读 SKILL.md 的 YAML frontmatter 取 name / description；
 *   2. 以 directory 形态的 resourceBase 暴露整个技能目录（scripts/ references/ 原样可读）；
 *   3. 在技能正文末尾追加「运行时说明」——本机 Python 绝对路径、依赖、凭据要求。
 *
 * 不 import 任何 @deepseek-ai/* 包，避免 profile 侧模块解析失败。
 */

import { existsSync, readFileSync, statSync } from 'node:fs';
import { readFile } from 'node:fs/promises';
import { join, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

/** 插件在 Cordis 里的身份。 */
export const name = 'douyin-expert';

/** 依赖的技能注册表服务。 */
export const inject = ['skills'];

/** 与 dsh-skill 的 BUNDLED_SKILL_RANK 同值；不 import 该包。 */
const BUNDLED_SKILL_RANK = 600;

/** 需要 redfox 数据服务的技能（19 个）。 */
const REDFOX_SKILLS = new Set([
  'bili-ai-feed',
  'douyin-account-diagnosis',
  'douyin-ai-feed',
  'douyin-content-surge',
  'douyin-daily-hot',
  'douyin-hot-trend',
  'douyin-prohibited-word',
  'douyin-rise-ranking',
  'douyin-search',
  'douyin-similar-account',
  'douyin-top-account',
  'douyin-video-downloader',
  'douyin-weekly-surge',
  'douyin-works-crawler',
  'gzh-ai-feed',
  'ks-ai-feed',
  'wechat-channels-ai-feed',
  'xiaohongshu-ai-feed',
]);

/** 纯本地技能（不联网）。 */
const LOCAL_SKILLS = new Set(['multi-copywrite-alchemy']);

/** 海外技能（已改为开源实现：yt-dlp / 直连公开接口）。 */
const OVERSEAS_SKILLS = new Set([
  'overseas-trending-search',
  'twitter-work-search',
  'youtube-digest',
]);

/** 22 个技能名 = assets 下的目录名，扁平。 */
const SKILL_NAMES = [
  'bili-ai-feed',
  'douyin-account-diagnosis',
  'douyin-ai-feed',
  'douyin-content-surge',
  'douyin-daily-hot',
  'douyin-hot-trend',
  'douyin-prohibited-word',
  'douyin-rise-ranking',
  'douyin-search',
  'douyin-similar-account',
  'douyin-top-account',
  'douyin-video-downloader',
  'douyin-weekly-surge',
  'douyin-works-crawler',
  'gzh-ai-feed',
  'ks-ai-feed',
  'multi-copywrite-alchemy',
  'overseas-trending-search',
  'twitter-work-search',
  'wechat-channels-ai-feed',
  'xiaohongshu-ai-feed',
  'youtube-digest',
];

/** 候选 Python 解释器（按序取第一个存在的）。 */
function resolvePython(configured) {
  if (typeof configured === 'string' && configured.length > 0) return configured;
  if (typeof process.env.DOUYIN_EXPERT_PYTHON === 'string' && process.env.DOUYIN_EXPERT_PYTHON.length > 0) {
    return process.env.DOUYIN_EXPERT_PYTHON;
  }
  const home = process.env.USERPROFILE ?? process.env.HOME ?? '';
  const candidates = [
    join(home, '.dsh', 'dsh-runtimes', 'dsh-primary-runtime', 'dependencies', 'python', 'python.exe'),
    join(home, '.dsh', 'dsh-runtimes', 'dsh-primary-runtime', 'dependencies', 'python', 'bin', 'python3'),
  ];
  for (const candidate of candidates) {
    try {
      if (statSync(candidate).isFile()) return candidate;
    } catch {
      /* 下一个候选 */
    }
  }
  return 'python';
}

/** 逐个技能解析 frontmatter（只确认有 description，不做业务校验）。 */
function parseSkill(raw, path) {
  const frontmatter = /^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/u.exec(raw);
  if (frontmatter === null) throw new Error(`douyin-expert: ${path} 缺少 YAML frontmatter`);
  const block = frontmatter[1];
  const match = /^description:\s*(.*)$/mu.exec(block);
  if (match === null || match[1].trim().length === 0) {
    throw new Error(`douyin-expert: ${path} 缺少 description`);
  }
  let description = match[1].trim();
  if (
    (description.startsWith('"') && description.endsWith('"')) ||
    (description.startsWith("'") && description.endsWith("'"))
  ) {
    description = description.slice(1, -1);
  }
  return { description, content: raw.slice(frontmatter[0].length).trim() };
}

/** redfox 数据服务技能的运行时说明。 */
function redfoxBlock(python) {
  return `

## 运行时（本机已就绪）

下面这些是本机实测可用的绝对路径与环境要求。执行本技能的 \`scripts/*.py\` 时一律用下面的解释器，
不要用系统 \`python\` / \`python3\`（本机 PATH 上是 Microsoft Store 存根，会直接失败）。

\`\`\`json
{
  "python": ${JSON.stringify(python)},
  "packages": ["requests", "beautifulsoup4", "python-docx"],
  "apiKeyEnv": "REDFOX_API_KEY",
  "apiBaseEnv": "REDFOX_API_BASE",
  "defaultApiBase": "https://redfox.hk"
}
\`\`\`

- 调用形态：\`"<上面的 python 路径>" scripts/xxx.py --help\`（路径含空格或中文时务必加引号）。
- 所有数据接口走 \`https://redfox.hk\`，需要两个环境变量：
  - \`REDFOX_API_BASE=https://redfox.hk\`（脚本不内置默认值，不设会报 \`Invalid URL ... No scheme supplied\`）
  - \`REDFOX_API_KEY=ak_xxxxxxxx\`（Key 在 https://redfox.hk/settings/api-keys?source=qoder 申请）
- **未配置 Key 时脚本会返回明确的鉴权错误（如 \`未找到 REDFOX_API_KEY\` 或 \`code=3107 API Key无效\`）。
  这属于预期行为，不要伪造数据，直接把错误如实告诉用户并引导去申请 Key。**

## 网络与浏览器增强能力（本机可用）

需要抓取页面 / 渲染 SPA / 处理登录态时，不要自己拼 urllib，直接用本工作区已有的浏览器能力：
- 技能 \`browser-automation\`（Playwright / OpenReverse 统一入口）
- 技能 \`browser-skill\`（已登录 Chromium 的 bsk_* 工具）

爬取类技能（works-crawler / search / top-account / similar-account）在上游接口不可用时，
可改用上述浏览器能力取数，但必须在输出里注明数据来源与获取方式。`;
}

/** 纯本地技能的运行时说明。 */
function localBlock(python) {
  return `

## 运行时（本机已就绪）

本技能纯本地运行，不联网、不需要任何 API Key。

\`\`\`json
{
  "python": ${JSON.stringify(python)},
  "packages": ["requests", "beautifulsoup4"],
  "network": false,
  "apiKeyEnv": null
}
\`\`\`

- 技能正文引用的 \`references/*.md\`（七维分析框架、写作公式、人格模板、核心工作流）都是纯 markdown，
  直接用 read 工具读取即可，不需要跑脚本。
- 需要解析成品文案时，可用 \`"<上面的 python 路径>"\` 执行技能内脚本。`;
}

/** 海外技能的运行时说明（已改为开源实现）。 */
function overseasBlock(python) {
  return `

## 运行时（本机已就绪 · 开源实现版）

本技能的取数逻辑**已从原付费转售 API 改为开源实现**，不再需要 \`DATA_API_KEY\` / \`DATA_API_BASE\`。

\`\`\`json
{
  "python": ${JSON.stringify(python)},
  "packages": ["yt-dlp"],
  "apiKeyEnv": null,
  "network": true
}
\`\`\`

- **YouTube**：用 \`yt-dlp\` 提取字幕/元数据。本机若未装，先执行一次
  \`"<上面的 python 路径>" -m pip install -U yt-dlp\`（DSH 运行时目录可写）。
- **X/Twitter**：走公开的 syndication 接口（\`syndication.twitter.com\`）与 \`snscrape\` 风格查询，
  适合取公开推文；受平台风控影响，高频调用可能返回空结果，属于预期，不要伪造。
- **TikTok**：用 \`yt-dlp\` 的 TikTok extractor 取视频元数据与直链。
- 所有抓取都受平台速率限制；单次任务建议控制在 50 条以内，失败时如实报告，不要重试到被封。
- 抓不到数据时如实说明「目标平台限制/风控」，**不要编造播放量、点赞数或字幕内容**。`;
}

/** 按技能类型选择运行时块。 */
function runtimeBlock(python, skillName) {
  if (OVERSEAS_SKILLS.has(skillName)) return overseasBlock(python);
  if (LOCAL_SKILLS.has(skillName)) return localBlock(python);
  if (REDFOX_SKILLS.has(skillName)) return redfoxBlock(python);
  return redfoxBlock(python);
}

/**
 * 注册 22 个技能。
 * @param ctx Cordis 上下文，需带 skills 服务。
 * @param config 可选 { assetRoot, python }。
 */
export function apply(ctx, config = {}) {
  const assetRoot = config.assetRoot ?? fileURLToPath(new URL('../assets/', import.meta.url));
  if (!existsSync(assetRoot)) throw new Error(`douyin-expert: 资产目录不存在: ${assetRoot}`);
  const python = resolvePython(config.python);

  const candidates = SKILL_NAMES.map((skillName) => {
    const directory = join(assetRoot, skillName);
    const path = join(directory, 'SKILL.md');
    if (!existsSync(path)) throw new Error(`douyin-expert: 技能文件不存在: ${path}`);
    const { description } = parseSkill(readFileSync(path, 'utf8'), path);
    return {
      name: skillName,
      description,
      invocation: { modelInvocable: true, userInvocable: true },
      provider: 'dsh-douyin-expert',
      source: 'bundled',
      rank: BUNDLED_SKILL_RANK,
      resourceBase: { kind: 'directory', path: directory.split(sep).join('/') },
      locator: path,
    };
  });

  const provider = {
    name: 'dsh-douyin-expert',
    list: () => Promise.resolve(candidates),
    async get(candidate, options) {
      const { rank: _rank, locator, ...summary } = candidate;
      const raw = await readFile(locator, { encoding: 'utf8', signal: options.signal });
      return {
        ...summary,
        content: parseSkill(raw, locator).content + runtimeBlock(python, summary.name),
      };
    },
  };

  ctx.skills.registerProvider(() => provider);
}
