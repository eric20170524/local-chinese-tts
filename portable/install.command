#!/bin/bash

set -euo pipefail

PACKAGE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_SOURCE="$PACKAGE_ROOT/app"
SKILL_SOURCE="$PACKAGE_ROOT/skill/local-chinese-tts"
APP_TARGET="${LOCAL_CHINESE_TTS_HOME:-$HOME/.local-chinese-tts}"
SKILL_TARGET="$HOME/.codex/skills/local-chinese-tts"

if [[ "$(uname -s)" != "Darwin" || "$(uname -m)" != "arm64" ]]; then
  printf '此安装包仅支持 Apple Silicon（M 系列）macOS。\n' >&2
  exit 1
fi

[[ -d "$APP_SOURCE" && -d "$SKILL_SOURCE" ]] || {
  printf '安装包结构不完整。请先完整解压后再运行。\n' >&2
  exit 1
}

mkdir -p "$(dirname "$APP_TARGET")" "$HOME/.codex/skills"
/usr/bin/ditto "$APP_SOURCE" "$APP_TARGET"
/usr/bin/ditto "$SKILL_SOURCE" "$SKILL_TARGET"
chmod +x "$APP_TARGET"/*.sh "$APP_TARGET"/*.command "$APP_TARGET"/*.py "$SKILL_TARGET/scripts"/*.sh

PYTHON="$APP_TARGET/.venv/bin/python"
if ! "$PYTHON" -c 'import edge_tts, aiohttp, mlx_audio, misaki, transformers; assert transformers.__version__ == "5.5.0"' 2>/dev/null; then
  for candidate in /opt/homebrew/opt/python@3.12/bin/python3.12 /opt/homebrew/bin/python3 /usr/local/bin/python3; do
    [[ -x "$candidate" ]] || continue
    if "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
      PYTHON="$candidate"
      break
    fi
  done
  "$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null || {
    printf '需要 Python 3.10+。建议安装 Homebrew Python 3.12 后重新运行。\n' >&2
    exit 1
  }
  if [[ -d "$APP_TARGET/.venv" ]]; then
    mv "$APP_TARGET/.venv" "$APP_TARGET/.venv.incompatible.$(date +%Y%m%d%H%M%S)"
  fi
  "$PYTHON" -m venv "$APP_TARGET/.venv"
  "$APP_TARGET/.venv/bin/python" -m pip install --disable-pip-version-check -r "$APP_TARGET/requirements.txt"
fi

"$APP_TARGET/install_local_tts.sh"
/usr/bin/curl -fsS -H 'Content-Type: application/json' -d '{"voice":"K01"}' http://127.0.0.1:8765/api/settings >/dev/null

printf '\n安装成功。\n'
printf '控制面板：http://127.0.0.1:8765/\n'
printf '本体目录：%s\n' "$APP_TARGET"
printf '全局技能：%s\n' "$SKILL_TARGET"
/usr/bin/open http://127.0.0.1:8765/

