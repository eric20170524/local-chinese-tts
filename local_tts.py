#!/usr/bin/env python3
"""Local Chinese TTS gateway with offline MLX and online neural voice presets."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any

import edge_tts
from aiohttp import web


ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
CACHE_DIR = ROOT / "cache"
SETTINGS_FILE = ROOT / "settings.json"
MODEL_STATUS_FILE = ROOT / "models" / "status.json"
DEFAULT_VOICE = "K01"
MAX_TEXT_LENGTH = 5000
FFMPEG = shutil.which("ffmpeg") or "/opt/homebrew/bin/ffmpeg"
PLAY_COMMANDS = (
    ["/usr/bin/afplay"],
    ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"],
    ["mpg123", "-q"],
    ["mpv", "--no-video", "--really-quiet"],
    ["aplay"],
)
LOCAL_LIGHT_MODEL = "mlx-community/Kokoro-82M-4bit"
LOCAL_QUALITY_MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-6bit"

LOCAL_VOICES: list[dict[str, Any]] = [
    {"id": "K01", "gender": "女声", "style": "轻量温柔", "name": "晓晓", "voice": "zf_xiaoxiao", "rate": "+0%", "pitch": "+0Hz", "locale": "普通话", "description": "默认离线音色，低内存、响应快", "provider": "local-mlx", "tier": "light", "offline": True, "model": LOCAL_LIGHT_MODEL, "lang_code": "z", "instruct": "", "resource": "实测峰值约 1.96GB"},
    {"id": "K02", "gender": "女声", "style": "轻量活泼", "name": "晓伊", "voice": "zf_xiaoyi", "rate": "+0%", "pitch": "+0Hz", "locale": "普通话", "description": "轻快女声，适合日常内容", "provider": "local-mlx", "tier": "light", "offline": True, "model": LOCAL_LIGHT_MODEL, "lang_code": "z", "instruct": "", "resource": "实测峰值约 1.96GB"},
    {"id": "K03", "gender": "男声", "style": "轻量阳光", "name": "云希", "voice": "zm_yunxi", "rate": "+0%", "pitch": "+0Hz", "locale": "普通话", "description": "清爽男声，适合快速朗读", "provider": "local-mlx", "tier": "light", "offline": True, "model": LOCAL_LIGHT_MODEL, "lang_code": "z", "instruct": "", "resource": "实测峰值约 1.96GB"},
    {"id": "K04", "gender": "男声", "style": "轻量沉稳", "name": "云扬", "voice": "zm_yunyang", "rate": "+0%", "pitch": "+0Hz", "locale": "普通话", "description": "稳定男声，适合说明和长文", "provider": "local-mlx", "tier": "light", "offline": True, "model": LOCAL_LIGHT_MODEL, "lang_code": "z", "instruct": "", "resource": "实测峰值约 1.96GB"},
    {"id": "QF1", "gender": "女声", "style": "高质温柔", "name": "Serena", "voice": "Serena", "rate": "+0%", "pitch": "+0Hz", "locale": "普通话", "description": "自然温暖，适合高品质叙述", "provider": "local-mlx", "tier": "quality", "offline": True, "model": LOCAL_QUALITY_MODEL, "lang_code": "Chinese", "instruct": "用温柔、自然、清晰的普通话朗读，情绪细腻但不过度表演。", "resource": "实测峰值约 5.85GB"},
    {"id": "QF2", "gender": "女声", "style": "高质明亮", "name": "Vivian", "voice": "Vivian", "rate": "+0%", "pitch": "+0Hz", "locale": "普通话", "description": "年轻明亮，支持自然情绪控制", "provider": "local-mlx", "tier": "quality", "offline": True, "model": LOCAL_QUALITY_MODEL, "lang_code": "Chinese", "instruct": "用明亮、有亲和力、自然活泼的普通话朗读。", "resource": "实测峰值约 5.85GB"},
    {"id": "QF3", "gender": "女声", "style": "高质甜美", "name": "Vivian · 甜美", "voice": "Vivian", "rate": "+0%", "pitch": "+0Hz", "locale": "普通话", "description": "甜润亲切，适合祝福、陪伴和轻叙述", "provider": "local-mlx", "tier": "quality", "offline": True, "model": LOCAL_QUALITY_MODEL, "lang_code": "Chinese", "instruct": "用甜美、轻柔、带微笑的年轻女声朗读普通话；音色明亮亲切，不过度撒娇，吐字清晰。", "resource": "实测峰值约 5.85GB"},
    {"id": "QF4", "gender": "女声", "style": "高质小女孩可爱", "name": "Ono_Anna · 可爱", "voice": "Ono_Anna", "rate": "+0%", "pitch": "+0Hz", "locale": "普通话（日本女声基底）", "description": "轻盈稚气、灵巧可爱，适合短句和轻松内容", "provider": "local-mlx", "tier": "quality", "offline": True, "model": LOCAL_QUALITY_MODEL, "lang_code": "Chinese", "instruct": "用小女孩般可爱、明亮、轻盈的感觉朗读普通话；语气自然有好奇心，保持清晰不含糊。", "resource": "实测峰值约 5.85GB"},
    {"id": "QF5", "gender": "女声", "style": "高质纯真", "name": "Serena · 纯真", "voice": "Serena", "rate": "+0%", "pitch": "+0Hz", "locale": "普通话", "description": "清澈真诚，适合童话、陪伴和治愈内容", "provider": "local-mlx", "tier": "quality", "offline": True, "model": LOCAL_QUALITY_MODEL, "lang_code": "Chinese", "instruct": "用清澈、纯真、温软的年轻女声朗读普通话；情绪真诚，像自然分享美好故事，不要夸张。", "resource": "实测峰值约 5.85GB"},
    {"id": "QF6", "gender": "女声", "style": "高质元气", "name": "Vivian · 元气", "voice": "Vivian", "rate": "+0%", "pitch": "+0Hz", "locale": "普通话", "description": "阳光饱满、节奏轻快，适合互动和鼓励", "provider": "local-mlx", "tier": "quality", "offline": True, "model": LOCAL_QUALITY_MODEL, "lang_code": "Chinese", "instruct": "用阳光、元气满满、节奏轻快的年轻女声朗读普通话；带自然笑意和积极能量，保持流畅清晰。", "resource": "实测峰值约 5.85GB"},
    {"id": "QF7", "gender": "女声", "style": "高质俏皮", "name": "Ono_Anna · 俏皮", "voice": "Ono_Anna", "rate": "+0%", "pitch": "+0Hz", "locale": "普通话（日本女声基底）", "description": "灵动俏皮、节奏轻快，适合聊天和趣味文案", "provider": "local-mlx", "tier": "quality", "offline": True, "model": LOCAL_QUALITY_MODEL, "lang_code": "Chinese", "instruct": "用灵动、俏皮、带一点玩笑感的年轻女声朗读普通话；节奏轻快，语尾自然，不要夸张表演。", "resource": "实测峰值约 5.85GB"},
    {"id": "QF8", "gender": "女声", "style": "高质软萌", "name": "Sohee · 软萌", "voice": "Sohee", "rate": "+0%", "pitch": "+0Hz", "locale": "普通话（韩语女声基底）", "description": "柔软亲近、情感细腻，适合安抚和陪伴", "provider": "local-mlx", "tier": "quality", "offline": True, "model": LOCAL_QUALITY_MODEL, "lang_code": "Chinese", "instruct": "用软萌、温暖、亲近的年轻女声朗读普通话；带细腻情绪和微笑感，吐字自然清楚。", "resource": "实测峰值约 5.85GB"},
    {"id": "QF9", "gender": "女声", "style": "高质清甜", "name": "Serena · 清甜", "voice": "Serena", "rate": "+0%", "pitch": "+0Hz", "locale": "普通话", "description": "清新甜润、不过度修饰，适合日常朗读", "provider": "local-mlx", "tier": "quality", "offline": True, "model": LOCAL_QUALITY_MODEL, "lang_code": "Chinese", "instruct": "用清新、甜润、自然克制的年轻女声朗读普通话；发音干净通透，节奏舒展，避免过度卖萌。", "resource": "实测峰值约 5.85GB"},
    {"id": "QF10", "gender": "女声", "style": "高质情感", "name": "Sohee · 情感", "voice": "Sohee", "rate": "+0%", "pitch": "+0Hz", "locale": "普通话（韩语女声基底）", "description": "温暖富有情绪层次，适合故事和抒情内容", "provider": "local-mlx", "tier": "quality", "offline": True, "model": LOCAL_QUALITY_MODEL, "lang_code": "Chinese", "instruct": "用温暖、富有情绪层次但自然不夸张的年轻女声朗读普通话；根据文字表达细微情感变化，保持清晰。", "resource": "实测峰值约 5.85GB"},
    {"id": "QM1", "gender": "男声", "style": "高质成熟", "name": "Uncle Fu", "voice": "Uncle_Fu", "rate": "+0%", "pitch": "+0Hz", "locale": "普通话", "description": "低沉醇厚，适合纪录片和长文", "provider": "local-mlx", "tier": "quality", "offline": True, "model": LOCAL_QUALITY_MODEL, "lang_code": "Chinese", "instruct": "用沉稳、醇厚、可信赖的普通话朗读，节奏从容。", "resource": "实测峰值约 5.85GB"},
    {"id": "QM2", "gender": "男声", "style": "高质京腔", "name": "Dylan", "voice": "Dylan", "rate": "+0%", "pitch": "+0Hz", "locale": "北京口音普通话", "description": "年轻自然，带轻微北京口音", "provider": "local-mlx", "tier": "quality", "offline": True, "model": LOCAL_QUALITY_MODEL, "lang_code": "Chinese", "instruct": "用自然、清晰、富有交流感的北京口音普通话朗读。", "resource": "实测峰值约 5.85GB"},
    {"id": "QM3", "gender": "男声", "style": "高质川味", "name": "Eric", "voice": "Eric", "rate": "+0%", "pitch": "+0Hz", "locale": "四川口音普通话", "description": "活泼略沙哑，带成都口音", "provider": "local-mlx", "tier": "quality", "offline": True, "model": LOCAL_QUALITY_MODEL, "lang_code": "Chinese", "instruct": "用活泼、自然、带成都口音的普通话朗读。", "resource": "实测峰值约 5.85GB"},
]

EDGE_VOICES: list[dict[str, Any]] = [
    {"id": "M01", "gender": "男声", "style": "阳光", "name": "云希", "voice": "zh-CN-YunxiNeural", "rate": "+3%", "pitch": "+0Hz", "locale": "普通话", "description": "明亮自然，适合日常朗读"},
    {"id": "M02", "gender": "男声", "style": "沉稳", "name": "云扬", "voice": "zh-CN-YunyangNeural", "rate": "-8%", "pitch": "-8Hz", "locale": "普通话", "description": "可靠克制，适合长文和说明"},
    {"id": "M03", "gender": "男声", "style": "热血", "name": "云健", "voice": "zh-CN-YunjianNeural", "rate": "+6%", "pitch": "-2Hz", "locale": "普通话", "description": "有力量感，适合播报和激励"},
    {"id": "F01", "gender": "女声", "style": "可爱", "name": "晓伊", "voice": "zh-CN-XiaoyiNeural", "rate": "+12%", "pitch": "+18Hz", "locale": "普通话", "description": "轻快俏皮，音高明亮"},
    {"id": "F02", "gender": "女声", "style": "活泼", "name": "晓伊", "voice": "zh-CN-XiaoyiNeural", "rate": "+7%", "pitch": "+7Hz", "locale": "普通话", "description": "自然灵动，适合聊天内容"},
    {"id": "F03", "gender": "女声", "style": "御姐", "name": "晓晓", "voice": "zh-CN-XiaoxiaoNeural", "rate": "-10%", "pitch": "-24Hz", "locale": "普通话", "description": "成熟低沉，节奏从容"},
    {"id": "F04", "gender": "女声", "style": "温柔", "name": "晓晓", "voice": "zh-CN-XiaoxiaoNeural", "rate": "-8%", "pitch": "-4Hz", "locale": "普通话", "description": "温和耐听，默认推荐"},
    {"id": "F05", "gender": "女声", "style": "甜美", "name": "晓臻", "voice": "zh-TW-HsiaoChenNeural", "rate": "+7%", "pitch": "+12Hz", "locale": "台湾普通话", "description": "柔甜亲切，带台湾口音"},
    {"id": "F06", "gender": "女声", "style": "元气", "name": "晓妮", "voice": "zh-CN-shaanxi-XiaoniNeural", "rate": "+10%", "pitch": "+14Hz", "locale": "陕西口音普通话", "description": "明快有精神，带地域特色"},
    {"id": "F07", "gender": "女声", "style": "俏皮", "name": "晓北", "voice": "zh-CN-liaoning-XiaobeiNeural", "rate": "+9%", "pitch": "+10Hz", "locale": "东北口音普通话", "description": "幽默爽朗，带东北口音"},
    {"id": "F08", "gender": "女声", "style": "清新", "name": "晓雨", "voice": "zh-TW-HsiaoYuNeural", "rate": "+4%", "pitch": "+8Hz", "locale": "台湾普通话", "description": "清晰舒展，适合轻阅读"},
    {"id": "F09", "gender": "女声", "style": "港风", "name": "晓曼", "voice": "zh-HK-HiuMaanNeural", "rate": "-2%", "pitch": "+2Hz", "locale": "粤语", "description": "亲切港风，适合粤语文本"},
    {"id": "F10", "gender": "女声", "style": "知性", "name": "晓佳", "voice": "zh-HK-HiuGaaiNeural", "rate": "-7%", "pitch": "-6Hz", "locale": "粤语", "description": "稳重清晰，适合粤语说明"},
]

for edge_voice in EDGE_VOICES:
    edge_voice.update(
        {
            "provider": "edge-online",
            "tier": "online",
            "offline": False,
            "model": "Microsoft Edge Neural TTS",
            "lang_code": edge_voice["locale"],
            "instruct": "",
            "resource": "云端",
        }
    )

VOICES: list[dict[str, Any]] = LOCAL_VOICES + EDGE_VOICES

VOICE_MAP = {voice["id"]: voice for voice in VOICES}
VOICE_NAME_MAP = {voice["voice"]: voice for voice in VOICES}
class AsyncFileLock:
    """A cross-process file lock that plays nice with asyncio without blocking the event loop."""
    def __init__(self, lock_path: Path):
        self.lock_path = lock_path
        self.lock_file = None

    async def __aenter__(self):
        import fcntl
        self.lock_file = open(self.lock_path, "w")
        while True:
            try:
                # Try to acquire exclusive lock non-blockingly
                fcntl.flock(self.lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except (OSError, BlockingIOError):
                await asyncio.sleep(0.2)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.lock_file:
            import fcntl
            try:
                fcntl.flock(self.lock_file, fcntl.LOCK_UN)
            except Exception:
                pass
            self.lock_file.close()
            self.lock_file = None


LOCAL_TTS_LOCK = asyncio.Lock()


def json_response(data: Any, *, status: int = 200) -> web.Response:
    return web.json_response(
        data,
        status=status,
        dumps=lambda value: json.dumps(value, ensure_ascii=False),
    )


def load_settings() -> dict[str, str]:
    try:
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        data = {}
    voice_id = str(data.get("voice", DEFAULT_VOICE))
    if voice_id not in VOICE_MAP:
        voice_id = DEFAULT_VOICE
    return {"voice": voice_id}


def save_settings(voice_id: str) -> dict[str, str]:
    if voice_id not in VOICE_MAP:
        raise ValueError(f"未知音色：{voice_id}")
    settings = {"voice": voice_id}
    SETTINGS_FILE.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return settings


def resolve_voice(voice_id: str | None) -> dict[str, str]:
    if not voice_id:
        voice_id = load_settings()["voice"]
    voice = VOICE_MAP.get(voice_id) or VOICE_NAME_MAP.get(voice_id)
    if voice is None:
        raise ValueError(f"未知音色：{voice_id}")
    return voice


def normalize_text(text: Any) -> str:
    if not isinstance(text, str):
        raise ValueError("text/input 必须是字符串")
    text = text.strip()
    if not text:
        raise ValueError("请输入要朗读的文字")
    if len(text) > MAX_TEXT_LENGTH:
        raise ValueError(f"单次最多 {MAX_TEXT_LENGTH} 个字符")
    return text


def adjusted_rate(preset_rate: str, speed: float) -> str:
    if speed < 0.5 or speed > 2.0:
        raise ValueError("speed 必须在 0.5 到 2.0 之间")
    base = int(preset_rate.removesuffix("%"))
    combined = max(-50, min(100, base + round((speed - 1.0) * 100)))
    return f"{combined:+d}%"


def cache_path(text: str, voice: dict[str, str], speed: float, extension: str = "mp3") -> Path:
    payload = json.dumps(
        {
            "v": 2,
            "text": text,
            "voice": voice["voice"],
            "rate": voice["rate"],
            "pitch": voice["pitch"],
            "speed": speed,
            "provider": voice.get("provider"),
            "model": voice.get("model"),
            "instruct": voice.get("instruct"),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return CACHE_DIR / f"{voice['id']}_{digest}.{extension}"


async def synthesize(text: str, voice: dict[str, str], speed: float = 1.0) -> tuple[Path, bool]:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    target = cache_path(text, voice, speed)
    if target.exists() and target.stat().st_size > 1000:
        return target, True

    if voice.get("provider") == "local-mlx":
        return await synthesize_local(text, voice, speed, target)

    rate = adjusted_rate(voice["rate"], speed)
    temporary = target.with_name(f".{target.stem}.{os.getpid()}.tmp.mp3")
    try:
        communicator = edge_tts.Communicate(
            text,
            voice["voice"],
            rate=rate,
            pitch=voice["pitch"],
            volume="+0%",
        )
        await communicator.save(str(temporary))
        if not temporary.exists() or temporary.stat().st_size <= 1000:
            raise RuntimeError("在线语音服务返回了空音频")
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    return target, False


async def synthesize_local(
    text: str,
    voice: dict[str, Any],
    speed: float,
    target: Path,
) -> tuple[Path, bool]:
    async with LOCAL_TTS_LOCK:
        async with AsyncFileLock(ROOT / "local_tts.lock"):
            if target.exists() and target.stat().st_size > 1000:
                return target, True

            token = f"{target.stem}.{os.getpid()}"
            text_file = CACHE_DIR / f".{token}.txt"
            wav_file = CACHE_DIR / f".{token}.wav"
            mp3_file = CACHE_DIR / f".{token}.mp3"
            text_file.write_text(text, encoding="utf-8")
            command = [
                sys.executable,
                str(ROOT / "local_mlx_worker.py"),
                "--model",
                str(voice["model"]),
                "--voice",
                str(voice["voice"]),
                "--lang-code",
                str(voice["lang_code"]),
                "--text-file",
                str(text_file),
                "--output",
                str(wav_file),
                "--speed",
                str(speed),
            ]
            if voice.get("instruct"):
                command.extend(["--instruct", str(voice["instruct"])])

            environment = os.environ.copy()
            environment.update(
                {
                    "HF_HOME": str(ROOT / "models" / "huggingface"),
                    "HF_HUB_DISABLE_TELEMETRY": "1",
                    "HF_HUB_OFFLINE": "1",
                    "TRANSFORMERS_OFFLINE": "1",
                    "TOKENIZERS_PARALLELISM": "false",
                }
            )
            try:
                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    env=environment,
                )
                stdout, stderr = await process.communicate()
                if process.returncode != 0 or not wav_file.exists() or wav_file.stat().st_size <= 1000:
                    details = stderr.decode("utf-8", errors="replace")[-1600:]
                    raise RuntimeError(f"本地模型合成失败：{details.strip() or '没有生成音频'}")

                converter = await asyncio.create_subprocess_exec(
                    FFMPEG,
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-i",
                    str(wav_file),
                    "-af",
                    "highpass=f=60,lowpass=f=12000,loudnorm=I=-17:TP=-1.5:LRA=7",
                    "-ar",
                    "44100",
                    "-ac",
                    "1",
                    "-c:a",
                    "libmp3lame",
                    "-q:a",
                    "2",
                    str(mp3_file),
                )
                if await converter.wait() != 0 or not mp3_file.exists():
                    raise RuntimeError("本地模型音频转换失败")
                os.replace(mp3_file, target)

                metrics = stdout.decode("utf-8", errors="replace").strip().splitlines()
                if metrics:
                    (ROOT / "logs").mkdir(exist_ok=True)
                    with (ROOT / "logs" / "local_models.jsonl").open("a", encoding="utf-8") as log:
                        log.write(metrics[-1] + "\n")
            finally:
                text_file.unlink(missing_ok=True)
                wav_file.unlink(missing_ok=True)
                mp3_file.unlink(missing_ok=True)
            return target, False


def local_model_status() -> dict[str, Any]:
    try:
        status = json.loads(MODEL_STATUS_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        status = {"models": {}}
    models = status.get("models", {})
    return {
        "light": bool(models.get("light", {}).get("ready")),
        "quality": bool(models.get("quality", {}).get("ready")),
    }


async def convert_audio(source: Path, output_format: str) -> Path:
    output_format = "aiff" if output_format in {"aif", "aiff"} else output_format
    if output_format == "mp3":
        return source
    if output_format not in {"aiff", "wav"}:
        raise ValueError("response_format 仅支持 mp3、aiff 或 wav")
    if not Path(FFMPEG).exists():
        raise RuntimeError("未找到 ffmpeg，无法转换音频格式")

    target = source.with_suffix(f".{output_format}")
    if target.exists() and target.stat().st_size > 1000:
        return target
    codec = "pcm_s16be" if output_format == "aiff" else "pcm_s16le"
    process = await asyncio.create_subprocess_exec(
        FFMPEG,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-i",
        str(source),
        "-ar",
        "44100",
        "-ac",
        "1",
        "-c:a",
        codec,
        str(target),
    )
    if await process.wait() != 0 or not target.exists():
        raise RuntimeError("音频格式转换失败")
    return target


@web.middleware
async def error_middleware(request: web.Request, handler):
    try:
        return await handler(request)
    except (ValueError, json.JSONDecodeError) as error:
        return json_response({"error": str(error)}, status=400)
    except web.HTTPException:
        raise
    except Exception as error:  # noqa: BLE001 - API boundary
        message = str(error) or error.__class__.__name__
        return json_response({"error": message}, status=502)


async def index_handler(_: web.Request) -> web.FileResponse:
    return web.FileResponse(WEB_DIR / "index.html")


async def health_handler(_: web.Request) -> web.Response:
    return json_response(
        {"ok": True, "service": "local-chinese-tts", "voices": len(VOICES), "default_voice": load_settings()["voice"], "local_models": local_model_status()},
    )


async def voices_handler(_: web.Request) -> web.Response:
    return json_response({"voices": VOICES, "selected": load_settings()["voice"], "local_models": local_model_status()})


async def model_status_handler(_: web.Request) -> web.Response:
    return json_response(local_model_status())


async def get_settings_handler(_: web.Request) -> web.Response:
    return json_response(load_settings())


async def set_settings_handler(request: web.Request) -> web.Response:
    data = await request.json()
    settings = save_settings(str(data.get("voice", "")))
    return json_response(settings)


async def tts_handler(request: web.Request) -> web.Response:
    data = await request.json()
    text = normalize_text(data.get("text"))
    voice = resolve_voice(data.get("voice"))
    speed = float(data.get("speed", 1.0))
    audio, cached = await synthesize(text, voice, speed)
    return json_response(
        {
            "url": f"/audio/{audio.name}",
            "cached": cached,
            "voice": voice,
            "characters": len(text),
        },
    )


async def openai_speech_handler(request: web.Request) -> web.StreamResponse:
    data = await request.json()
    text = normalize_text(data.get("input"))
    voice = resolve_voice(data.get("voice"))
    speed = float(data.get("speed", 1.0))
    response_format = str(data.get("response_format", "mp3")).lower()
    audio, _ = await synthesize(text, voice, speed)
    audio = await convert_audio(audio, response_format)
    content_types = {"mp3": "audio/mpeg", "aiff": "audio/aiff", "aif": "audio/aiff", "wav": "audio/wav"}
    return web.FileResponse(
        audio,
        headers={
            "Content-Type": content_types.get(response_format, "application/octet-stream"),
            "Content-Disposition": f'inline; filename="{voice["id"]}.{audio.suffix.lstrip(".")}"',
        },
    )


async def models_handler(_: web.Request) -> web.Response:
    return web.json_response(
        {
            "object": "list",
            "data": [
                {"id": "local-chinese-tts", "object": "model", "owned_by": "local"},
            ],
        }
    )


def create_app() -> web.Application:
    app = web.Application(middlewares=[error_middleware], client_max_size=1024 * 1024)
    app.router.add_get("/", index_handler)
    app.router.add_get("/api/health", health_handler)
    app.router.add_get("/api/voices", voices_handler)
    app.router.add_get("/api/models", model_status_handler)
    app.router.add_get("/api/settings", get_settings_handler)
    app.router.add_post("/api/settings", set_settings_handler)
    app.router.add_post("/api/tts", tts_handler)
    app.router.add_post("/v1/audio/speech", openai_speech_handler)
    app.router.add_get("/v1/models", models_handler)
    app.router.add_static("/assets/", WEB_DIR, show_index=False)
    app.router.add_static("/audio/", CACHE_DIR, show_index=False)
    return app


async def speak_command(args: argparse.Namespace) -> int:
    if args.text:
        text = args.text
    elif args.clipboard:
        pbpaste = shutil.which("pbpaste")
        xclip = shutil.which("xclip")
        wl_paste = shutil.which("wl-paste")
        if pbpaste:
            text = subprocess.run([pbpaste], check=True, capture_output=True, text=True).stdout
        elif wl_paste:
            text = subprocess.run([wl_paste], check=True, capture_output=True, text=True).stdout
        elif xclip:
            text = subprocess.run([xclip, "-selection", "clipboard", "-o"], check=True, capture_output=True, text=True).stdout
        else:
            raise RuntimeError("未找到剪贴板工具：macOS 需要 pbpaste，Linux 可安装 wl-clipboard 或 xclip")
    elif args.stdin or not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        raise ValueError("请使用 --text、--clipboard，或通过标准输入传入文字")

    text = normalize_text(text)
    voice = resolve_voice(args.voice)
    audio, cached = await synthesize(text, voice, args.speed)
    audio = await convert_audio(audio, args.format)

    if args.output:
        destination = Path(args.output).expanduser().resolve()
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(audio, destination)
        print(destination)
    else:
        print(audio)

    if args.play:
        for command in PLAY_COMMANDS:
            executable = command[0]
            if Path(executable).exists() or shutil.which(executable):
                subprocess.run([*command, str(audio)], check=True)
                break
        else:
            raise RuntimeError("未找到音频播放工具：macOS 需要 afplay，Linux 可安装 ffplay、mpg123、mpv 或 aplay")
    print(f"voice={voice['id']} cached={str(cached).lower()}", file=sys.stderr)
    return 0


def list_command() -> int:
    selected = load_settings()["voice"]
    for voice in VOICES:
        marker = "*" if voice["id"] == selected else " "
        print(f"{marker} {voice['id']}  {voice['gender']} · {voice['style']} · {voice['name']} · {voice['locale']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="本机中文 TTS：3 种男声 + 10 种女声")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve = subparsers.add_parser("serve", help="启动本地网页和 OpenAI 兼容 API")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8765)

    speak = subparsers.add_parser("speak", help="合成、播放或导出文字")
    speak.add_argument("--text")
    speak.add_argument("--stdin", action="store_true")
    speak.add_argument("--clipboard", action="store_true")
    speak.add_argument("--voice", choices=sorted(VOICE_MAP))
    speak.add_argument("--speed", type=float, default=1.0)
    speak.add_argument("--format", choices=["mp3", "aiff", "wav"], default="mp3")
    speak.add_argument("--output")
    speak.add_argument("--play", action="store_true")

    subparsers.add_parser("list", help="列出音色")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "serve":
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        web.run_app(create_app(), host=args.host, port=args.port, print=None, access_log=None)
        return 0
    if args.command == "speak":
        try:
            return asyncio.run(speak_command(args))
        except (ValueError, RuntimeError) as error:
            print(f"错误：{error}", file=sys.stderr)
            return 2
    if args.command == "list":
        return list_command()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
