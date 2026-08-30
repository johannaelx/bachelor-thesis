import io
import numpy as np
import whisper
import soundfile as sf

# loads the Whisper model once
model = whisper.load_model("small")


def wav_bytes_to_pcm(wav_bytes: bytes) -> np.ndarray:
    """
    Converts WAV audio bytes into a mono PCM float32 NumPy array.

    Args:
        wav_bytes: Raw WAV audio data as bytes.

    Returns:
        A 1D NumPy array containing mono PCM audio samples.
    """
    with io.BytesIO(wav_bytes) as wav_io:
        audio, samplerate = sf.read(wav_io, dtype="float32")

    # convert to mono if stereo
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    return audio


def transcribe_pcm(audio_pcm: np.ndarray) -> str:
    """
    Transcribes mono PCM audio data into text using the Whisper model.

    Args:
        audio_pcm: A 1D NumPy array containing mono PCM audio samples.

    Returns:
        The transcribed text. Returns an empty string for empty input.

    Raises:
        ValueError: If the input audio is not a 1D mono signal.
    """
    if audio_pcm.ndim != 1:
        raise ValueError("audio_pcm must be a 1D mono signal")

    if audio_pcm.size == 0:
        return ""

    result = model.transcribe(audio_pcm, fp16=False, task="transcribe")

    return result.get("text", "").strip()


def transcribe_wav_bytes(wav_bytes: bytes) -> str:
    """
    High-level helper that converts WAV audio bytes directly into text.

    This function combines WAV decoding and transcription into a single
    call and is intended for use in the speech pipeline.
    """
    audio_pcm = wav_bytes_to_pcm(wav_bytes)
    return transcribe_pcm(audio_pcm)
