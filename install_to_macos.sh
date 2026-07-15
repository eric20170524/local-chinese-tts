#!/bin/bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$ROOT/outputs/aiff"
TARGET_DIR="$HOME/Library/Sounds"

shopt -s nullglob
files=("$SOURCE_DIR"/*.aiff)
if [[ ${#files[@]} -ne 13 ]]; then
  printf '未找到完整的 13 个 AIFF 文件，请先运行 generate_voice_pack.sh。\n' >&2
  exit 1
fi

mkdir -p "$TARGET_DIR"
cp "${files[@]}" "$TARGET_DIR/"
printf '安装完成：13 个声音已复制到 %s\n' "$TARGET_DIR"
printf '请重新打开“系统设置 > 声音 > 声音效果”查看。\n'

