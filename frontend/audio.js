import { state } from "./state.js";
import { nextItem, setStatus } from "./session.js";

const screenSession = document.getElementById("screen-session");

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
  if (!state.mediaStream) {
    state.mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  }

  if (!state.audioContext) {
    state.audioContext = new AudioContext();
  }

  if (state.audioContext.state === "suspended") {
    await state.audioContext.resume();
  }
}

function startRecording() {
  if (state.isRecording || state.isProcessing) {
    return;
  }

  state.recordedSamples = [];
  state.sourceNode = state.audioContext.createMediaStreamSource(state.mediaStream);
  state.processorNode = state.audioContext.createScriptProcessor(4096, 1, 1);

  state.processorNode.onaudioprocess = (event) => {
    if (!state.isRecording) {
      return;
    }
    state.recordedSamples.push(...event.inputBuffer.getChannelData(0));
  };

  state.sourceNode.connect(state.processorNode);
  state.processorNode.connect(state.audioContext.destination);

  state.isRecording = true;
  setStatus("recording", "Aufnahme läuft… lasse die Leertaste los, um die Antwort zu versenden");
}

function stopRecording() {
  if (!state.isRecording) {
    return null;
  }

  state.isRecording = false;

  state.processorNode.disconnect();
  state.sourceNode.disconnect();
  state.processorNode = null;
  state.sourceNode = null;

  if (state.recordedSamples.length === 0) {
    setStatus("idle", "Kein Audio erkannt — halte die Leertaste gedrückt, um zu sprechen");
    return null;
  }

  return encodeWav(state.recordedSamples, state.audioContext.sampleRate);
}

async function sendRecording(wavBlob) {
  state.isProcessing = true;
  setStatus("processing", "Deine Antwort wird verarbeitet…");

  const formData = new FormData();
  formData.append("audio", wavBlob, "recording.wav");
  formData.append("user_id", state.currentUserId);
  formData.append("item_id", state.items[state.currentItemIndex].id);

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

    // if item was answered incorrectly, repeat it later in same session
    if (data.sm2?.same_day_repeat) {
      state.items.push(state.items[state.currentItemIndex]);
    }

    nextItem();
  } catch (error) {
    console.error(error);
    setStatus("idle", error.message || "Etwas ist schiefgelaufen — probiere es nochmal");
  } finally {
    state.isProcessing = false;
  }
}

async function handleSpaceDown(event) {
  if (event.code !== "Space" || event.repeat || isEditableTarget(event)) {
    return;
  }

  // only active during session screen
  if (screenSession.classList.contains("hidden")) {
    return;
  }

  event.preventDefault();
  state.spaceHeld = true;

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

  if (!state.spaceHeld) {
    return;
  }

  state.spaceHeld = false;

  const wavBlob = stopRecording();
  if (!wavBlob) {
    return;
  }

  await sendRecording(wavBlob);
}

window.addEventListener("keydown", handleSpaceDown);
window.addEventListener("keyup", handleSpaceUp);

window.addEventListener("blur", () => {
  if (state.isRecording) {
    state.spaceHeld = false;
    stopRecording();
    setStatus("idle", "Aufnahme abgebrochen — halte die Leertaste gedrückt, um zu sprechen");
  }
});
