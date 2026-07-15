#!/bin/bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LABEL="com.local.chinese-tts"
CLEANUP_LABEL="com.local-chinese-tts.cleanup"
DOMAIN="gui/$(id -u)"
LAUNCH_SOURCE="$ROOT/launchagent/$LABEL.plist"
LAUNCH_TARGET="$HOME/Library/LaunchAgents/$LABEL.plist"
CLEANUP_SOURCE="$ROOT/launchagent/$CLEANUP_LABEL.plist"
CLEANUP_TARGET="$HOME/Library/LaunchAgents/$CLEANUP_LABEL.plist"
SERVICE_SOURCE="$ROOT/service/中文音色朗读.workflow"
SERVICE_TARGET="$HOME/Library/Services/中文音色朗读.workflow"
SERVICE_STAGE="$ROOT/.install-stage/中文音色朗读.workflow"
ROOT_FOR_SED="$(printf '%s' "$ROOT" | /usr/bin/sed 's/[&|]/\\&/g')"

mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Services" "$ROOT/logs" "$ROOT/cache" "$SERVICE_STAGE/Contents"
/usr/bin/sed "s|__TTS_ROOT__|$ROOT_FOR_SED|g" "$LAUNCH_SOURCE" > "$LAUNCH_TARGET"
/usr/bin/sed "s|__TTS_ROOT__|$ROOT_FOR_SED|g" "$CLEANUP_SOURCE" > "$CLEANUP_TARGET"
cp "$SERVICE_SOURCE/Contents/Info.plist" "$SERVICE_STAGE/Contents/Info.plist"
/usr/bin/sed "s|__TTS_ROOT__|$ROOT_FOR_SED|g" "$SERVICE_SOURCE/Contents/document.wflow" > "$SERVICE_STAGE/Contents/document.wflow"
/usr/bin/ditto "$SERVICE_STAGE" "$SERVICE_TARGET"

/bin/launchctl bootout "$DOMAIN/$LABEL" 2>/dev/null || true
sleep 0.5
if ! /bin/launchctl bootstrap "$DOMAIN" "$LAUNCH_TARGET"; then
  sleep 1
  /bin/launchctl bootstrap "$DOMAIN" "$LAUNCH_TARGET"
fi
/bin/launchctl enable "$DOMAIN/$LABEL"

/bin/launchctl bootout "$DOMAIN/$CLEANUP_LABEL" 2>/dev/null || true
if ! /bin/launchctl bootstrap "$DOMAIN" "$CLEANUP_TARGET"; then
  sleep 1
  /bin/launchctl bootstrap "$DOMAIN" "$CLEANUP_TARGET"
fi
/bin/launchctl enable "$DOMAIN/$CLEANUP_LABEL"
/bin/bash "$ROOT/cleanup_tts_cache.sh" --quiet

/System/Library/CoreServices/pbs -flush 2>/dev/null || true

for _ in {1..40}; do
  if /usr/bin/curl -fsS http://127.0.0.1:8765/api/health >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done

/usr/bin/curl -fsS http://127.0.0.1:8765/api/health >/dev/null
printf '安装完成。\n'
printf '控制面板：http://127.0.0.1:8765/\n'
printf '本机 API：http://127.0.0.1:8765/v1/audio/speech\n'
printf '选中文字后可从“服务”菜单运行：中文音色朗读\n'
