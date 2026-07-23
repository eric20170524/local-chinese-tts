# Local Chinese TTS

[English](README_EN.md)

本项目提供中文本机 TTS 服务、网页控制面板、命令行、OpenAI Speech 兼容 API，以及 macOS 专用的系统提示音与“服务”快速操作。

## 平台支持

| 平台 | 支持状态 | 说明 |
|---|---|---|
| macOS Apple Silicon | 完整支持 | 支持离线 MLX 音色、在线备用音色、网页/API/CLI、LaunchAgent、Automator 服务和系统提示音安装。 |
| Windows | 完整支持 | 支持网页/API/CLI、Windows Batch / PowerShell 自动化脚本、双击隐蔽启动（`打开本机TTS.vbs`）、跨进程文件锁 `msvcrt`、Edge-TTS 在线音色与 ONNX 离线模型。 |
| Linux | 部分支持 | Python 服务、网页/API/CLI 可作为在线音色或手动适配后的服务使用；macOS 系统声音、LaunchAgent、Automator 服务不可用。 |

因此，核心服务在 macOS、Windows、Linux 上均可运行，并在 Windows 上提供完整的 PowerShell / Batch 自动化管理工具与静默启动能力。

> 仓库不包含本机模型、虚拟环境、缓存、日志和个人设置。安装依赖后可运行 `python download_local_models.py` 下载离线模型；轻量与高质量模型合计约 3.1GB。

## 本机动态 TTS

服务默认只监听 `127.0.0.1:8765`。

- 控制面板：[http://127.0.0.1:8765/](http://127.0.0.1:8765/)
- OpenAI Speech 兼容接口：`http://127.0.0.1:8765/v1/audio/speech`
- 当前默认音色会在网页中保存；在 macOS 上也会同步用于“中文音色朗读”快速操作。
- 默认音色是 `K01 本地轻量温柔`。
- K/Q 本地系列被强制设置为离线模式，不会静默访问 Hugging Face 或其他云端服务。
- F/M 在线系列首次合成需要联网；全部结果都会保存在 `cache/`。

## macOS 离线档位

当前离线模型基于 MLX，主要面向 Apple Silicon。原始实测机器为 MacBook Pro M2、8GB 统一内存、10 核 GPU：

| 档位 | 模型 | 音色 | 本机模型占用 | 测试合成耗时 | MLX 峰值内存 | 用途 |
|---|---|---:|---:|---:|---:|---|
| 默认轻量 | Kokoro 82M 4-bit | 4 | 约 650MB | 约 1.1-4.2 秒 | 约 1.1-2.0GB | 日常朗读、快速操作、长期开启 |
| 按需高质量 | Qwen3-TTS 1.7B 6-bit | 13 | 约 2.5GB | 约 9.5-11.3 秒 | 约 4.7-5.9GB | 重要内容、自然情绪和高品质导出 |

高质量模型由独立进程按需加载，完成后进程退出并释放内存；常驻的本机 API 服务实测约 40MB，不会长期占用模型内存。

## 安装与启动

### Windows 使用（win 分支）

#### 双击快捷启动
双击根目录下的 `打开本机TTS.vbs` 或 `打开本机TTS.bat` 即可静默启动服务并自动打开浏览器控制面板。

#### Windows 命令行

```cmd
# 自动创建虚拟环境并安装依赖
install_local_tts.bat

# 启动 HTTP API 服务与控制面板
start_local_tts.bat

# 停止服务
stop_local_tts.bat

# 命令行朗读测试
tts.bat list
tts.bat speak --voice F04 --text "你好，这是 Windows 本机 TTS 测试。" --play
```

### macOS 完整安装

```bash
cd /Users/lm/pyProj/local-chinese-tts
./install_local_tts.sh
```

安装后会注册当前用户的登录启动项、缓存清理任务和“中文音色朗读”服务。

在任意支持 macOS 服务的 App 中选中文字，然后打开 App 菜单中的“服务”，选择“中文音色朗读”。需要键盘快捷键时，可前往“系统设置 > 键盘 > 键盘快捷键 > 服务”，为“中文音色朗读”指定按键。

也可以直接启动控制面板：

```bash
./start_local_tts.sh
```

### Linux 部分使用

Linux 没有 macOS 系统集成。可以只运行本地 HTTP 服务和 CLI，但离线 MLX 音色不作为已验证支持范围。在线 F/M 音色依赖 `edge-tts` 和网络。

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
./tts.sh serve
```

## 缓存自动清理

动态朗读生成的音频与异常中断遗留的临时文件都保存在 `cache/`。macOS 完整安装会每天凌晨 03:15 自动删除超过 3 天的缓存；其他平台可以手动执行：

```bash
# 只显示将被删除的文件
./cleanup_tts_cache.sh --dry-run

# 立即删除超过 3 天的缓存
./cleanup_tts_cache.sh
```

## 命令行

```bash
# 查看全部音色，星号表示当前默认音色
./tts.sh list

# 朗读任意文字
./tts.sh speak --voice K01 --text "这是默认的本地轻量音色。" --play

# 高质量本地音色
./tts.sh speak --voice QF1 --text "这是高质量本地温柔女声。" --play

# 导出 AIFF
./tts.sh speak --voice QM1 --text "这是一条高质量成熟男声。" --format aiff --output ~/Desktop/成熟男声.aiff
```

`--play` 会在 macOS 上调用 `afplay`，在 Linux 上尝试 `ffplay`、`mpg123`、`mpv` 或 `aplay`。

## 本机 API

接口兼容常用的 OpenAI Speech 请求字段。`voice` 可填写 `K01`-`K04`、`QF1`-`QF10`、`QM1`-`QM3`，或者在线的 `M01`-`M03`、`F01`-`F10`：

```bash
curl http://127.0.0.1:8765/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -d '{"model":"local-chinese-tts","input":"你好，这是完全离线的本机语音接口。","voice":"K01","response_format":"mp3"}' \
  --output hello.mp3
```

## 已配置音色

### 完全离线

| 编号 | 档位 | 性别 | 风格 | 显示名 | 语言/口音 |
|---|---|---|---|---|---|
| K01 | 轻量默认 | 女声 | 温柔 | 晓晓 | 普通话 |
| K02 | 轻量 | 女声 | 活泼 | 晓伊 | 普通话 |
| K03 | 轻量 | 男声 | 阳光 | 云希 | 普通话 |
| K04 | 轻量 | 男声 | 沉稳 | 云扬 | 普通话 |
| QF1 | 高质量 | 女声 | 温柔 | Serena | 普通话 |
| QF2 | 高质量 | 女声 | 明亮 | Vivian | 普通话 |
| QF3 | 高质量 | 女声 | 甜美 | Vivian · 甜美 | 普通话 |
| QF4 | 高质量 | 女声 | 小女孩可爱 | Ono_Anna · 可爱 | 普通话（日本女声基底） |
| QF5 | 高质量 | 女声 | 纯真 | Serena · 纯真 | 普通话 |
| QF6 | 高质量 | 女声 | 元气 | Vivian · 元气 | 普通话 |
| QF7 | 高质量 | 女声 | 俏皮 | Ono_Anna · 俏皮 | 普通话（日本女声基底） |
| QF8 | 高质量 | 女声 | 软萌 | Sohee · 软萌 | 普通话（韩语女声基底） |
| QF9 | 高质量 | 女声 | 清甜 | Serena · 清甜 | 普通话 |
| QF10 | 高质量 | 女声 | 情感 | Sohee · 情感 | 普通话（韩语女声基底） |
| QM1 | 高质量 | 男声 | 成熟 | Uncle Fu | 普通话 |
| QM2 | 高质量 | 男声 | 京腔 | Dylan | 北京口音普通话 |
| QM3 | 高质量 | 男声 | 川味 | Eric | 四川口音普通话 |

### 在线备用

| 编号 | 性别 | 风格 | 显示名 | 语言/口音 |
|---|---|---|---|---|
| M01 | 男声 | 阳光 | 云希 | 普通话 |
| M02 | 男声 | 沉稳 | 云扬 | 普通话 |
| M03 | 男声 | 热血 | 云健 | 普通话 |
| F01 | 女声 | 可爱 | 晓伊 | 普通话 |
| F02 | 女声 | 活泼 | 晓伊 | 普通话 |
| F03 | 女声 | 御姐 | 晓晓 | 普通话 |
| F04 | 女声 | 温柔 | 晓晓 | 普通话 |
| F05 | 女声 | 甜美 | 晓臻 | 台湾普通话 |
| F06 | 女声 | 元气 | 晓妮 | 陕西口音普通话 |
| F07 | 女声 | 俏皮 | 晓北 | 东北口音普通话 |
| F08 | 女声 | 清新 | 晓雨 | 台湾普通话 |
| F09 | 女声 | 港风 | 晓曼 | 粤语 |
| F10 | 女声 | 知性 | 晓佳 | 粤语 |

## 重新生成 macOS 固定提示音

```bash
cd /Users/lm/pyProj/local-chinese-tts
./generate_voice_pack.sh --install
```

自定义中文文案：

```bash
./generate_voice_pack.sh --install --text "会议马上开始，请及时加入。"
```

生成阶段需要联网调用在线神经语音；只发送 `--text` 指定的文案。生成后的 AIFF 文件完全离线可用。首次在新机器运行时，脚本还会安装固定版本的 `edge-tts` Python 依赖。

## 文件位置

- `outputs/aiff/`：44.1 kHz、单声道、16-bit AIFF，适合放入 macOS 系统声音目录。
- `outputs/mp3/`：相同声音的 MP3 试听版。
- `outputs/manifest.tsv`：声音、风格、语速、音高和时长清单。
- `试听.html`：浏览器试听全部 13 个在线声音。
- `local_tts.py`：本机网页、缓存、命令行和兼容 API 服务。
- `local_mlx_worker.py`：隔离运行本地 MLX 模型，确保高质量模型用完即释放。
- `models/`：已下载的两个本地模型，合计约 3.1GB。
- `web/`：本机 TTS 控制面板。
- `cache/`：动态朗读音频缓存。
- `cleanup_tts_cache.sh`：缓存清理脚本；macOS 登录启动项每天自动运行一次。

macOS 固定提示音安装后，重新打开“系统设置 > 声音 > 声音效果”。系统列表中会出现以 `CN_` 开头的声音；安装只影响当前 macOS 用户。

## 语音依据

本地推理使用面向 Apple 芯片优化的 [MLX-Audio](https://github.com/Blaizzy/mlx-audio)。高质量档来自 [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS)，轻量档来自 [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M-v1.1-zh)。在线音色性别和风格能力来自 [Microsoft Azure Speech 语言与语音支持](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support)，在线自动化调用参考 [edge-tts](https://github.com/rany2/edge-tts)。
