import os
import json
from typing import Dict
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

# prompt file
SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "default.txt"

def load_system_prompt() -> str:
    """
    Loads the system prompt.
    """

    with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


def npc_api(user_text: str) -> str:
    """
    Sends the user's utterance to the LLM and returns a JSON-formatted response.
    """
    system_prompt = load_system_prompt()

    user_prompt = f"""
    Player said:
    "{user_text}"

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


def npc_chat(user_text: str) -> Dict:
    """
    High-level wrapper used by the backend conversation pipeline.
    Parses the JSON reply from the LLM.
    """

    raw_response = npc_api(user_text)

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
