"""
Zaza Assistant — Persistent Memory

Stores conversation history locally as a JSON file so the assistant
remembers past sessions. Fully offline — no internet needed, just
local file I/O.

The memory folder is created next to the main script/exe and contains
a single history.json file with timestamped interactions.
"""

import json
import os
from datetime import datetime

from config import MEMORY_DIR, MAX_HISTORY

HISTORY_FILE = os.path.join(MEMORY_DIR, "history.json")


def _ensure_dir():
    os.makedirs(MEMORY_DIR, exist_ok=True)


def save_interaction(user_text: str, assistant_reply: str):
    """Save a single user→assistant exchange to disk."""
    _ensure_dir()
    history = load_history()
    history.append({
        "timestamp": datetime.now().isoformat(),
        "user": user_text,
        "assistant": assistant_reply,
    })
    # Keep only the most recent interactions
    history = history[-MAX_HISTORY:]
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except IOError:
        pass  # don't crash if write fails


def load_history() -> list:
    """Load the full conversation history from disk."""
    if not os.path.isfile(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def get_recent_summary(n: int = 5) -> str:
    """Get a text summary of the last N interactions for the LLM's context."""
    history = load_history()
    if not history:
        return ""
    recent = history[-n:]
    lines = []
    for h in recent:
        ts = h.get("timestamp", "")
        # Parse timestamp for readable format
        try:
            dt = datetime.fromisoformat(ts)
            time_str = dt.strftime("%B %d at %I:%M %p")
        except (ValueError, TypeError):
            time_str = "recently"
        lines.append(f"- [{time_str}] User asked: \"{h['user']}\" → You replied: \"{h['assistant']}\"")
    return "\n".join(lines)


def get_last_session_info() -> dict:
    """Returns info about the last interaction, or None if no history."""
    history = load_history()
    if not history:
        return None
    last = history[-1]
    try:
        dt = datetime.fromisoformat(last.get("timestamp", ""))
        return {
            "timestamp": dt,
            "user": last.get("user", ""),
            "assistant": last.get("assistant", ""),
            "total_interactions": len(history),
        }
    except (ValueError, TypeError):
        return {"total_interactions": len(history)}


def clear_history():
    """Wipes the conversation history and resets it to an empty list."""
    _ensure_dir()
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    except IOError:
        pass
