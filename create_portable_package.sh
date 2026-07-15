#!/bin/bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RELEASE_ROOT="$ROOT/release"
STAMP="$(date +%Y%m%d-%H%M%S)"
PACKAGE_NAME="LocalChineseTTS-Portable-macos-arm64-$STAMP"
STAGE="$RELEASE_ROOT/$PACKAGE_NAME"
ARCHIVE="$RELEASE_ROOT/$PACKAGE_NAME.zip"
SKILL_SOURCE="$HOME/.codex/skills/local-chinese-tts"

[[ -d "$SKILL_SOURCE" ]] || {
  printf '未找到全局技能：%s\n' "$SKILL_SOURCE" >&2
  exit 1
}
[[ -f "$ROOT/models/status.json" ]] || {
  printf '未找到本地模型状态。请先下载模型后再打包。\n' >&2
  exit 1
}

mkdir -p "$STAGE/app" "$STAGE/skill"

for entry in \
  .venv \
  launchagent \
  models \
  patches \
  portable \
  service \
  web \
  .gitignore \
  README.md \
  requirements.txt \
  local_tts.py \
  local_mlx_worker.py \
  download_local_models.py \
  cleanup_tts_cache.sh \
  generate_voice_pack.sh \
  install_local_tts.sh \
  install_to_macos.sh \
  start_local_tts.sh \
  stop_local_tts.sh \
  tts.sh \
  打开本机TTS.command; do
  /bin/cp -cR "$ROOT/$entry" "$STAGE/app/"
done

/usr/bin/rsync -a --exclude='.DS_Store' --exclude='__MACOSX' \
  "$SKILL_SOURCE/" "$STAGE/skill/local-chinese-tts/"
/bin/cp "$ROOT/portable/install.command" "$STAGE/install.command"
/bin/cp "$ROOT/portable/INSTALL.md" "$STAGE/INSTALL.md"
chmod +x "$STAGE/install.command"

/usr/bin/ditto -c -k --keepParent "$STAGE" "$ARCHIVE"
LC_ALL=C /usr/bin/shasum -a 256 "$ARCHIVE" > "$ARCHIVE.sha256"

printf '便携目录：%s\n' "$STAGE"
printf '安装包：%s\n' "$ARCHIVE"
printf 'SHA-256：%s\n' "$ARCHIVE.sha256"
