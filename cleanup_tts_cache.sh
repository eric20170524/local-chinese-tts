#!/bin/bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CACHE_DIR="$ROOT/cache"
RETENTION_DAYS=3
DRY_RUN=0
QUIET=0

usage() {
  printf '用法：%s [--dry-run] [--days 天数] [--quiet]\n' "$(basename "$0")"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      ;;
    --days)
      shift
      [[ $# -gt 0 && "$1" =~ ^[1-9][0-9]*$ ]] || {
        printf '--days 需要正整数。\n' >&2
        exit 2
      }
      RETENTION_DAYS="$1"
      ;;
    --quiet)
      QUIET=1
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      exit 2
      ;;
  esac
  shift
done

mkdir -p "$CACHE_DIR"

# find 的 +N 表示“超过 N 个完整 24 小时”；保留 3 天因此使用 +2。
FIND_AGE=$((RETENTION_DAYS - 1))
FILES=()
FILE_COUNT=0
while IFS= read -r -d '' file; do
  FILES["$FILE_COUNT"]="$file"
  FILE_COUNT=$((FILE_COUNT + 1))
done < <(/usr/bin/find "$CACHE_DIR" -type f -mtime "+$FIND_AGE" -print0)

if (( DRY_RUN )); then
  for ((index = 0; index < FILE_COUNT; index++)); do
    printf '%s\n' "${FILES[$index]}"
  done
  printf '将清理 %d 个超过 %d 天的缓存文件。\n' "$FILE_COUNT" "$RETENTION_DAYS"
  exit 0
fi

for ((index = 0; index < FILE_COUNT; index++)); do
  /bin/rm -f -- "${FILES[$index]}"
done

if (( ! QUIET )); then
  printf '已清理 %d 个超过 %d 天的 TTS 缓存文件。\n' "$FILE_COUNT" "$RETENTION_DAYS"
fi
