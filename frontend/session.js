import { state } from "./state.js";

const targetWordEl = document.getElementById("target-word");
const translationEl = document.getElementById("translation");
const showTranslationBtn = document.getElementById("show-translation-btn");
const statusIndicator = document.getElementById("status-indicator");
const statusText = document.getElementById("status-text");
const deckNameEl = document.getElementById("deck-name");

export function showItem(index) {
  const item = state.items[index];
  if (!item) return;
  targetWordEl.textContent = item.german;
  translationEl.textContent = item.english;
  translationEl.classList.add("hidden");
  showTranslationBtn.style.display = "";
  state.translationRevealed = false;
}

function showFinished() {
  targetWordEl.textContent = "🎉";
  translationEl.classList.add("hidden");
  showTranslationBtn.style.display = "none";
  document.querySelector(".vocabulary-label").textContent = "Alle Wörter geübt!";
}

export function nextItem() {
  const nextIndex = state.currentItemIndex + 1;
  if (nextIndex >= state.items.length) {
    showFinished();
    return;
  }
  state.currentItemIndex = nextIndex;
  showItem(state.currentItemIndex);
}

export async function loadDeck() {
  const response = await fetch(`/decks/${state.currentDeckId}?user_id=${state.currentUserId}`);
  if (!response.ok) throw new Error("Deck nicht gefunden");
  const data = await response.json();
  deckNameEl.textContent = `Aktueller Stapel: ${data.deck_name}`;
  state.items = data.items;
  if (state.items.length > 0) {
    state.currentItemIndex = 0;
    showItem(0);
  } else {
    showFinished();
  }
}

export function setStatus(stateStr, text) {
  statusIndicator.dataset.state = stateStr;
  statusText.textContent = text;
}

showTranslationBtn.addEventListener("click", async () => {
  if (state.translationRevealed) return;
  state.translationRevealed = true;
  translationEl.classList.remove("hidden");
  showTranslationBtn.style.display = "none";

  // automatically score q=0 when translation is revealed
  try {
    await fetch("/review", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_id: state.currentUserId,
        item_id: state.items[state.currentItemIndex].id,
        q: 0,
      }),
    });
  } catch (err) {
    console.error("Review konnte nicht gespeichert werden:", err);
  }

  // q=0 always triggers same_day_repeat
  state.items.push(state.items[state.currentItemIndex]);
  nextItem();
});
