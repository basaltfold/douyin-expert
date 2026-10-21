# 抖音专家 (douyin-expert) — 从 DSH desktop profile 卸载
#
# 回滚 install.ps1 的三处改动并删除 junction。可用 -Restore <时间戳> 直接还原备份。

[CmdletBinding()]
param(
  [string]$Profile = (Join-Path $env:USERPROFILE '.dsh\profiles\desktop'),
  [string]$Restore = ''
)

$ErrorActionPreference = 'Stop'
$pkgName = 'douyin-expert'
$pkgFile = Join-Path $Profile 'package.json'
$target  = Join-Path $Profile "node_modules\$pkgName"

if ($Restore) {
  $bak = "$pkgFile.dyexbak-$Restore"
  if (-not (Test-Path $bak)) { throw "备份不存在: $bak" }
  Copy-Item $bak $pkgFile -Force
  Write-Host "已从 $bak 还原 package.json"
} else {
  $json = Get-Content $pkgFile -Raw -Encoding UTF8 | ConvertFrom-Json
  $deps = [ordered]@{}
  foreach ($p in $json.dependencies.PSObject.Properties) {
    if ($p.Name -ne $pkgName) { $deps[$p.Name] = $p.Value }
  }
  $json.dependencies = [pscustomobject]$deps
  $json.dsh.profile.bundles = @($json.dsh.profile.bundles | Where-Object { $_ -ne $pkgName })
  $json | ConvertTo-Json -Depth 32 | Set-Content $pkgFile -Encoding UTF8
  Write-Host '已从 dependencies / bundles 移除'
}

if (Test-Path $target) {
  $item = Get-Item $target -Force
  if ($item.LinkType) { Remove-Item $target -Force; Write-Host "已删除链接: $target" }
  else { Write-Warning "不是链接，未删除: $target" }
}

Write-Host '卸载完成。重启 DeepSeek Harness 生效。'
