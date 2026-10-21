# 抖音专家 (douyin-expert) — 安装到 DSH desktop profile
#
# 做三件事（都带备份，可 uninstall.ps1 回滚）：
#   1. 在 profile/node_modules 下建立指向本仓库的目录联接（junction）
#   2. profile/package.json: dependencies 加 "douyin-expert"
#   3. profile/package.json: dsh.profile.bundles 末尾加 "douyin-expert"
#
# 跑完需要重启 DeepSeek Harness 才会加载。

[CmdletBinding()]
param(
  [string]$Profile = (Join-Path $env:USERPROFILE '.dsh\profiles\desktop'),
  [string]$Source  = $PSScriptRoot,
  [switch]$WithOverseasDeps
)

$ErrorActionPreference = 'Stop'
$pkgName = 'douyin-expert'

if (-not (Test-Path $Profile))              { throw "profile 不存在: $Profile" }
if (-not (Test-Path (Join-Path $Source 'package.json'))) { throw "源目录不像插件包: $Source" }

$pkgFile   = Join-Path $Profile 'package.json'
$patchFile = Join-Path $Profile 'cordis.patch.yml'
$target    = Join-Path $Profile "node_modules\$pkgName"
$stamp     = Get-Date -Format 'yyyyMMdd-HHmmss'

# 0. 备份
Copy-Item $pkgFile "$pkgFile.dyexbak-$stamp" -Force
if (Test-Path $patchFile) { Copy-Item $patchFile "$patchFile.dyexbak-$stamp" -Force }
Write-Host "[1/6] 已备份 profile 配置 (后缀 .dyexbak-$stamp)"

# 1. node_modules 链接
if (Test-Path $target) {
  $item = Get-Item $target -Force
  if ($item.LinkType) { Remove-Item $target -Force }
  else { throw "目标已存在且不是链接，请先手动处理: $target" }
}
New-Item -ItemType Junction -Path $target -Target $Source | Out-Null
Write-Host "[2/6] 已建立链接: $target -> $Source"

# 2/3. package.json: dependencies + bundles
$json = Get-Content $pkgFile -Raw -Encoding UTF8 | ConvertFrom-Json
$deps = [ordered]@{}
foreach ($p in $json.dependencies.PSObject.Properties) { $deps[$p.Name] = $p.Value }
$deps[$pkgName] = "file:$($Source -replace '\\','/')"
$json.dependencies = [pscustomobject]$deps

$bundles = @($json.dsh.profile.bundles)
if ($bundles -notcontains $pkgName) { $bundles += $pkgName }
$json.dsh.profile.bundles = $bundles

$json | ConvertTo-Json -Depth 32 | Set-Content $pkgFile -Encoding UTF8
Write-Host "[3/6] dependencies 已写入 $pkgName"
Write-Host "[4/6] bundles 已写入 $pkgName (共 $($bundles.Count) 项)"

# 4. cordis.patch.yml 兜底：如果 bundles 机制没生效，手动补一行 insert
$patchText = if (Test-Path $patchFile) { Get-Content $patchFile -Raw -Encoding UTF8 } else { '' }
if ($patchText -notmatch [regex]::Escape($pkgName)) {
  $block = @"

# 抖音专家（bundle 层未生效时的手动兜底）
- insert:
    - id: $pkgName
      name: '$pkgName'
"@
  Add-Content -Path $patchFile -Value $block -Encoding UTF8
  Write-Host "[5/6] cordis.patch.yml 已追加 insert 行"
} else {
  Write-Host "[5/6] cordis.patch.yml 已含 $pkgName，跳过"
}

# 5. 海外技能的可选依赖（yt-dlp）
if ($WithOverseasDeps) {
  $py = Join-Path $env:USERPROFILE '.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe'
  if (-not (Test-Path $py)) { throw "找不到 DSH 运行时 Python: $py" }
  Write-Host "[6/6] 安装海外技能依赖 yt-dlp ..."
  & $py -m pip install -U yt-dlp
  if ($LASTEXITCODE -ne 0) { throw "yt-dlp 安装失败（exit $LASTEXITCODE）" }
} else {
  Write-Host "[6/6] 跳过海外依赖安装（如需 YouTube / TikTok 能力，重新执行时加 -WithOverseasDeps）"
}

Write-Host ''
Write-Host '安装完成。重启 DeepSeek Harness 后，技能目录里会出现 22 个技能：'
Write-Host '  抖音类 : douyin-daily-hot / douyin-hot-trend / douyin-content-surge / douyin-weekly-surge'
Write-Host '           douyin-search / douyin-works-crawler / douyin-top-account / douyin-rise-ranking'
Write-Host '           douyin-similar-account / douyin-account-diagnosis / douyin-video-downloader'
Write-Host '           douyin-ai-feed / douyin-prohibited-word / multi-copywrite-alchemy'
Write-Host '  多平台 : bili-ai-feed / gzh-ai-feed / ks-ai-feed / wechat-channels-ai-feed / xiaohongshu-ai-feed'
Write-Host '  海外   : overseas-trending-search / twitter-work-search / youtube-digest'
Write-Host ''
Write-Host '自检： node scripts/selftest.mjs'
