"""
Zaza Assistant — Configuration
Edit this file to rename your assistant, change the LLM model,
tweak audio settings, or add/remove apps it knows how to open.
"""

import os
import sys

# ── Base path (works both as plain script and as a PyInstaller .exe) ──
if getattr(sys, "frozen", False):
    # Running as a bundled .exe — models/ must sit next to the .exe, not inside it
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Identity ──────────────────────────────────────────────
ASSISTANT_NAME = "Josh"           # what the assistant calls itself
# The wake word you actually *say* is determined by WAKE_MODEL below
# (e.g. "Hey Jarvis"). The assistant name is just for display/speech.

# ── Ollama (local LLM) ────────────────────────────────────
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:3b"      # good balance of speed + tool-calling accuracy on 16GB RAM
                                  # alt: "llama3.2:3b" if qwen misbehaves

# ── Wake Word Detection (OpenWakeWord) ─────────────────────
# Purpose-built neural wake word engine — much more accurate and lighter
# on CPU than the old Whisper-polling approach. Streams audio continuously
# in 80ms chunks with zero gaps.
#
# Available pre-trained models (just change the value below):
#   "hey_jarvis"   — say "Hey Jarvis"   (recommended, most reliable)
#   "alexa"        — say "Alexa"
#   "hey_mycroft"  — say "Hey Mycroft"
#
# First run downloads the model (~few MB) — needs internet once.
WAKE_MODEL = "hey_jarvis"         # pre-trained model name
WAKE_THRESHOLD = 0.5              # confidence (0.0–1.0); raise if you get false triggers

# ── Command transcription (Whisper) ────────────────────────
# After the wake word fires, Whisper transcribes your actual command.
# This is where accuracy matters most.
SAMPLE_RATE = 16000
WHISPER_MODEL_SIZE = "base.en"    # tiny.en = fastest / base.en = good balance / small.en = most accurate
WHISPER_COMPUTE_TYPE = "int8"     # int8 = fast on CPU, minimal accuracy loss
MAX_COMMAND_SECONDS = 8           # hard cap so it never listens forever
SILENCE_THRESHOLD = 500           # fallback — auto-calibrated on startup from ambient noise
SILENCE_DURATION = 1.2            # seconds of quiet before it decides you're done talking

# ── Conversation mode ─────────────────────────────────────
# After the wake word fires, the assistant stays in conversation mode —
# you can keep talking without saying the wake word again. It only goes
# back to listening for the wake word after this many seconds of silence.
CONVERSATION_TIMEOUT = 30         # seconds of silence before ending conversation

# ── Persistent memory ─────────────────────────────────────
# Conversation history is saved locally so the assistant remembers past
# sessions. Fully offline — just a JSON file on your disk.
MEMORY_DIR = os.path.join(BASE_DIR, "memory")
MAX_HISTORY = 50                  # keep this many past interactions

# ── Text-to-Speech ────────────────────────────────────────
TTS_RATE = 175                    # words per minute
TTS_VOLUME = 1.0
TTS_VOICE_INDEX = 0               # 0 = default Windows voice, 1 = next installed voice, etc.
                                  # To list available voices, run:
                                  #   python -c "import pyttsx3; e=pyttsx3.init(); [print(i,v.name) for i,v in enumerate(e.getProperty('voices'))]"

# ── Vosk (legacy — kept for reference, not used by default) ─
# VOSK_MODEL_PATH = os.path.join(BASE_DIR, "models", "vosk-model-small-en-us")

# ── Known applications ────────────────────────────────────
# Key = what you'll say, Value = command Windows runs.
# For most installed apps, the plain .exe name works because Windows resolves
# it via App Paths in the registry. If one doesn't open, give the full path.
APP_PATHS = {
    "chrome": "chrome",
    "google chrome": "chrome",
    "edge": "msedge",
    "notepad": "notepad",
    "calculator": "calc",
    "calc": "calc",
    "explorer": "explorer",
    "file explorer": "explorer",
    "word": "winword",
    "excel": "excel",
    "vscode": "code",
    "vs code": "code",
    "visual studio code": "code",
    "spotify": "spotify",
    "cmd": "cmd",
    "command prompt": "cmd",
    "powershell": "powershell",
    "task manager": "taskmgr",
    "paint": "mspaint",
}

# ── Common folders (say "open my documents" etc.) ─────────
FOLDER_PATHS = {
    "documents": os.path.join(os.path.expanduser("~"), "Documents"),
    "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
    "desktop": os.path.join(os.path.expanduser("~"), "Desktop"),
    "pictures": os.path.join(os.path.expanduser("~"), "Pictures"),
}
