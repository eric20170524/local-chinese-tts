#!/bin/bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$ROOT/local_tts.pid"

if [[ -f "$PID_FILE" ]]; then
  pid="$(cat "$PID_FILE")"
  if kill -0 "$pid" 2>/dev/null; then
    kill "$pid"
    printf '已停止本地 TTS（PID %s）。\n' "$pid"
  fi
  rm -f "$PID_FILE"
else
  printf '没有找到由启动脚本记录的 TTS 进程。\n'
fi

