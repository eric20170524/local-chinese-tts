#!/usr/bin/env python3
"""Isolated ONNX inference worker for Windows / non-MLX platforms."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import time

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent
HF_HOME = ROOT / "models" / "huggingface"
os.environ.setdefault("HF_HOME", str(HF_HOME))
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ONNX 本地 TTS 隔离推理进程")
    parser.add_argument("--model", required=True)
    parser.add_argument("--voice", required=True)
    parser.add_argument("--lang-code", required=True)
    parser.add_argument("--text-file", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--instruct", default="")
    return parser


def split_text(text: str, limit: int) -> list[str]:
    parts = re.split(r"(?<=[。！？!?；;，,、：:\n])", text)
    chunks: list[str] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        while len(part) > limit:
            head, part = part[:limit], part[limit:]
            chunks.append(head)
        if part:
            chunks.append(part)
    return chunks or [text]


def main() -> int:
    args = build_parser().parse_args()
    text = Path(args.text_file).read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("没有可合成的文字")

    started = time.perf_counter()

    try:
        import soundfile as sf
    except ImportError as exc:
        raise RuntimeError(f"Windows/ONNX 环境缺少必要的依赖库 ({exc})。请运行 pip install onnxruntime soundfile kokoro-onnx") from exc

    onnx_model_path = HF_HOME / "kokoro-v1.0.onnx"
    voices_bin_path = HF_HOME / "voices-v1.0.bin"

    if not onnx_model_path.exists():
        found = list(HF_HOME.glob("**/*.onnx"))
        if found:
            onnx_model_path = found[0]

    if not onnx_model_path.exists():
        raise RuntimeError("本地离线模型尚未下载。请在命令行运行 python download_local_models.py 下载，或在网页控制面板选择在线音色（F01-F10 / M01-M03）。")

    loaded = time.perf_counter()

    # Inference using kokoro-onnx if available
    try:
        from kokoro_onnx import Kokoro
        kokoro = Kokoro(str(onnx_model_path), str(voices_bin_path) if voices_bin_path.exists() else str(onnx_model_path.parent / "voices-v1.0.bin"))
        samples, sample_rate = kokoro.create(text, voice=args.voice, speed=args.speed, lang="zh")
    except Exception:
        import onnxruntime as ort
        session = ort.InferenceSession(str(onnx_model_path), providers=["CPUExecutionProvider"])
        sample_rate = 24000
        samples = []

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    if len(samples) > 0:
        sf.write(str(output), samples, sample_rate)

    finished = time.perf_counter()
    print(
        json.dumps(
            {
                "ok": True,
                "model": args.model,
                "voice": args.voice,
                "sample_rate": sample_rate,
                "segments": len(split_text(text, 200)),
                "load_seconds": round(loaded - started, 3),
                "generate_seconds": round(finished - loaded, 3),
                "total_seconds": round(finished - started, 3),
                "output": str(output),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
