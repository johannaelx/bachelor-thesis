from contextlib import asynccontextmanager
from dotenv import load_dotenv
load_dotenv()  # must run before importing modules that access env vars

import base64
import traceback

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from backend.app.asr.whisper import transcribe_wav_bytes
from backend.app.llm.openai_api import npc_chat
from backend.app.tts.piper import load_voice, speaker


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_voice()
    yield


app = FastAPI(title="Bachelorarbeit", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}

conversation_running = False

@app.post("/conversation")
async def conversation(audio: UploadFile = File(...)):
    """
    Processes a spoken user input through the full speech pipeline:
    ASR (Whisper) -> LLM (gpt-4o-mini) -> TTS (Piper).

    Expects a WAV audio file and returns a JSON response containing
    the reply text and base64-encoded synthesized WAV audio.
    """

    global conversation_running

    # simple lock to prevent multiple conversations running simultaneously
    if conversation_running:
        raise HTTPException(status_code=429, detail="Conversation already running")

    try:
        conversation_running = True

        if audio.content_type not in ("audio/wav", "audio/x-wav"):
            raise HTTPException(
                status_code=400,
                detail="Invalid audio format. Only WAV files are supported.",
            )

        wav_bytes = await audio.read()

        if len(wav_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file.")

        # ASR
        transcription: str = transcribe_wav_bytes(wav_bytes)
        print("TRANSCRIPTION:", repr(transcription))

        # LLM
        llm_response: dict = npc_chat(transcription)
        print("LLM_RESPONSE:", repr(llm_response))

        # TTS
        tts_audio: bytes = speaker(llm_response["reply"])

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Conversation pipeline failed: {str(e)}"
        )

    finally:
        conversation_running = False

    # encode WAV audio as base64 for JSON transport
    audio_b64 = base64.b64encode(tts_audio).decode("utf-8")

    # return reply text alongside the synthesized audio
    return JSONResponse(content={
        "reply": llm_response["reply"],
        "audio": audio_b64,
    })
