import { state } from "./state.js";
import { loadDeck, setStatus } from "./session.js";

const screenStart = document.getElementById("screen-start");
const screenSession = document.getElementById("screen-session");
const profileListEl = document.getElementById("profile-list");
const deckListEl = document.getElementById("deck-list");
const newProfileForm = document.getElementById("new-profile-form");
const newProfileNameInput = document.getElementById("new-profile-name");
const startBtn = document.getElementById("start-btn");

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
  state.currentUserId = id;

  profileListEl.querySelectorAll(".selection-card").forEach((card) => {
    card.classList.toggle("selected", card.dataset.profileId === String(id));
  });

  if (id === "new") {
    newProfileForm.classList.remove("hidden");
    newProfileNameInput.focus();
  } else {
    newProfileForm.classList.add("hidden");
    state.newProfileName = "";
    newProfileNameInput.value = "";
  }

  updateStartBtn();
}

function selectDeck(id) {
  state.currentDeckId = id;

  deckListEl.querySelectorAll(".selection-card").forEach((card) => {
    card.classList.toggle("selected", card.dataset.deckId === String(id));
  });

  updateStartBtn();
}

function updateStartBtn() {
  const profileReady =
    typeof state.currentUserId === "number" ||
    (state.currentUserId === "new" && state.newProfileName.trim().length > 0);
  const deckReady = state.currentDeckId !== null;
  startBtn.disabled = !(profileReady && deckReady);
}

newProfileNameInput.addEventListener("input", () => {
  state.newProfileName = newProfileNameInput.value;
  updateStartBtn();
});

startBtn.addEventListener("click", async () => {
  startBtn.disabled = true;
  startBtn.textContent = "Wird gestartet…";

  try {
    // create user in DB if new profile was chosen
    if (state.currentUserId === "new") {
      const res = await fetch("/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: state.newProfileName.trim() }),
      });
      if (!res.ok) throw new Error("Benutzer konnte nicht erstellt werden.");
      const user = await res.json();
      state.currentUserId = user.id;
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

export async function initStartScreen() {
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
