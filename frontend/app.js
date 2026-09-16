// start screen
const screenStart = document.getElementById("screen-start");
const screenSession = document.getElementById("screen-session");
const profileListEl = document.getElementById("profile-list");
const deckListEl = document.getElementById("deck-list");
const newProfileForm = document.getElementById("new-profile-form");
const newProfileNameInput = document.getElementById("new-profile-name");
const startBtn = document.getElementById("start-btn");

// session screen
const targetWordEl = document.getElementById("target-word");
const translationEl = document.getElementById("translation");
const showTranslationBtn = document.getElementById("show-translation-btn");
const statusIndicator = document.getElementById("status-indicator");
const statusText = document.getElementById("status-text");
const deckNameEl = document.getElementById("deck-name");

// global
let items = [];
let currentItemIndex = 0;
let currentUserId = null;
let currentDeckId = null;
let newProfileName = "";

let translationRevealed = false;
let isRecording = false;
let isProcessing = false;
let spaceHeld = false;
let audioContext = null;
let mediaStream = null;
let sourceNode = null;
let processorNode = null;
let recordedSamples = [];

// start screen

async function initStartScreen() {
  try {
    const [usersRes, decksRes] = await Promise.all([
      fetch("/users"),
      fetch("/decks"),
    ]);

    if (!usersRes.ok || !decksRes.ok) {
      throw new Error("Daten konnten nicht geladen werden.");
    }

    const users = await usersRes.json();
    const decks = await decksRes.json();

    renderProfiles(users);
    renderDecks(decks);

    // auto-select deck if only one exists
    if (decks.length === 1) {
      selectDeck(decks[0].id);
    }
  } catch (err) {
    console.error(err);
    alert(err.message || "Fehler beim Laden des Startbildschirms.");
  }
}

function createSelectionCard(label, onClick) {
  const card = document.createElement("button");
  card.type = "button";
  card.className = "selection-card";
  card.textContent = label;
  card.addEventListener("click", onClick);
  return card;
}

function renderProfiles(users) {
  profileListEl.innerHTML = "";

  users.forEach((user) => {
    const card = createSelectionCard(user.name, () => selectProfile(user.id));
    card.dataset.profileId = String(user.id);
    profileListEl.appendChild(card);
  });

  const newCard = createSelectionCard("+ Neues Profil", () => selectProfile("new"));
  newCard.dataset.profileId = "new";
  newCard.classList.add("card-dashed");
  profileListEl.appendChild(newCard);
}

function renderDecks(decks) {
  deckListEl.innerHTML = "";
  decks.forEach((deck) => {
    const card = createSelectionCard(deck.name, () => selectDeck(deck.id));
    card.dataset.deckId = String(deck.id);
    deckListEl.appendChild(card);
  });
}

function selectProfile(id) {
  currentUserId = id;

  profileListEl.querySelectorAll(".selection-card").forEach((card) => {
    card.classList.toggle("selected", card.dataset.profileId === String(id));
  });

  if (id === "new") {
    newProfileForm.classList.remove("hidden");
    newProfileNameInput.focus();
  } else {
    newProfileForm.classList.add("hidden");
    newProfileName = "";
    newProfileNameInput.value = "";
  }

  updateStartBtn();
}

function selectDeck(id) {
  currentDeckId = id;

  deckListEl.querySelectorAll(".selection-card").forEach((card) => {
    card.classList.toggle("selected", card.dataset.deckId === String(id));
  });

  updateStartBtn();
}

function updateStartBtn() {
  const profileReady =
    typeof currentUserId === "number" ||
    (currentUserId === "new" && newProfileName.trim().length > 0);
  const deckReady = currentDeckId !== null;
  startBtn.disabled = !(profileReady && deckReady);
}

newProfileNameInput.addEventListener("input", () => {
  newProfileName = newProfileNameInput.value;
  updateStartBtn();
});

startBtn.addEventListener("click", async () => {
  startBtn.disabled = true;
  startBtn.textContent = "Wird gestartet…";

  try {
    // create user in DB if new profile was chosen
    if (currentUserId === "new") {
      const res = await fetch("/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newProfileName.trim() }),
      });
      if (!res.ok) throw new Error("Benutzer konnte nicht erstellt werden.");
      const user = await res.json();
      currentUserId = user.id;
    }

    await loadDeck();

    // switch to session screen
    screenStart.classList.add("hidden");
    screenSession.classList.remove("hidden");
    setStatus("idle", "Halte die Leertaste gedrückt, um zu sprechen");

  } catch (err) {
    console.error(err);
    alert(err.message || "Fehler beim Starten der Session.");
    startBtn.disabled = false;
    startBtn.textContent = "Session starten";
  }
});

// session screen

function showItem(index) {
  const item = items[index];
  if (!item) return;
  targetWordEl.textContent = item.german;
  translationEl.textContent = item.english;
  translationEl.classList.add("hidden");
  showTranslationBtn.style.display = "";
  translationRevealed = false;
}

function showFinished() {
  targetWordEl.textContent = "🎉";
  translationEl.classList.add("hidden");
  showTranslationBtn.style.display = "none";
  document.querySelector(".vocabulary-label").textContent = "Alle Wörter geübt!";
}

function nextItem() {
  const nextIndex = currentItemIndex + 1;
  if (nextIndex >= items.length) {
    showFinished();
    return;
  }
  currentItemIndex = nextIndex;
  showItem(currentItemIndex);
}

async function loadDeck() {
  const response = await fetch(`/decks/${currentDeckId}`);
  if (!response.ok) throw new Error("Deck nicht gefunden");
  const data = await response.json();
  deckNameEl.textContent = `Aktueller Stapel: ${data.deck_name}`;
  items = data.items;
  if (items.length > 0) {
    currentItemIndex = 0;
    showItem(0);
  }
}

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

    nextItem();
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

  // only active during session screen
  if (screenSession.classList.contains("hidden")) {
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
  if (translationRevealed) return;
  translationRevealed = true;
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

// init
initStartScreen();
