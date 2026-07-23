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
    "clone": "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-6bit",
}

KOKORO_VOICE_FILES = [
    "voices/zf_xiaoxiao.safetensors",
    "voices/zf_xiaoyi.safetensors",
    "voices/zm_yunxi.safetensors",
    "voices/zm_yunyang.safetensors",
]


def download_file_parallel(url: str, out_file: Path, content_length: int, num_workers: int = 8) -> None:
    import concurrent.futures
    import math
    import threading
    import urllib.request

    req_init = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req_init) as resp:
        final_url = resp.geturl()

    tmp_file = out_file.with_suffix(out_file.suffix + ".tmp")
    with open(tmp_file, "wb") as f:
        f.truncate(content_length)

    chunk_size = math.ceil(content_length / num_workers)
    tasks = []
    for i in range(num_workers):
        start_byte = i * chunk_size
        end_byte = min(content_length - 1, (i + 1) * chunk_size - 1)
        tasks.append((start_byte, end_byte))

    print(f"  └─ [多线程直连 CDN 加速] 开启 {num_workers} 线程下载 {out_file.name} (共 {content_length / 1024 / 1024:.1f} MB)...", flush=True)

    downloaded = 0
    lock = threading.Lock()
    last_print = time.time()

    def download_chunk(start: int, end: int) -> None:
        nonlocal downloaded, last_print
        req = urllib.request.Request(final_url, headers={"User-Agent": "Mozilla/5.0", "Range": f"bytes={start}-{end}"})
        with urllib.request.urlopen(req) as resp, open(tmp_file, "r+b") as f:
            f.seek(start)
            while True:
                buf = resp.read(2 * 1024 * 1024)
                if not buf:
                    break
                f.write(buf)
                with lock:
                    downloaded += len(buf)
                    if time.time() - last_print > 1:
                        last_print = time.time()
                        pct = f"{downloaded / content_length * 100:.1f}%"
                        print(f"     [进度] {pct} ({downloaded / 1024 / 1024:.1f}/{content_length / 1024 / 1024:.1f} MB)", flush=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(download_chunk, s, e) for s, e in tasks]
        for future in concurrent.futures.as_completed(futures):
            future.result()

    tmp_file.replace(out_file)


def download_repo_direct(repo_id: str, hub_dir: Path, allow_patterns: list[str] | None = None) -> Path:
    import urllib.request
    from huggingface_hub import list_repo_files

    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    snapshot_dir = hub_dir / ("models--" + repo_id.replace("/", "--")) / "snapshots" / "main"
    snapshot_dir.mkdir(parents=True, exist_ok=True)

    try:
        files = list_repo_files(repo_id)
    except Exception:
        # Fallback to standard snapshot_download if list_repo_files fails
        return snapshot_download(repo_id=repo_id, cache_dir=hub_dir, allow_patterns=allow_patterns)

    if allow_patterns:
        files = [f for f in files if any(p.rstrip("*") in f for p in allow_patterns)]

    print(f"[{repo_id}] 正在通过国内镜像直接下载 {len(files)} 个文件...", flush=True)
    for file_path in files:
        out_file = snapshot_dir / file_path
        out_file.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://hf-mirror.com/{repo_id}/resolve/main/{file_path}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            content_length = int(resp.headers.get("Content-Length", 0))
            if out_file.exists() and content_length > 0 and out_file.stat().st_size == content_length and file_path != ".gitattributes":
                print(f"  └─ [已有完整] {file_path} ({content_length / 1024 / 1024:.1f} MB)", flush=True)
                continue
            if content_length > 10 * 1024 * 1024:
                download_file_parallel(url, out_file, content_length, num_workers=8)
            else:
                print(f"  └─ [下载中] {file_path} (目标大小: {content_length / 1024 / 1024:.1f} MB)...", flush=True)
                tmp_file = out_file.with_suffix(out_file.suffix + ".tmp")
                with open(tmp_file, "wb") as f:
                    while True:
                        chunk = resp.read(1024 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)
                tmp_file.replace(out_file)
        print(f"  └─ [完成] {file_path}", flush=True)
    return snapshot_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="下载本机 MLX 中文语音模型")
    parser.add_argument("tiers", nargs="*", choices=sorted(MODELS), default=list(MODELS))
    args = parser.parse_args()

    os.environ["HF_HOME"] = str(HF_HOME)
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["HF_HUB_DISABLE_XET"] = "1"
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
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
        print(f"\n正在处理 {tier}: {repo}", flush=True)
        try:
            path = str(download_repo_direct(repo, HF_HOME / "hub"))
        except Exception as err:
            print(f"直链下载失败，使用备用方式下载: {err}", flush=True)
            path = str(snapshot_download(repo_id=repo, cache_dir=HF_HOME / "hub"))

        dependencies = []
        if tier == "light":
            try:
                voice_path = str(download_repo_direct("prince-canuma/Kokoro-82M", HF_HOME / "hub", allow_patterns=KOKORO_VOICE_FILES))
            except Exception:
                voice_path = str(snapshot_download(repo_id="prince-canuma/Kokoro-82M", cache_dir=HF_HOME / "hub", allow_patterns=KOKORO_VOICE_FILES))
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

