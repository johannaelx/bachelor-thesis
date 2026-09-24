// Shared application state used across all modules.

export const state = {
  // session identity
  currentUserId: null,    // number (existing user) or "new"
  currentDeckId: null,
  newProfileName: "",

  // vocabulary items
  items: [],
  currentItemIndex: 0,

  // session UI
  translationRevealed: false,

  // audio recording
  isRecording: false,
  isProcessing: false,
  spaceHeld: false,
  audioContext: null,
  mediaStream: null,
  sourceNode: null,
  processorNode: null,
  recordedSamples: [],
};
