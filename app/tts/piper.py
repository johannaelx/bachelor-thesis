import io
import wave
from pathlib import Path
from piper import PiperVoice, SynthesisConfig

# base directory of this module
BASE_DIR = Path(__file__).resolve().parent

# directory containing TTS models
VOICE_MODEL_PATH = BASE_DIR / "models" /"en_US-ryan-medium.onnx"


def get_voice() -> PiperVoice:
    """
    Returns the Piper voice.
    Voices are cached to avoid repeated model loading.
    """

    if not VOICE_MODEL_PATH.exists():
        raise FileNotFoundError(f"Piper model not found: {VOICE_MODEL_PATH}")

    voice = PiperVoice.load(str(VOICE_MODEL_PATH))

    print(f"Loaded TTS voice model.")

    return voice


# configuration for speech synthesis
syn_config = SynthesisConfig(
    volume=0.5,
    length_scale=1.0,
    noise_scale=1.0,
    noise_w_scale=1.0,
    normalize_audio=False,
)


def speaker(text_input: str) -> bytes:
    """
    Synthesizes speech from text using the voice.
    """

    voice = get_voice()

    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as wav_file:
        voice.synthesize_wav(text_input, wav_file, syn_config=syn_config)

    buffer.seek(0)

    return buffer.read()