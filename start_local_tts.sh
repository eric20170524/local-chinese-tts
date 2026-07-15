#!/bin/bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON="$ROOT/.venv/bin/python"
PID_FILE="$ROOT/local_tts.pid"
LOG_FILE="$ROOT/logs/local_tts.log"
URL="http://127.0.0.1:8765/"
CURL="$(command -v curl || true)"
OPEN_CMD="$(command -v open || command -v xdg-open || true)"

mkdir -p "$ROOT/logs" "$ROOT/cache"
/bin/bash "$ROOT/cleanup_tts_cache.sh" --quiet || true

if [[ ! -x "$PYTHON" ]]; then
  python3 -m venv "$ROOT/.venv"
fi

if ! "$PYTHON" -c 'import edge_tts, aiohttp, mlx_audio, misaki, transformers; assert transformers.__version__ == "5.5.0"' 2>/dev/null; then
  "$PYTHON" -m pip install --disable-pip-version-check -r "$ROOT/requirements.txt"
fi

KOKORO_TARGET="$("$PYTHON" - <<'PY'
from pathlib import Path
import mlx_audio
print(Path(mlx_audio.__file__).resolve().parent / "tts" / "models" / "kokoro" / "istftnet.py")
PY
)"
if [[ -f "$KOKORO_TARGET" ]] && ! grep -q 'common_length = min' "$KOKORO_TARGET"; then
  patch "$KOKORO_TARGET" "$ROOT/patches/mlx_audio_kokoro_shape_alignment.patch"
fi

if [[ -z "$CURL" ]]; then
  printf '缺少 curl，无法检查服务状态。\n' >&2
  exit 1
fi

if "$CURL" -fsS "${URL}api/health" >/dev/null 2>&1; then
  printf '本地 TTS 已在运行：%s\n' "$URL"
else
  nohup "$PYTHON" "$ROOT/local_tts.py" serve >>"$LOG_FILE" 2>&1 &
  printf '%s\n' "$!" > "$PID_FILE"
  for _ in {1..40}; do
    if "$CURL" -fsS "${URL}api/health" >/dev/null 2>&1; then
      break
    fi
    sleep 0.25
  done
  "$CURL" -fsS "${URL}api/health" >/dev/null
  printf '本地 TTS 已启动：%s\n' "$URL"
fi

if [[ "${NO_OPEN:-0}" != "1" && -n "$OPEN_CMD" ]]; then
  "$OPEN_CMD" "$URL" >/dev/null 2>&1 || true
fi
