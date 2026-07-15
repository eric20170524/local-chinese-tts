#!/usr/bin/env python3
"""Download the two curated offline TTS models into this project."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import time

from huggingface_hub import snapshot_download


ROOT = Path(__file__).resolve().parent
HF_HOME = ROOT / "models" / "huggingface"
STATUS_FILE = ROOT / "models" / "status.json"

MODELS = {
    "light": "mlx-community/Kokoro-82M-4bit",
    "quality": "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-6bit",
}

KOKORO_VOICE_FILES = [
    "voices/zf_xiaoxiao.safetensors",
    "voices/zf_xiaoyi.safetensors",
    "voices/zm_yunxi.safetensors",
    "voices/zm_yunyang.safetensors",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="下载本机 MLX 中文语音模型")
    parser.add_argument("tiers", nargs="*", choices=sorted(MODELS), default=list(MODELS))
    args = parser.parse_args()

    os.environ["HF_HOME"] = str(HF_HOME)
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    HF_HOME.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)

    status = {"models": {}, "updated_at": int(time.time())}
    if STATUS_FILE.exists():
        try:
            status.update(json.loads(STATUS_FILE.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            pass

    for tier in args.tiers:
        repo = MODELS[tier]
        print(f"正在下载 {tier}: {repo}", flush=True)
        path = snapshot_download(repo_id=repo, cache_dir=HF_HOME / "hub")
        dependencies = []
        if tier == "light":
            voice_path = snapshot_download(
                repo_id="prince-canuma/Kokoro-82M",
                cache_dir=HF_HOME / "hub",
                allow_patterns=KOKORO_VOICE_FILES,
            )
            dependencies.append({"repo": "prince-canuma/Kokoro-82M", "path": voice_path})
        status["models"][tier] = {
            "repo": repo,
            "path": path,
            "dependencies": dependencies,
            "ready": True,
        }
        status["updated_at"] = int(time.time())
        STATUS_FILE.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"完成 {tier}: {path}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
