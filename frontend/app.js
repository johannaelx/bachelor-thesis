const targetWordEl = document.getElementById("target-word");
const translationEl = document.getElementById("translation");
const showTranslationBtn = document.getElementById("show-translation-btn");
const statusIndicator = document.getElementById("status-indicator");
const statusText = document.getElementById("status-text");

// Placeholder vocabulary until the SRS backend provides due words.
const vocabulary = {
  word: "Haus",
  translation: "house",
};

let translationRevealed = false;
let isRecording = false;
let isProcessing = false;
let spaceHeld = false;
let audioContext = null;
let mediaStream = null;
let sourceNode = null;
let processorNode = null;
let recordedSamples = [];

targetWordEl.textContent = vocabulary.word;

function setStatus(state, text) {
  statusIndicator.dataset.state = state;
  statusText.textContent = text;
}

function isEditableTarget(event) {
  const target = event.target;
  return (
    target instanceof HTMLInputElement ||
    target instanceof HTMLTextAreaElement ||
    target instanceof HTMLSelectElement ||
    target.isContentEditable
  );
}

function encodeWav(samples, sampleRate) {
  const buffer = new ArrayBuffer(44 + samples.length * 2);
  const view = new DataView(buffer);

  const writeString = (offset, value) => {
    for (let i = 0; i < value.length; i += 1) {
      view.setUint8(offset + i, value.charCodeAt(i));
    }
  };

  writeString(0, "RIFF");
  view.setUint32(4, 36 + samples.length * 2, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, "data");
  view.setUint32(40, samples.length * 2, true);

  let offset = 44;
  for (const sample of samples) {
    const clamped = Math.max(-1, Math.min(1, sample));
    view.setInt16(offset, clamped < 0 ? clamped * 0x8000 : clamped * 0x7fff, true);
    offset += 2;
  }

  return new Blob([buffer], { type: "audio/wav" });
}

async function ensureAudioReady() {
  if (!mediaStream) {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  }

  if (!audioContext) {
    audioContext = new AudioContext();
  }

  if (audioContext.state === "suspended") {
    await audioContext.resume();
  }
}

function startRecording() {
  if (isRecording || isProcessing) {
    return;
  }

  recordedSamples = [];
  sourceNode = audioContext.createMediaStreamSource(mediaStream);
  processorNode = audioContext.createScriptProcessor(4096, 1, 1);

  processorNode.onaudioprocess = (event) => {
    if (!isRecording) {
      return;
    }
    recordedSamples.push(...event.inputBuffer.getChannelData(0));
  };

  sourceNode.connect(processorNode);
  processorNode.connect(audioContext.destination);

  isRecording = true;
  setStatus("recording", "Aufnahme läuft… lasse die Leertaste los, um die Antwort zu versenden");
}

function stopRecording() {
  if (!isRecording) {
    return null;
  }

  isRecording = false;

  processorNode.disconnect();
  sourceNode.disconnect();
  processorNode = null;
  sourceNode = null;

  if (recordedSamples.length === 0) {
    setStatus("idle", "Kein Audio erkannt — halte die Leertaste gedrückt, um zu sprechen");
    return null;
  }

  return encodeWav(recordedSamples, audioContext.sampleRate);
}

async function sendRecording(wavBlob) {
  isProcessing = true;
  setStatus("processing", "Deine Antwort wird verarbeitet…");

  const formData = new FormData();
  formData.append("audio", wavBlob, "recording.wav");

  try {
    const response = await fetch("/conversation", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new Error(errorBody.detail || `Request failed (${response.status})`);
    }

    const data = await response.json();
    setStatus("ready", "Antwort verarbeitet — halte die Leertaste gedrückt, um erneut zu sprechen");

    if (data.audio) {
      const audio = new Audio(`data:audio/wav;base64,${data.audio}`);
      await audio.play();
    }
  } catch (error) {
    console.error(error);
    setStatus("idle", error.message || "Etwas ist schiefgelaufen — probiere es nochmal");
  } finally {
    isProcessing = false;
  }
}

async function handleSpaceDown(event) {
  if (event.code !== "Space" || event.repeat || isEditableTarget(event)) {
    return;
  }

  event.preventDefault();
  spaceHeld = true;

  try {
    await ensureAudioReady();
    startRecording();
  } catch (error) {
    console.error(error);
    setStatus("idle", "Mikrofonzugriff erforderlich");
  }
}

async function handleSpaceUp(event) {
  if (event.code !== "Space" || isEditableTarget(event)) {
    return;
  }

  event.preventDefault();

  if (!spaceHeld) {
    return;
  }

  spaceHeld = false;

  const wavBlob = stopRecording();
  if (!wavBlob) {
    return;
  }

  await sendRecording(wavBlob);
}

showTranslationBtn.addEventListener("click", () => {
  if (translationRevealed) {
    return;
  }

  translationRevealed = true;
  translationEl.textContent = vocabulary.translation;
  translationEl.classList.remove("hidden");
  showTranslationBtn.style.display = "none";
});

window.addEventListener("keydown", handleSpaceDown);
window.addEventListener("keyup", handleSpaceUp);

window.addEventListener("blur", () => {
  if (isRecording) {
    spaceHeld = false;
    stopRecording();
    setStatus("idle", "Aufnahme abgebrochen — halte die Leertaste gedrückt, um zu sprechen");
  }
});

setStatus("idle", "Halte die Leertaste gedrückt, um zu sprechen");