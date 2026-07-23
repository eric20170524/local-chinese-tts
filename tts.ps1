$ROOT = $PSScriptRoot
$PYTHON = "$ROOT\.venv\Scripts\python.exe"
if (!(Test-Path "$PYTHON")) {
    $PYTHON = "python"
}
& "$PYTHON" "$ROOT\local_tts.py" @args
