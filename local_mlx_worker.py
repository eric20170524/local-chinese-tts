#!/usr/bin/env python3
"""Isolated MLX inference worker so large models release memory after each request."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import time


ROOT = Path(__file__).resolve().parent
HF_HOME = ROOT / "models" / "huggingface"
os.environ.setdefault("HF_HOME", str(HF_HOME))
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MLX 本地 TTS 隔离推理进程")
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

    from mlx_audio.audio_io import write as audio_write
    from mlx_audio.tts.utils import load
    import mlx.core as mx
    import numpy as np

    started = time.perf_counter()
    model = load(args.model)
    loaded = time.perf_counter()

    generate_kwargs = {
        "text": text,
        "voice": args.voice,
        "speed": args.speed,
        "lang_code": args.lang_code,
        "verbose": False,
        "max_tokens": 2400,
    }
    if args.instruct:
        generate_kwargs["instruct"] = args.instruct

    chunk_limit = 240 if "Kokoro" in args.model else 500
    results = []
    for chunk in split_text(text, chunk_limit):
        generate_kwargs["text"] = chunk
        results.extend(model.generate(**generate_kwargs))
    if not results:
        raise RuntimeError("本地模型没有返回音频")
    arrays = [result.audio for result in results if result.audio is not None]
    if not arrays:
        raise RuntimeError("本地模型返回了空音频")
    audio = arrays[0] if len(arrays) == 1 else mx.concatenate(arrays, axis=0)
    mx.eval(audio)

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    sample_rate = int(results[0].sample_rate)
    audio_write(str(output), np.asarray(audio), sample_rate, format="wav")
    finished = time.perf_counter()

    print(
        json.dumps(
            {
                "ok": True,
                "model": args.model,
                "voice": args.voice,
                "sample_rate": sample_rate,
                "segments": len(results),
                "load_seconds": round(loaded - started, 3),
                "generate_seconds": round(finished - loaded, 3),
                "total_seconds": round(finished - started, 3),
                "peak_memory_gb": round(mx.get_peak_memory() / 1e9, 3),
                "output": str(output),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
