import io
import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

# Whisper expects 16 kHz PCM when a NumPy array is passed to transcribe()
WHISPER_SR = 16000

# loads the Whisper model once
model = WhisperModel("base.en", device="cpu", compute_type="int8")


def resample_pcm(
    audio: np.ndarray, orig_sr: int, target_sr: int = WHISPER_SR
) -> np.ndarray:
    """
    Resamples a 1D PCM signal to the given target sample rate.
    """
    if orig_sr == target_sr:
        return audio.astype(np.float32)

    if audio.size == 0:
        return audio.astype(np.float32)

    target_length = int(round(len(audio) * target_sr / orig_sr))
    x_old = np.linspace(0, 1, num=len(audio), endpoint=False)
    x_new = np.linspace(0, 1, num=target_length, endpoint=False)
    return np.interp(x_new, x_old, audio).astype(np.float32)


def wav_bytes_to_pcm(wav_bytes: bytes) -> np.ndarray:
    """
    Converts WAV audio bytes into a mono 16 kHz PCM float32 NumPy array.

    Args:
        wav_bytes: Raw WAV audio data as bytes.

    Returns:
        A 1D NumPy array containing mono PCM audio samples at 16 kHz.
    """
    with io.BytesIO(wav_bytes) as wav_io:
        audio, samplerate = sf.read(wav_io, dtype="float32")

    # convert to mono if stereo
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    return resample_pcm(audio, orig_sr=int(samplerate), target_sr=WHISPER_SR)


def transcribe_pcm(audio_pcm: np.ndarray) -> str:
    """
    Transcribes mono 16 kHz PCM audio data into text using the Whisper model.

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

    segments, _ = model.transcribe(
        audio_pcm,
        language="en",
        beam_size=1,
        task="transcribe",
    )
    return " ".join(segment.text for segment in segments).strip()


def transcribe_wav_bytes(wav_bytes: bytes) -> str:
    """
    High-level helper that converts WAV audio bytes directly into text.

    This function combines WAV decoding and transcription into a single
    call and is intended for use in the speech pipeline.
    """
    audio_pcm = wav_bytes_to_pcm(wav_bytes)
    return transcribe_pcm(audio_pcm)
