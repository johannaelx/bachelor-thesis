import os
import json
from pathlib import Path
from openai import OpenAI
from collections import deque

from dotenv import load_dotenv
load_dotenv()

# OpenAI chat model used for generating NPC responses
API_MODEL_NAME = "gpt-4o-mini"

# API key is read from the environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY ist nicht gesetzt")

# OpenAI client instance
client = OpenAI(api_key=OPENAI_API_KEY)

# short-term dialogue memory
NPC_MEMORY = deque(maxlen=6)

# prompt files
SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "default.txt"
SCORE_PROMPT_PATH = Path(__file__).parent / "prompts" / "score_vocabulary.txt"
GREETING_PROMPT_PATH = Path(__file__).parent / "prompts" / "greeting.txt"

def reset_memory() -> None:
    """
    Clears the NPC dialogue memory. Should be called at the start of each session.
    """
    NPC_MEMORY.clear()

def npc_greeting(target_word: str) -> dict:
    """
    Generates an opening message from the NPC at the start of a session. Seeds NPC_Memory.
    """
    with open(GREETING_PROMPT_PATH, "r", encoding="utf") as f:
        system_prompt = f.read()
    
    user_prompt = f"""
    Target word: "{target_word}"

    Respond in JSON only.
    """

    response = client.chat.completions.create(
        model=API_MODEL_NAME,
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
    )

    raw = response.choices[0].message.content
    try:
        parsed = json.loads(raw)
        reply_text = parsed.get("reply", "")
    except json.JSONDecodeError:
        reply_text = raw
        parsed = {"reply": reply_text}
    
    NPC_MEMORY.append({"role": "assistant", "content": reply_text})

    return parsed

def load_system_prompt() -> str:
    """
    Loads the system prompt.
    """

    with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def npc_api(user_text: str, next_target_word: str | None = None) -> str:
    """
    Sends the user's utterance to the LLM and returns a JSON-formatted response.
    """
    system_prompt = load_system_prompt()

    next_word_instruction = ""
    if next_target_word:
        next_word_instruction = f'\nNext vocabulary target for the learner: "{next_target_word}". Naturally work a question or remark into your reply that leads the learner to use this word. DO NOT USE THE WORD YOURSELF:'

    user_prompt = f"""
    Player said:
    "{user_text}"
    {next_word_instruction}
    Respond in JSON only.
    """

    messages = [
        {"role": "system", "content": system_prompt},
    ]

    # add recent dialogue turns
    messages.extend(NPC_MEMORY)

    messages.append(
        {"role": "user", "content": user_prompt}
    )

    response = client.chat.completions.create(
        model=API_MODEL_NAME,
        messages=messages,
        temperature=0.6,
    )

    return response.choices[0].message.content


def npc_chat(user_text: str, next_target_word: str | None = None) -> dict:
    """
    High-level wrapper used by the backend conversation pipeline.
    Parses the JSON reply from the LLM.
    """

    raw_response = npc_api(user_text, next_target_word)

    try:
        parsed = json.loads(raw_response)
        reply_text = parsed.get("reply", "")
    except json.JSONDecodeError:
        reply_text = raw_response
        parsed = {"reply": reply_text}

    # update memory
    NPC_MEMORY.append({"role": "user", "content": user_text})
    NPC_MEMORY.append({"role": "assistant", "content": reply_text})

    return parsed


def score_vocabulary(target_word: str, transcription: str) -> dict:
    """
    Asks the LLM to score how well the target word was used in the transcription.
    Returns a dict with "target_word" and "q" ∈ {0, 2, 5}.
    Falls back to q=0 if the response cannot be parsed.
    """
    with open(SCORE_PROMPT_PATH, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    user_prompt = f"""
    Target word: "{target_word}"
    Learner's sentence: "{transcription}"

    Respond in JSON only.
    """

    response = client.chat.completions.create(
        model=API_MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
    )

    raw = response.choices[0].message.content
    try:
        parsed = json.loads(raw)
        q = int(parsed.get("q", 0))
        if q not in {0, 2, 5}:
            q = 0
    except (json.JSONDecodeError, ValueError):
        q = 0

    return {"target_word": target_word, "q": q}
