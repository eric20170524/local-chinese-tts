$ROOT = $PSScriptRoot
$PID_FILE = "$ROOT\local_tts.pid"

if (Test-Path "$PID_FILE") {
    $pidNum = (Get-Content "$PID_FILE" -ErrorAction SilentlyContinue).Trim()
    if ($pidNum -and (Get-Process -Id $pidNum -ErrorAction SilentlyContinue)) {
        Stop-Process -Id $pidNum -Force -ErrorAction SilentlyContinue
        Write-Host "已停止本地 TTS（PID $pidNum）。"
    } else {
        Write-Host "本地 TTS 进程未在运行。"
    }
    Remove-Item "$PID_FILE" -Force -ErrorAction SilentlyContinue
} else {
    Write-Host "没有找到由启动脚本记录的 TTS 进程。"
}
