const state = {
  voices: [],
  selected: "K01",
  filter: "local",
  localModels: {},
};

const elements = {
  statusDot: document.querySelector("#statusDot"),
  statusText: document.querySelector("#statusText"),
  textInput: document.querySelector("#textInput"),
  charCount: document.querySelector("#charCount"),
  voiceGrid: document.querySelector("#voiceGrid"),
  template: document.querySelector("#voiceTemplate"),
  selectedSummary: document.querySelector("#selectedSummary"),
  speedSelect: document.querySelector("#speedSelect"),
  speakButton: document.querySelector("#speakButton"),
  resultPanel: document.querySelector("#resultPanel"),
  audioPlayer: document.querySelector("#audioPlayer"),
  downloadLink: document.querySelector("#downloadLink"),
  cacheState: document.querySelector("#cacheState"),
  errorMessage: document.querySelector("#errorMessage"),
  copyEndpoint: document.querySelector("#copyEndpoint"),
  voiceCount: document.querySelector("#voiceCount"),
  voiceSummary: document.querySelector("#voiceSummary"),
};

function setStatus(kind, text) {
  elements.statusDot.className = `status-dot ${kind}`;
  elements.statusText.textContent = text;
}

function selectedVoice() {
  return state.voices.find((voice) => voice.id === state.selected);
}

function updateSummary() {
  const voice = selectedVoice();
  if (!voice) return;
  const source = voice.offline ? (voice.tier === "quality" ? "本地高质量" : "本地轻量") : "在线神经语音";
  elements.selectedSummary.textContent = `${voice.id} · ${source} · ${voice.gender} · ${voice.style} · ${voice.name}`;
}

function matchesFilter(voice) {
  if (state.filter === "all") return true;
  if (state.filter === "local") return voice.offline;
  if (state.filter === "online") return !voice.offline;
  return voice.tier === state.filter;
}

function tierLabel(voice) {
  if (voice.tier === "quality") return "本地高质";
  if (voice.tier === "light") return "本地轻量";
  return "在线";
}

async function selectVoice(voiceId) {
  state.selected = voiceId;
  document.querySelectorAll(".voice-card").forEach((card) => {
    const isSelected = card.dataset.voice === voiceId;
    card.classList.toggle("selected", isSelected);
    card.setAttribute("aria-pressed", String(isSelected));
  });
  updateSummary();
  try {
    await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ voice: voiceId }),
    });
  } catch (_) {
    // Selection still works for the current page even if persistence fails.
  }
}

function renderVoices() {
  elements.voiceGrid.replaceChildren();
  state.voices.forEach((voice) => {
    const fragment = elements.template.content.cloneNode(true);
    const card = fragment.querySelector(".voice-card");
    card.dataset.voice = voice.id;
    card.dataset.gender = voice.gender;
    card.dataset.tier = voice.tier;
    card.dataset.offline = String(voice.offline);
    card.classList.toggle("selected", voice.id === state.selected);
    card.hidden = !matchesFilter(voice);
    card.setAttribute("aria-pressed", String(voice.id === state.selected));
    fragment.querySelector(".voice-id").textContent = `${voice.id} · ${tierLabel(voice)}`;
    fragment.querySelector(".voice-style").textContent = voice.style;
    fragment.querySelector(".voice-name").textContent = voice.name;
    fragment.querySelector(".voice-description").textContent = voice.description;
    fragment.querySelector(".voice-locale").textContent = `${voice.locale} · ${voice.offline ? "完全离线" : "在线生成"}`;
    card.addEventListener("click", () => selectVoice(voice.id));
    elements.voiceGrid.appendChild(fragment);
  });
  updateSummary();
}

function showError(message) {
  elements.errorMessage.textContent = message;
  elements.errorMessage.classList.remove("hidden");
}

function clearError() {
  elements.errorMessage.classList.add("hidden");
}

async function speak() {
  const text = elements.textInput.value.trim();
  if (!text) {
    showError("请先输入要朗读的文字。");
    elements.textInput.focus();
    return;
  }

  clearError();
  elements.speakButton.disabled = true;
  elements.speakButton.querySelector("span:last-child").textContent = "正在生成…";
  try {
    const response = await fetch("/api/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        voice: state.selected,
        speed: Number(elements.speedSelect.value),
      }),
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "生成失败");

    elements.audioPlayer.src = `${data.url}?t=${Date.now()}`;
    elements.downloadLink.href = data.url;
    elements.downloadLink.download = `${data.voice.id}_${data.voice.style}_${data.voice.name}.mp3`;
    elements.cacheState.textContent = data.cached ? "来自本地缓存" : "新生成并已缓存";
    elements.resultPanel.classList.remove("hidden");
    try {
      await elements.audioPlayer.play();
    } catch (_) {
      elements.cacheState.textContent += " · 请点击播放器播放";
    }
  } catch (error) {
    showError(`生成失败：${error.message}`);
  } finally {
    elements.speakButton.disabled = false;
    elements.speakButton.querySelector("span:last-child").textContent = "开始朗读";
  }
}

async function initialize() {
  const savedText = localStorage.getItem("localChineseTtsText");
  if (savedText) elements.textInput.value = savedText;
  elements.charCount.textContent = elements.textInput.value.length;

  try {
    const response = await fetch("/api/voices");
    if (!response.ok) throw new Error("服务不可用");
    const data = await response.json();
    state.voices = data.voices;
    state.selected = data.selected || "K01";
    state.localModels = data.local_models || {};
    elements.voiceCount.textContent = String(state.voices.length);
    const localCount = state.voices.filter((voice) => voice.offline).length;
    const onlineCount = state.voices.length - localCount;
    elements.voiceSummary.textContent = `${localCount} 种本地离线音色，${onlineCount} 种在线音色。轻量模型常驻默认，高质量模型按需加载。`;
    renderVoices();
    const ready = state.localModels.light && state.localModels.quality;
    setStatus(ready ? "online" : "offline", ready ? "本地轻量与高质量模型均已就绪" : "本机服务运行中 · 本地模型尚未完整下载");
  } catch (error) {
    setStatus("offline", "无法连接本机 TTS 服务");
    showError(error.message);
  }
}

elements.textInput.addEventListener("input", () => {
  elements.charCount.textContent = elements.textInput.value.length;
  localStorage.setItem("localChineseTtsText", elements.textInput.value);
});

elements.textInput.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
    event.preventDefault();
    speak();
  }
});

elements.speakButton.addEventListener("click", speak);

document.querySelectorAll(".filter").forEach((button) => {
  button.addEventListener("click", () => {
    state.filter = button.dataset.filter;
    document.querySelectorAll(".filter").forEach((item) => item.classList.toggle("active", item === button));
    document.querySelectorAll(".voice-card").forEach((card) => {
      const voice = state.voices.find((item) => item.id === card.dataset.voice);
      card.hidden = !voice || !matchesFilter(voice);
    });
  });
});

elements.copyEndpoint.addEventListener("click", async () => {
  await navigator.clipboard.writeText("http://127.0.0.1:8765/v1/audio/speech");
  const label = elements.copyEndpoint.querySelector("span");
  label.textContent = "已复制";
  setTimeout(() => { label.textContent = "复制"; }, 1400);
});

initialize();
