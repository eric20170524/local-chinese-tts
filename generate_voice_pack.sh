#!/bin/bash

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$ROOT/.venv/bin/python"
FFMPEG="${FFMPEG:-$(command -v ffmpeg || true)}"
FFPROBE="${FFPROBE:-$(command -v ffprobe || true)}"
DEFAULT_TEXT="叮咚，您有一条新消息。"
TEXT="${VOICE_TEXT:-$DEFAULT_TEXT}"
INSTALL=0

usage() {
  printf '用法：%s [--install] [--text "要说的中文"]\n' "$0"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --install)
      INSTALL=1
      shift
      ;;
    --text)
      [[ $# -ge 2 ]] || { usage; exit 2; }
      TEXT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf '未知参数：%s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

[[ -n "$FFMPEG" && -n "$FFPROBE" ]] || {
  printf '缺少 ffmpeg/ffprobe。请先执行：brew install ffmpeg\n' >&2
  exit 1
}

if [[ ! -x "$VENV_PYTHON" ]]; then
  python3 -m venv "$ROOT/.venv"
fi

if ! "$VENV_PYTHON" -c 'import edge_tts' 2>/dev/null; then
  "$VENV_PYTHON" -m pip install --disable-pip-version-check 'edge-tts==7.2.7'
fi

AIFF_DIR="$ROOT/outputs/aiff"
MP3_DIR="$ROOT/outputs/mp3"
MANIFEST="$ROOT/outputs/manifest.tsv"
mkdir -p "$AIFF_DIR" "$MP3_DIR"
rm -f "$AIFF_DIR"/*.aiff "$MP3_DIR"/*.mp3

WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/macos-cn-voice-pack.XXXXXX")"
trap 'rm -rf "$WORK_DIR"' EXIT

printf '编号\t性别\t风格\t显示名\t服务语音\t语速\t音高\t语言\t时长（秒）\t试听文案\n' > "$MANIFEST"

FILTER='silenceremove=start_periods=1:start_duration=0.02:start_threshold=-50dB,highpass=f=70,lowpass=f=11000,loudnorm=I=-17:TP=-1.5:LRA=7,apad=pad_dur=0.12'
count=0

while IFS='|' read -r code gender style display_name voice rate pitch locale; do
  [[ -n "$code" ]] || continue
  stem="CN_${code}_${gender}_${style}_${display_name}"
  raw_file="$WORK_DIR/${code}.mp3"
  aiff_file="$AIFF_DIR/${stem}.aiff"
  mp3_file="$MP3_DIR/${stem}.mp3"

  printf '[%s/13] 正在生成：%s · %s（%s）\n' "$((count + 1))" "$gender" "$style" "$display_name"
  "$VENV_PYTHON" -m edge_tts \
    --voice "$voice" \
    --rate="$rate" \
    --pitch="$pitch" \
    --volume='+0%' \
    --text "$TEXT" \
    --write-media "$raw_file"

  "$FFMPEG" -hide_banner -loglevel error -y \
    -i "$raw_file" -af "$FILTER" \
    -ar 44100 -ac 1 -c:a pcm_s16be "$aiff_file"

  "$FFMPEG" -hide_banner -loglevel error -y \
    -i "$aiff_file" -c:a libmp3lame -q:a 2 "$mp3_file"

  size="$(stat -f '%z' "$aiff_file")"
  if [[ "$size" -lt 10000 ]]; then
    printf '生成失败或声音为空：%s\n' "$aiff_file" >&2
    exit 1
  fi

  duration="$($FFPROBE -v error -show_entries format=duration -of default=nw=1:nk=1 "$aiff_file")"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%.2f\t%s\n' \
    "$code" "$gender" "$style" "$display_name" "$voice" "$rate" "$pitch" "$locale" "$duration" "$TEXT" \
    >> "$MANIFEST"
  count=$((count + 1))
done <<'VOICES'
M01|男声|阳光|云希|zh-CN-YunxiNeural|+3%|+0Hz|普通话
M02|男声|沉稳|云扬|zh-CN-YunyangNeural|-8%|-8Hz|普通话
M03|男声|热血|云健|zh-CN-YunjianNeural|+6%|-2Hz|普通话
F01|女声|可爱|晓伊|zh-CN-XiaoyiNeural|+12%|+18Hz|普通话
F02|女声|活泼|晓伊|zh-CN-XiaoyiNeural|+7%|+7Hz|普通话
F03|女声|御姐|晓晓|zh-CN-XiaoxiaoNeural|-10%|-24Hz|普通话
F04|女声|温柔|晓晓|zh-CN-XiaoxiaoNeural|-8%|-4Hz|普通话
F05|女声|甜美|晓臻|zh-TW-HsiaoChenNeural|+7%|+12Hz|台湾普通话
F06|女声|元气|晓妮|zh-CN-shaanxi-XiaoniNeural|+10%|+14Hz|陕西口音普通话
F07|女声|俏皮|晓北|zh-CN-liaoning-XiaobeiNeural|+9%|+10Hz|东北口音普通话
F08|女声|清新|晓雨|zh-TW-HsiaoYuNeural|+4%|+8Hz|台湾普通话
F09|女声|港风|晓曼|zh-HK-HiuMaanNeural|-2%|+2Hz|粤语
F10|女声|知性|晓佳|zh-HK-HiuGaaiNeural|-7%|-6Hz|粤语
VOICES

if [[ "$count" -ne 13 ]]; then
  printf '数量校验失败：应为 13，实际为 %s。\n' "$count" >&2
  exit 1
fi

if [[ "$INSTALL" -eq 1 ]]; then
  SOUNDS_DIR="$HOME/Library/Sounds"
  mkdir -p "$SOUNDS_DIR"
  cp "$AIFF_DIR"/*.aiff "$SOUNDS_DIR/"
  printf '已安装 13 个 AIFF 文件到：%s\n' "$SOUNDS_DIR"
fi

printf '\n完成：3 种男声 + 10 种女声，共 13 个。\n'
printf 'AIFF：%s\n' "$AIFF_DIR"
printf 'MP3： %s\n' "$MP3_DIR"
printf '清单：%s\n' "$MANIFEST"

