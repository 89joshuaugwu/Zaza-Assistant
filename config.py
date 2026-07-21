"""
Zaza Assistant — Configuration
Edit this file to rename your assistant, change the LLM model,
or add/remove apps it knows how to open.
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
ASSISTANT_NAME = "Josh"          # what you call it
WAKE_WORD = "josh"           # phrase that activates listening (lowercase, no punctuation)

# ── Ollama (local LLM) ────────────────────────────────────
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "qwen2.5:3b"      # good balance of speed + tool-calling accuracy on 16GB RAM
                                  # alt: "llama3.2:3b" if qwen misbehaves

# ── Speech-to-Text (Vosk) ─────────────────────────────────
VOSK_MODEL_PATH = os.path.join(BASE_DIR, "models", "vosk-model-small-en-us")
SAMPLE_RATE = 16000

# ── Command transcription (Whisper — much higher accuracy) ─
# Vosk (above) only handles the wake word — fast, always-listening, "good
# enough" for spotting one keyword. Actual commands get transcribed with
# Whisper instead, since Vosk's small model was garbling full sentences.
WHISPER_MODEL_SIZE = "base.en"   # tiny.en (fastest) / base.en (good balance) / small.en (most accurate, slower)
WHISPER_COMPUTE_TYPE = "int8"    # int8 = fast on CPU, minimal accuracy loss
MAX_COMMAND_SECONDS = 8          # hard cap so it never listens forever
SILENCE_THRESHOLD = 500          # int16 amplitude below this = silence
SILENCE_DURATION = 1.2           # seconds of quiet before it decides you're done talking

# ── Text-to-Speech ────────────────────────────────────────
TTS_RATE = 175                   # words per minute
TTS_VOLUME = 1.0

# ── Known applications ────────────────────────────────────
# Add your own here. Key = what you'll say, Value = command Windows runs.
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
