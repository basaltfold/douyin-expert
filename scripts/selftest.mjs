#!/usr/bin/env node
/**
 * 抖音专家 (douyin-expert) — 自检脚本
 *
 * 不依赖 DSH 进程，直接以假 ctx 加载 lib/index.js，
 * 校验 22 个技能能被 list/get、frontmatter 可解析、正文能取到、运行时块按类型注入。
 *
 * 用法： node scripts/selftest.mjs
 *        REQUIRE_PYTHON=1 node scripts/selftest.mjs   # 本机验收：python 路径必须存在
 */

const root = new URL('../', import.meta.url);
const entry = new URL('./lib/index.js', root);

const mod = await import(entry.href);

const checks = [];
const fail = (msg) => checks.push(['FAIL', msg]);
const ok = (msg) => checks.push(['ok', msg]);

/** 期望的 22 个技能名（与 lib/index.js 的 SKILL_NAMES 保持一致）。 */
const EXPECTED = [
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

if (mod.name !== 'douyin-expert') fail(`插件名应为 douyin-expert，实为 ${mod.name}`);
else ok('插件名 douyin-expert');

if (!Array.isArray(mod.inject) || !mod.inject.includes('skills')) fail('inject 必须包含 skills');
else ok(`inject = ${JSON.stringify(mod.inject)}`);

if (typeof mod.apply !== 'function') fail('缺少 apply()');

let registered = null;
const ctx = {
  skills: {
    registerProvider(factory) {
      registered = factory({ signal: new AbortController().signal, invalidate() {} });
      return () => {};
    },
  },
};

mod.apply(ctx, {});
if (registered === null) fail('apply() 未调用 skills.registerProvider()');
else ok(`已注册 provider "${registered.name}"`);

const list = await registered.list();
if (list.length !== EXPECTED.length) fail(`技能数应为 ${EXPECTED.length}，实为 ${list.length}`);
else ok(`技能数 ${list.length}`);

const names = list.map((s) => s.name).sort();
const missing = EXPECTED.filter((n) => !names.includes(n));
const extra = names.filter((n) => !EXPECTED.includes(n));
if (missing.length > 0) fail(`缺少技能: ${missing.join(', ')}`);
if (extra.length > 0) fail(`多出技能: ${extra.join(', ')}`);
const dupes = names.filter((n, i) => names.indexOf(n) !== i);
if (dupes.length > 0) fail(`技能名重复: ${dupes.join(', ')}`);
if (missing.length === 0 && extra.length === 0 && dupes.length === 0) {
  ok(`${EXPECTED.length} 个技能名与预期完全一致且唯一`);
}

/** 运行时块的分支判定。 */
const REDFOX = new Set([
  'bili-ai-feed', 'douyin-account-diagnosis', 'douyin-ai-feed', 'douyin-content-surge',
  'douyin-daily-hot', 'douyin-hot-trend', 'douyin-prohibited-word', 'douyin-rise-ranking',
  'douyin-search', 'douyin-similar-account', 'douyin-top-account', 'douyin-video-downloader',
  'douyin-weekly-surge', 'douyin-works-crawler', 'gzh-ai-feed', 'ks-ai-feed',
  'wechat-channels-ai-feed', 'xiaohongshu-ai-feed',
]);
const LOCAL = new Set(['multi-copywrite-alchemy']);
const OVERSEAS = new Set(['overseas-trending-search', 'twitter-work-search', 'youtube-digest']);

let pyPath = null;
for (const candidate of list) {
  const skill = await registered.get(candidate, {});
  const n = skill.name;

  if (!skill.description || skill.description.length < 8) fail(`${n} description 过短`);
  if (!skill.content || skill.content.length < 50) fail(`${n} content 过短（${skill.content?.length}）`);
  if (!skill.content.includes('## 运行时')) fail(`${n} 未注入运行时块`);
  if (skill.provider !== 'dsh-douyin-expert') fail(`${n} provider 不符: ${skill.provider}`);
  if (skill.resourceBase?.kind !== 'directory') fail(`${n} resourceBase 应为 directory`);
  if (!skill.resourceBase.path.includes('assets')) fail(`${n} resourceBase 未指向 assets`);

  const { statSync } = await import('node:fs');
  try {
    if (!statSync(skill.resourceBase.path).isDirectory()) fail(`${n} resourceBase 目录不存在`);
  } catch {
    fail(`${n} resourceBase 目录不可访问: ${skill.resourceBase.path}`);
  }

  // 运行时块必须与该技能类型匹配
  if (REDFOX.has(n) && !skill.content.includes('REDFOX_API_KEY')) {
    fail(`${n} 属于 redfox 类型但运行时块缺 REDFOX_API_KEY`);
  }
  if (LOCAL.has(n) && !skill.content.includes('不联网')) {
    fail(`${n} 属于本地类型但运行时块未声明不联网`);
  }
  if (OVERSEAS.has(n) && !skill.content.includes('开源实现')) {
    fail(`${n} 属于海外类型但运行时块未声明开源实现`);
  }
  // 海外技能不得把 DATA_API_KEY 当作「必需项」；仅允许出现在「不再需要」这类说明里
  if (OVERSEAS.has(n)) {
    const asRequirement =
      /"apiKeyEnv":\s*"DATA_API_KEY"/.test(skill.content) ||
      /export DATA_API_KEY=/.test(skill.content) ||
      /设置环境变量 `?DATA_API_KEY`?[（(]/.test(skill.content);
    if (asRequirement) fail(`${n} 运行时块仍把 DATA_API_KEY 列为必需凭据`);
    if (!/"apiKeyEnv":\s*null/.test(skill.content) && !/X_BEARER_TOKEN/.test(skill.content)) {
      fail(`${n} 运行时块既未声明 apiKeyEnv 为 null，也未提 X_BEARER_TOKEN`);
    }
  }

  // 摘要字段必须是可序列化纯数据
  const summary = { ...skill };
  delete summary.content;
  JSON.stringify(summary);

  if (pyPath === null) {
    const m = /"python":\s*"([^"]+)"/.exec(skill.content);
    if (m) pyPath = m[1];
  }
}

if (pyPath === null) fail('运行时块里没有 python 路径');
else {
  const { existsSync } = await import('node:fs');
  const exists = existsSync(pyPath);
  // 该路径是「本机 DSH 运行时」的绝对路径，CI runner 上必然不存在。
  if (exists) ok(`python 路径存在: ${pyPath}`);
  else if (process.env.REQUIRE_PYTHON === '1') fail(`python 路径不存在: ${pyPath}`);
  else console.log(`SKIP  python 路径在非本机环境不存在（CI 正常）: ${pyPath}`);
}

const failed = checks.filter(([state]) => state === 'FAIL');
for (const [state, msg] of checks) console.log(`${state === 'ok' ? ' OK ' : 'FAIL'}  ${msg}`);
console.log(`\n${failed.length === 0 ? 'PASS' : 'FAILED'} — ${checks.length - failed.length}/${checks.length}`);
process.exit(failed.length === 0 ? 0 : 1);
