$ErrorActionPreference = "Stop"
$ROOT = $PSScriptRoot
$PYTHON = "$ROOT\.venv\Scripts\python.exe"
$PYTHONW = "$ROOT\.venv\Scripts\pythonw.exe"
if (!(Test-Path "$PYTHONW")) { $PYTHONW = $PYTHON }
$PID_FILE = "$ROOT\local_tts.pid"
$LOG_FILE = "$ROOT\logs\local_tts.log"
$URL = "http://127.0.0.1:8765/"

if (!(Test-Path "$ROOT\logs")) { New-Item -ItemType Directory -Path "$ROOT\logs" | Out-Null }
if (!(Test-Path "$ROOT\cache")) { New-Item -ItemType Directory -Path "$ROOT\cache" | Out-Null }

if (Test-Path "$ROOT\cleanup_tts_cache.ps1") {
    & "$ROOT\cleanup_tts_cache.ps1" -Quiet
}

if (!(Test-Path "$PYTHON")) {
    Write-Host "正在创建 Python 虚拟环境..."
    python -m venv "$ROOT\.venv"
}

$checkDep = & "$PYTHON" -c "import edge_tts, aiohttp; print('ok')" 2>$null
if ($checkDep -ne "ok") {
    Write-Host "正在安装依赖包..."
    & "$PYTHON" -m pip install --disable-pip-version-check -r "$ROOT\requirements.txt"
}

$alreadyRunning = $false
try {
    $resp = Invoke-RestMethod -Uri "${URL}api/health" -TimeoutSec 2 -ErrorAction Stop
    if ($resp.ok) { $alreadyRunning = $true }
} catch {}

if ($alreadyRunning) {
    Write-Host "本地 TTS 已在运行：$URL"
} else {
    Write-Host "正在启动本地 TTS 服务..."
    $cmdArgs = "/c start `"`" /b `"$PYTHONW`" `"$ROOT\local_tts.py`" serve"
    $proc = Start-Process -FilePath "cmd.exe" -ArgumentList $cmdArgs -WindowStyle Hidden -PassThru
    $proc.Id | Out-File -FilePath "$PID_FILE" -Encoding utf8

    $healthy = $false
    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Milliseconds 250
        try {
            $resp = Invoke-RestMethod -Uri "${URL}api/health" -TimeoutSec 1 -ErrorAction Stop
            if ($resp.ok) {
                $healthy = $true
                break
            }
        } catch {}
    }

    if ($healthy) {
        Write-Host "本地 TTS 已成功启动：$URL"
    } else {
        Write-Host "警告：服务启动后未能及时响应健康检查，请检查日志 $LOG_FILE"
    }
}

if ($env:NO_OPEN -ne "1") {
    Start-Process "$URL"
}
