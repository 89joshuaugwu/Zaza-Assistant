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

# ── Hugging Face Authentication (optional for faster downloads) ──
# We load the token securely from the .env file instead of hardcoding it here.
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BASE_DIR, ".env"))
except ImportError:
    pass

HF_TOKEN = os.environ.get("HF_TOKEN")
if HF_TOKEN:
    os.environ["HUGGING_FACE_HUB_TOKEN"] = HF_TOKEN

# ── Identity ──────────────────────────────────────────────
ASSISTANT_NAME = "Josh"           # what the assistant calls itself

# ── Security (voice PIN) ──────────────────────────────────
# Set a numeric PIN (0–1000) to protect sensitive tools.
# When you try to use a protected tool (e.g. shutdown, lock screen),
# the assistant will ask you to speak your PIN before executing.
#
# Set to None to disable (all tools run without PIN).
# Change the number to your own secret PIN:
SECURITY_PIN = 2002               # e.g. 742 — set your own number here!

# Which tools require PIN verification before executing:
PROTECTED_TOOLS = {
    "lock_screen",
    "system_power",
    "empty_recycle_bin",
    "create_text_file",
}
# Add or remove tool names from this set to customize what's protected.

# ── Ollama (local LLM) ────────────────────────────────────
OLLAMA_URL = "http://localhost:11434/api/chat"

# Uncomment the LLM model you want to use:
# OLLAMA_MODEL = "qwen2.5:3b"      # Highly recommended: extremely accurate at calling tools
# OLLAMA_MODEL = "llama3.2:3b"     # Good alternative
OLLAMA_MODEL = "llama3.2:1b"     # Fastest, but very bad at calling tools (often hallucinates)

# ── Wake Word Detection (switchable) ───────────────────────
# Two modes — flip WAKE_MODE to switch between them:
#
#   "model"   → Pre-trained OpenWakeWord neural model
#               Fastest, lowest CPU (~1%), most reliable.
#               But limited to: hey_jarvis, alexa, hey_mycroft
#
#   "custom"  → Whisper streaming detection
#               Works with ANY phrase you want (e.g. "hey josh").
#               Slightly more CPU (~5-10% during speech).
#
WAKE_MODE = "model"              # "model" or "custom" — flip to switch!

# Model mode settings (used when WAKE_MODE = "model")
WAKE_MODEL = "hey_jarvis"         # options: hey_jarvis, alexa, hey_mycroft
WAKE_THRESHOLD = 0.5              # confidence 0.0–1.0 (raise to reduce false triggers)

# Custom mode settings (used when WAKE_MODE = "custom")
WAKE_WORD = "jarvis"            # say literally anything you want

# ── Command transcription (Whisper) ────────────────────────
# After the wake word fires, Whisper transcribes your actual command.
# Uncomment the model you want to use:

# WHISPER_MODEL_SIZE = "tiny.en"     # ~40 MB - Fastest, but struggles with accents/stammers
# WHISPER_MODEL_SIZE = "base.en"     # ~75 MB - Good speed, basic accuracy
# WHISPER_MODEL_SIZE = "small.en"    # ~250 MB - Good balance of speed and accuracy
# WHISPER_MODEL_SIZE = "medium.en"   # ~750 MB - Highly accurate, handles most accents well
# WHISPER_MODEL_SIZE = "Systran/faster-distil-whisper-large-v3"  # ~750 MB - Distilled Large-v3
WHISPER_MODEL_SIZE = "deepdml/faster-whisper-large-v3-turbo-ct2" # ~1.6 GB - The absolute best speed/accuracy ratio (Turbo)

SAMPLE_RATE = 16000
WHISPER_COMPUTE_TYPE = "int8"     # int8 = fast on CPU, minimal accuracy loss
MAX_COMMAND_SECONDS = 8           # hard cap so it never listens forever
SILENCE_THRESHOLD = 500           # fallback — auto-calibrated on startup from ambient noise
SILENCE_DURATION = 0.8            # seconds of quiet before it decides you're done talking

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
    "microsoft edge": "msedge",
    "notepad": "notepad",
    "calculator": "calc",
    "calc": "calc",
    "explorer": "explorer",
    "file explorer": "explorer",
    "word": "winword",
    "ms word": "winword",
    "microsoft word": "winword",
    "office": "winword",  # default office to word if they just say office
    "ms office": "winword",
    "excel": "excel",
    "ms excel": "excel",
    "microsoft excel": "excel",
    "powerpoint": "powerpnt",
    "ms powerpoint": "powerpnt",
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
