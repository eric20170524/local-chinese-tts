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
  cloneName: document.querySelector("#cloneName"),
  cloneAudio: document.querySelector("#cloneAudio"),
  cloneRefText: document.querySelector("#cloneRefText"),
  createCloneBtn: document.querySelector("#createCloneBtn"),
  clonedVoicesList: document.querySelector("#clonedVoicesList"),
  dropZone: document.querySelector("#dropZone"),
  dropText: document.querySelector("#dropText"),
  cloneAudioPreview: document.querySelector("#cloneAudioPreview"),
  cloneModelStatusBadge: document.querySelector("#cloneModelStatusBadge"),
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
  const source = voice.offline
    ? (voice.tier === "clone" ? "本地专属克隆" : voice.tier === "quality" ? "本地高质量" : "本地轻量")
    : "在线神经语音";
  elements.selectedSummary.textContent = `${voice.id} · ${source} · ${voice.gender} · ${voice.style} · ${voice.name}`;
}

function matchesFilter(voice) {
  if (state.filter === "all") return true;
  if (state.filter === "local") return voice.offline;
  if (state.filter === "online") return !voice.offline;
  return voice.tier === state.filter;
}

function tierLabel(voice) {
  if (voice.tier === "clone") return "专属克隆";
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
  renderClonedVoices();
  updateSummary();
  try {
    await fetch("/api/settings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ voice: voiceId }),
    });
  } catch (_) {}
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
  renderClonedVoices();
}

function renderClonedVoices() {
  const cloned = state.voices.filter((v) => v.tier === "clone");
  if (!elements.clonedVoicesList) return;
  elements.clonedVoicesList.replaceChildren();

  if (cloned.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-clones";
    empty.textContent = "暂无自定义克隆音色，上传 3~10 秒参考音频即可生成专属音色";
    elements.clonedVoicesList.appendChild(empty);
    return;
  }

  cloned.forEach((voice) => {
    const item = document.createElement("div");
    item.className = `cloned-item ${voice.id === state.selected ? "active-voice" : ""}`;

    const info = document.createElement("div");
    info.className = "cloned-info";

    const title = document.createElement("div");
    title.className = "cloned-title";
    title.innerHTML = `<span>${voice.name}</span><span class="cloned-badge">${voice.id}</span>`;

    const sub = document.createElement("div");
    sub.className = "cloned-sub";
    sub.textContent = voice.ref_text ? `参考文本: "${voice.ref_text}"` : `专属参考音频音色 (${voice.locale})`;

    info.appendChild(title);
    info.appendChild(sub);

    const actions = document.createElement("div");
    actions.className = "cloned-actions";

    if (voice.ref_audio_url) {
      const listenBtn = document.createElement("button");
      listenBtn.className = "btn-mini";
      listenBtn.type = "button";
      listenBtn.textContent = "🔊 原声";
      listenBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        const a = new Audio(voice.ref_audio_url);
        a.play();
      });
      actions.appendChild(listenBtn);
    }

    const useBtn = document.createElement("button");
    useBtn.className = "btn-mini use-btn";
    useBtn.type = "button";
    useBtn.textContent = voice.id === state.selected ? "使用中" : "使用";
    useBtn.addEventListener("click", () => selectVoice(voice.id));
    actions.appendChild(useBtn);

    const deleteBtn = document.createElement("button");
    deleteBtn.className = "btn-mini danger";
    deleteBtn.type = "button";
    deleteBtn.textContent = "删除";
    deleteBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      deleteCloneVoice(voice.id);
    });
    actions.appendChild(deleteBtn);

    item.appendChild(info);
    item.appendChild(actions);
    elements.clonedVoicesList.appendChild(item);
  });
}

async function deleteCloneVoice(voiceId) {
  if (!confirm("确定要删除该克隆音色吗？")) return;
  try {
    const res = await fetch(`/api/voices/clone/${voiceId}`, { method: "DELETE" });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "删除失败");
    state.voices = state.voices.filter((v) => v.id !== voiceId);
    if (state.selected === voiceId) {
      state.selected = "K01";
    }
    renderVoices();
  } catch (err) {
    showError(`删除克隆音色失败：${err.message}`);
  }
}

function handleAudioFileSelected(file) {
  if (!file) return;
  elements.dropText.textContent = `已选择: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)`;
  const url = URL.createObjectURL(file);
  elements.cloneAudioPreview.src = url;
  elements.cloneAudioPreview.classList.remove("hidden");
  if (!elements.cloneName.value) {
    elements.cloneName.value = file.name.replace(/\.[^/.]+$/, "") + "克隆";
  }
}

if (elements.cloneAudio) {
  elements.cloneAudio.addEventListener("change", (e) => {
    if (e.target.files && e.target.files[0]) {
      handleAudioFileSelected(e.target.files[0]);
    }
  });
}

if (elements.dropZone) {
  ["dragenter", "dragover"].forEach((eventName) => {
    elements.dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      elements.dropZone.classList.add("drag-over");
    });
  });
  ["dragleave", "drop"].forEach((eventName) => {
    elements.dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      elements.dropZone.classList.remove("drag-over");
    });
  });
  elements.dropZone.addEventListener("drop", (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files && files[0] && files[0].type.startsWith("audio/")) {
      elements.cloneAudio.files = files;
      handleAudioFileSelected(files[0]);
    }
  });
}

if (elements.createCloneBtn) {
  elements.createCloneBtn.addEventListener("click", async () => {
    const file = elements.cloneAudio.files && elements.cloneAudio.files[0];
    const name = elements.cloneName.value.trim() || "专属克隆音色";
    const refText = elements.cloneRefText.value.trim();

    if (!file) {
      showError("请选择或拖拽参考音频文件");
      return;
    }

    clearError();
    elements.createCloneBtn.disabled = true;
    const span = elements.createCloneBtn.querySelector("span");
    span.textContent = "⏳ 正在分析与录入音频...";

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("name", name);
      formData.append("ref_text", refText);

      const res = await fetch("/api/voices/clone", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "声音克隆处理失败");

      const newVoice = data.voice;
      state.voices.unshift(newVoice);
      state.selected = newVoice.id;
      renderVoices();

      elements.cloneName.value = "";
      elements.cloneRefText.value = "";
      elements.cloneAudio.value = "";
      elements.cloneAudioPreview.src = "";
      elements.cloneAudioPreview.classList.add("hidden");
      elements.dropText.textContent = "点击选择或拖拽音频文件至此处";
      alert(`音色【${newVoice.name}】录入成功！已自动设为当前朗读音色。`);
    } catch (err) {
      showError(`制作克隆音色失败：${err.message}`);
    } finally {
      elements.createCloneBtn.disabled = false;
      span.textContent = "✨ 保存并生成克隆音色";
    }
  });
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
    elements.downloadLink.download = `${data.voice.id}_${data.voice.style || "克隆"}_${data.voice.name}.mp3`;
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
    elements.voiceSummary.textContent = `${localCount} 种本地离线音色，${onlineCount} 种在线音色。轻量与克隆模型支持 100% 离线使用。`;
    renderVoices();
    const ready = state.localModels.light && state.localModels.quality;
    if (elements.cloneModelStatusBadge) {
      elements.cloneModelStatusBadge.textContent = state.localModels.clone ? "Qwen3 Base 克隆模型已就绪" : "克隆模型准备中...";
    }
    setStatus(ready ? "online" : "offline", ready ? "本地模型均已就绪" : "本机服务运行中");
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
