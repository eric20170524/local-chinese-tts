$ErrorActionPreference = "Stop"
$ROOT = $PSScriptRoot
$PYTHON = "$ROOT\.venv\Scripts\python.exe"

Write-Host "========== 开始安装 Local Chinese TTS =========="
if (!(Test-Path "$ROOT\logs")) { New-Item -ItemType Directory -Path "$ROOT\logs" | Out-Null }
if (!(Test-Path "$ROOT\cache")) { New-Item -ItemType Directory -Path "$ROOT\cache" | Out-Null }

if (!(Test-Path "$PYTHON")) {
    Write-Host "[1/3] 正在创建 Python 虚拟环境..."
    python -m venv "$ROOT\.venv"
}

Write-Host "[2/3] 正在安装依赖包..."
& "$PYTHON" -m pip install --disable-pip-version-check -r "$ROOT\requirements.txt"

Write-Host "[3/3] 正在清理历史缓存..."
if (Test-Path "$ROOT\cleanup_tts_cache.ps1") {
    & "$ROOT\cleanup_tts_cache.ps1" -Quiet
}

Write-Host "正在尝试启动服务..."
& "$ROOT\start_local_tts.ps1"

Write-Host "=============================================="
Write-Host "安装完成！"
Write-Host "控制面板：http://127.0.0.1:8765/"
Write-Host "本机 API：http://127.0.0.1:8765/v1/audio/speech"
Write-Host "=============================================="
