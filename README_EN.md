# Local Chinese TTS

[中文](README.md)

Local Chinese TTS is a self-hosted Chinese text-to-speech service with a web control panel, command-line interface, an OpenAI Speech-compatible API, and macOS integrations for system sounds and the Services menu.

## Platform support

| Platform | Status | Notes |
|---|---|---|
| macOS on Apple Silicon | Fully supported | Offline MLX voices, online fallback voices, web/API/CLI, LaunchAgents, an Automator Service, and system-sound installation. |
| Linux | Partially supported | The Python service, web UI, API, and CLI can run with online voices or manual adaptation. macOS system sounds, LaunchAgents, and the Automator Service are unavailable. The offline MLX setup is primarily intended for Apple Silicon. |
| Windows | Not supported | The project currently relies on Bash, POSIX file locks, and macOS/Linux-style paths. A PowerShell installer and Windows file-lock implementation are not yet available. |

The core service is not macOS-only, but the complete offline and system-integration experience targets macOS on Apple Silicon.

## Highlights

- A local HTTP service bound to `127.0.0.1:8765` by default.
- Web control panel at [http://127.0.0.1:8765/](http://127.0.0.1:8765/).
- OpenAI Speech-compatible endpoint: `http://127.0.0.1:8765/v1/audio/speech`.
- A lightweight, fully offline Kokoro/MLX tier and a high-quality, on-demand Qwen3-TTS/MLX tier.
- Online fallback voices powered by `edge-tts`, used only when an F/M voice is explicitly selected.
- macOS login startup, cache cleanup, system notification sounds, and a “Chinese Voice Reading” Service.

The repository intentionally excludes local models, virtual environments, caches, logs, and personal settings. After installing dependencies, download the offline models with `python3 download_local_models.py`. The lightweight and high-quality models require about 3.1 GB in total.

## Offline tiers on macOS

Offline inference uses MLX and is designed for Apple Silicon. Measurements below were taken on a MacBook Pro with an M2 chip, 8 GB unified memory, and a 10-core GPU.

| Tier | Model | Voices | Download size | Measured synthesis time | MLX peak memory | Intended use |
|---|---|---:|---:|---:|---:|---|
| Default lightweight | Kokoro 82M 4-bit | 4 | about 650 MB | about 1.1–4.2 s | about 1.1–2.0 GB | Everyday reading, quick actions, and long-running use. |
| On-demand high quality | Qwen3-TTS 1.7B 6-bit | 13 | about 2.5 GB | about 9.5–11.3 s | about 4.7–5.9 GB | Important content, expressive speech, and high-quality exports. |

The high-quality model runs in an isolated, on-demand worker process. The worker exits after each request so its memory is released. The resident API service uses roughly 40 MB in the original measurement and does not keep a model loaded.

## Installation and startup

### Full macOS installation

```bash
cd /path/to/local-chinese-tts
./install_local_tts.sh
```

For a fresh clone, install the Python dependencies and download the offline models first:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python3 download_local_models.py
```

The full installer registers a per-user login item, a cache cleanup job, and the “Chinese Voice Reading” Service. In an app that supports macOS Services, select text and choose **Services → Chinese Voice Reading** from the app menu. To assign a keyboard shortcut, open **System Settings → Keyboard → Keyboard Shortcuts → Services**.

You can also start the control panel directly:

```bash
./start_local_tts.sh
```

### Linux (partial support)

Linux does not provide the macOS integrations. You can run the local HTTP service and CLI, but offline MLX voices are outside the verified support scope. Online F/M voices require `edge-tts` and an internet connection.

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
./tts.sh serve
```

## Local service

The service listens only on `127.0.0.1:8765` by default.

- Control panel: [http://127.0.0.1:8765/](http://127.0.0.1:8765/)
- OpenAI Speech-compatible API: `http://127.0.0.1:8765/v1/audio/speech`
- The selected default voice is stored by the web UI and is also used by the macOS “Chinese Voice Reading” Service.
- The default voice is `K01`, a lightweight and fully offline voice on macOS Apple Silicon.
- Local K/Q voices are forced offline and never silently contact Hugging Face or another cloud service during synthesis.
- F/M online voices need network access on their first synthesis. Generated audio is cached under `cache/`.

## Cache cleanup

Generated speech audio and interrupted temporary files are stored in `cache/`. A full macOS installation deletes cache files older than three days every day at 03:15. On other platforms, run the cleanup script manually:

```bash
# Show files that would be removed
./cleanup_tts_cache.sh --dry-run

# Delete cache files older than three days
./cleanup_tts_cache.sh
```

## Command line

```bash
# List every voice; an asterisk marks the selected default
./tts.sh list

# Speak text with the default lightweight local voice
./tts.sh speak --voice K01 --text "This is the default lightweight local voice." --play

# Use a high-quality local voice
./tts.sh speak --voice QF1 --text "这是高质量本地温柔女声。" --play

# Export AIFF
./tts.sh speak --voice QM1 --text "这是一条高质量成熟男声。" --format aiff --output ~/Desktop/mature-male-voice.aiff
```

`--play` uses `afplay` on macOS. On Linux it tries `ffplay`, `mpg123`, `mpv`, and then `aplay`.

## API

The endpoint accepts the commonly used OpenAI Speech request fields. Set `voice` to `K01`–`K04`, `QF1`–`QF10`, `QM1`–`QM3`, or an online `M01`–`M03` / `F01`–`F10` voice.

```bash
curl http://127.0.0.1:8765/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{"model":"local-chinese-tts","input":"你好，这是完全离线的本机语音接口。","voice":"K01","response_format":"mp3"}' \
  --output hello.mp3
```

## Included voices

### Fully offline

| Code | Tier | Voice | Style | Display name | Language/accent |
|---|---|---|---|---|---|
| K01 | Lightweight default | Female | Gentle | Xiaoxiao | Mandarin Chinese |
| K02 | Lightweight | Female | Lively | Xiaoyi | Mandarin Chinese |
| K03 | Lightweight | Male | Sunny | Yunxi | Mandarin Chinese |
| K04 | Lightweight | Male | Steady | Yunyang | Mandarin Chinese |
| QF1 | High quality | Female | Gentle | Serena | Mandarin Chinese |
| QF2 | High quality | Female | Bright | Vivian | Mandarin Chinese |
| QF3 | High quality | Female | Sweet | Vivian · Sweet | Mandarin Chinese |
| QF4 | High quality | Female | Cute little girl | Ono_Anna · Cute | Mandarin Chinese (Japanese female voice base) |
| QF5 | High quality | Female | Innocent | Serena · Innocent | Mandarin Chinese |
| QF6 | High quality | Female | Energetic | Vivian · Energetic | Mandarin Chinese |
| QF7 | High quality | Female | Playful | Ono_Anna · Playful | Mandarin Chinese (Japanese female voice base) |
| QF8 | High quality | Female | Soft and cute | Sohee · Soft and cute | Mandarin Chinese (Korean female voice base) |
| QF9 | High quality | Female | Clear and sweet | Serena · Clear and sweet | Mandarin Chinese |
| QF10 | High quality | Female | Emotional | Sohee · Emotional | Mandarin Chinese (Korean female voice base) |
| QM1 | High quality | Male | Mature | Uncle Fu | Mandarin Chinese |
| QM2 | High quality | Male | Beijing-style | Dylan | Beijing-accented Mandarin |
| QM3 | High quality | Male | Sichuan-style | Eric | Sichuan-accented Mandarin |

### Online fallbacks

| Code | Voice | Style | Display name | Language/accent |
|---|---|---|---|---|
| M01 | Male | Sunny | Yunxi | Mandarin Chinese |
| M02 | Male | Steady | Yunyang | Mandarin Chinese |
| M03 | Male | Passionate | Yunjian | Mandarin Chinese |
| F01 | Female | Cute | Xiaoyi | Mandarin Chinese |
| F02 | Female | Lively | Xiaoyi | Mandarin Chinese |
| F03 | Female | Mature/elegant | Xiaoxiao | Mandarin Chinese |
| F04 | Female | Gentle | Xiaoxiao | Mandarin Chinese |
| F05 | Female | Sweet | Xiaozhen | Taiwanese Mandarin |
| F06 | Female | Energetic | Xiaoni | Shaanxi-accented Mandarin |
| F07 | Female | Playful | Xiaobei | Northeastern Mandarin |
| F08 | Female | Fresh | Xiaoyu | Taiwanese Mandarin |
| F09 | Female | Hong Kong style | Xiaoman | Cantonese |
| F10 | Female | Intellectual | Xiaojia | Cantonese |

## Regenerate macOS notification sounds

```bash
cd /path/to/local-chinese-tts
./generate_voice_pack.sh --install
```

Use custom Chinese text:

```bash
./generate_voice_pack.sh --install --text "会议马上开始，请及时加入。"
```

Generation uses an online neural voice and sends only the text supplied with `--text`. The generated AIFF files work completely offline. On a new machine, the script installs the pinned `edge-tts` Python dependency on first use.

## Project layout

- `outputs/aiff/`: 44.1 kHz, mono, 16-bit AIFF files for the macOS system-sounds directory.
- `outputs/mp3/`: MP3 previews of the same sounds.
- `outputs/manifest.tsv`: voice, style, speed, pitch, and duration manifest.
- `试听.html`: browser preview page for all 13 online voices.
- `local_tts.py`: web UI, cache, CLI, and compatible API service.
- `local_mlx_worker.py`: isolated local MLX inference worker; it releases high-quality model memory after use.
- `download_local_models.py`: downloads the curated offline models locally.
- `models/`: local model storage; model files are deliberately ignored by Git.
- `web/`: local TTS control panel.
- `cache/`: generated speech cache, ignored by Git.
- `cleanup_tts_cache.sh`: cache cleanup script; installed as a daily job by the full macOS installer.

After installing macOS notification sounds, reopen **System Settings → Sound → Sound Effects**. Sounds whose names start with `CN_` appear in the system list. Installation affects only the current macOS user.

## Credits

Local inference uses [MLX-Audio](https://github.com/Blaizzy/mlx-audio), optimized for Apple silicon. The high-quality tier uses [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS), and the lightweight tier uses [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M-v1.1-zh). Voice availability and style information for the online voices are based on [Microsoft Azure Speech language and voice support](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support); online synthesis automation uses [edge-tts](https://github.com/rany2/edge-tts).

## License

This project is available under the [Local Chinese TTS Personal Use License](LICENSE). Third-party dependencies, models, and services are subject to their own terms.
