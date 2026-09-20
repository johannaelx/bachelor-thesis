from contextlib import asynccontextmanager
from dotenv import load_dotenv
load_dotenv()  # must run before importing modules that access env vars

import base64
import traceback
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.asr.whisper import transcribe_wav_bytes
from backend.app.llm.openai_api import npc_chat, score_vocabulary
from backend.app.tts.piper import load_voice, speaker
from backend.app.database import get_db
from backend.app.models.deck import Deck
from backend.app.models.item import Item
from backend.app.models.user import User
from backend.app.progress import apply_and_save_review

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_voice()
    yield


app = FastAPI(title="Bachelorarbeit", lifespan=lifespan)


class UserCreate(BaseModel):
    name: str


class ReviewRequest(BaseModel):
    user_id: int
    item_id: int
    q: int


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/users")
def list_users(db: Session = Depends(get_db)):
    """Returns all users."""
    users = db.query(User).all()
    return [{"id": u.id, "name": u.name} for u in users]


@app.post("/users", status_code=201)
def create_user(body: UserCreate, db: Session = Depends(get_db)):
    """Creates a new user and returns it."""
    user = User(name=body.name.strip())
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "name": user.name}


@app.get("/decks")
def list_decks(db: Session = Depends(get_db)):
    """Returns all decks (without items)."""
    decks = db.query(Deck).all()
    return [{"id": d.id, "name": d.name} for d in decks]


@app.get("/decks/{deck_id}")
def get_deck(deck_id: int, db: Session = Depends(get_db)):
    """Returns a single deck with all its items."""
    deck = db.query(Deck).filter(Deck.id == deck_id).first()
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    items = [
        {"id": item.id, "german": item.german, "english": item.english}
        for item in deck.items
    ]
    return {"id": deck.id, "deck_name": deck.name, "items": items}


@app.post("/review")
def review(body: ReviewRequest, db: Session = Depends(get_db)):
    """
    Applies SM-2 for a given user/item/quality score and saves the result.
    Called directly when the user reveals the translation (q=0).
    """
    if body.q not in {0, 2, 5}:
        raise HTTPException(status_code=400, detail="q muss 0, 2 oder 5 sein.")

    item = db.get(Item, body.item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found.")

    user = db.get(User, body.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    result = apply_and_save_review(db, body.user_id, body.item_id, body.q)
    return {"q": body.q, "sm2": result}


conversation_running = False

@app.post("/conversation")
async def conversation(
    audio: UploadFile = File(...),
    user_id: int = Form(...),
    item_id: int = Form(...),
    db: Session = Depends(get_db),
):
    """
    Processes a spoken user input through the full speech pipeline:
    ASR (Faster Whisper) -> LLM scoring -> SM-2 -> DB -> LLM reply (gpt-4o-mini) -> TTS (Piper).

    Expects a WAV audio file plus user_id and item_id as form fields.
    Returns the NPC reply text, base64-encoded audio, and the SM-2 result.
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

        item = db.get(Item, item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found.")

        # ASR
        transcription: str = transcribe_wav_bytes(wav_bytes)
        print("TRANSCRIPTION:", repr(transcription))

        # LLM scoring
        scoring: dict = score_vocabulary(item.english, transcription)
        q: int = scoring["q"]
        print("SCORING:", repr(scoring))

        # SM-2
        sm2_result = apply_and_save_review(db, user_id, item_id, q)
        print("SM2:", repr(sm2_result))

        # LLM reply
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

    return JSONResponse(content={
        "reply": llm_response["reply"],
        "audio": audio_b64,
        "scoring": scoring,
        "sm2": sm2_result,
    })


# Serve the frontend after API routes so /health and /conversation stay intact.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
