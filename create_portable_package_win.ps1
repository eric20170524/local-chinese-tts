$ErrorActionPreference = "Stop"
$ROOT = $PSScriptRoot
$RELEASE_ROOT = "$ROOT\release"
$STAMP = Get-Date -Format "yyyyMMdd-HHmmss"
$PACKAGE_NAME = "LocalChineseTTS-Portable-windows-x64-$STAMP"
$STAGE = "$RELEASE_ROOT\$PACKAGE_NAME"
$ARCHIVE = "$RELEASE_ROOT\$PACKAGE_NAME.zip"

if (!(Test-Path "$RELEASE_ROOT")) { New-Item -ItemType Directory -Path "$RELEASE_ROOT" | Out-Null }
if (Test-Path "$STAGE") { Remove-Item "$STAGE" -Recurse -Force }

New-Item -ItemType Directory -Path "$STAGE\app" | Out-Null

$entries = @(
    ".venv",
    "models",
    "patches",
    "portable",
    "web",
    ".gitignore",
    "README.md",
    "requirements.txt",
    "local_tts.py",
    "local_mlx_worker.py",
    "local_onnx_worker.py",
    "download_local_models.py",
    "cleanup_tts_cache.ps1",
    "cleanup_tts_cache.bat",
    "install_local_tts.ps1",
    "install_local_tts.bat",
    "start_local_tts.ps1",
    "start_local_tts.bat",
    "stop_local_tts.ps1",
    "stop_local_tts.bat",
    "tts.ps1",
    "tts.bat",
    "打开本机TTS.bat",
    "打开本机TTS.vbs"
)

foreach ($entry in $entries) {
    $src = "$ROOT\$entry"
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination "$STAGE\app\" -Recurse -Force
    }
}

Copy-Item -Path "$ROOT\start_local_tts.bat" -Destination "$STAGE\打开本机TTS.bat" -Force
if (Test-Path "$ROOT\portable\INSTALL.md") {
    Copy-Item -Path "$ROOT\portable\INSTALL.md" -Destination "$STAGE\INSTALL.md" -Force
}

Compress-Archive -Path "$STAGE\*" -DestinationPath "$ARCHIVE" -Force

$hash = (Get-FileHash -Path "$ARCHIVE" -Algorithm SHA256).Hash
"$hash  $(Split-Path $ARCHIVE -Leaf)" | Out-File -FilePath "$ARCHIVE.sha256" -Encoding utf8

Write-Host "便携目录：$STAGE"
Write-Host "安装包：$ARCHIVE"
Write-Host "SHA-256：$hash"
