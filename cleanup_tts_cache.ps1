param (
    [switch]$DryRun,
    [int]$Days = 3,
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"
$ROOT = $PSScriptRoot
$CACHE_DIR = "$ROOT\cache"

if (!(Test-Path "$CACHE_DIR")) {
    New-Item -ItemType Directory -Path "$CACHE_DIR" | Out-Null
}

$cutoff = (Get-Date).AddDays(-$Days)
$filesToDelete = Get-ChildItem -Path "$CACHE_DIR" -File | Where-Object { $_.LastWriteTime -lt $cutoff }

if ($DryRun) {
    foreach ($file in $filesToDelete) {
        Write-Host $file.FullName
    }
    Write-Host "将清理 $($filesToDelete.Count) 个超过 $Days 天的缓存文件。"
    exit 0
}

$count = 0
foreach ($file in $filesToDelete) {
    Remove-Item $file.FullName -Force -ErrorAction SilentlyContinue
    $count++
}

if (-not $Quiet) {
    Write-Host "已清理 $count 个超过 $Days 天的 TTS 缓存文件。"
}
