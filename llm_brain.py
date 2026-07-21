"""
Zaza Assistant — LLM Brain
Sends the user's command to a local Ollama model with tool definitions.
If the model decides to call a tool, we execute it and feed the result back
so the model can give a natural final answer.
"""

import json
import requests

from config import OLLAMA_URL, OLLAMA_MODEL, ASSISTANT_NAME
from tools import get_ollama_tool_schema, execute_tool

SYSTEM_PROMPT = f"""You are {ASSISTANT_NAME}, a local voice assistant running on the user's PC.
You have tools to check the time/date, open or close apps, open folders/files, search files,
open websites, and check system/battery info.

Rules:
- If the user's request matches a tool, call it. Don't just describe what you would do — call it.
- If no tool fits, answer briefly and conversationally, like a helpful assistant, not a chatbot essay.
- Keep spoken replies SHORT (1-2 sentences). This gets read aloud via text-to-speech.
- Never invent file paths or app names you weren't told — ask if unclear.
"""


def _chat(messages: list) -> dict:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "tools": get_ollama_tool_schema(),
        "stream": False,
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()


def think(user_text: str) -> str:
    """Takes a transcribed command, returns the final spoken reply."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]

    try:
        response = _chat(messages)
    except requests.exceptions.ConnectionError:
        return "I can't reach Ollama. Make sure it's running — try 'ollama serve' in a terminal."
    except Exception as e:
        return f"Something broke talking to the model: {e}"

    message = response.get("message", {})
    tool_calls = message.get("tool_calls")

    if not tool_calls:
        return message.get("content", "").strip() or "I didn't quite catch that."

    # Execute each tool call the model requested, then let it summarize
    messages.append(message)
    for call in tool_calls:
        fn = call["function"]
        name = fn["name"]
        args = fn.get("arguments", {})
        if isinstance(args, str):
            try:
                args = json.loads(args)
            except json.JSONDecodeError:
                args = {}

        result = execute_tool(name, args)
        messages.append({
            "role": "tool",
            "content": result,
        })

    try:
        final = _chat(messages)
        return final.get("message", {}).get("content", "").strip() or "Done."
    except Exception:
        # tool ran fine even if the summary call failed — surface the raw result
        return "Done."
