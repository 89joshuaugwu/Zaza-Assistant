# Josh Assistant (formerly Zaza)

Offline, local, voice-controlled PC assistant. No API keys, no subscriptions,
no internet required after setup (aside from one-time model downloads).

Say **"Hey Jarvis"** → it says "Yes?" → give your command → it does it and
reads the result back. Everything runs 100% on your machine.

**Pipeline:**
Wake word detection (OpenWakeWord) → command transcription (faster-whisper)
→ local LLM decides which tool to call (Ollama + Qwen2.5:3b) → streams response word-by-word
→ text-to-speech reads the result back in real-time using a dedicated background queue (pyttsx3).

Total disk footprint: ~3-5GB (Ollama model + Whisper base.en + OpenWakeWord).

---

## 1. Install Ollama (the local LLM runtime)

Download and install: https://ollama.com/download/windows

After install, open a terminal (PowerShell) and confirm it's running:

```powershell
ollama --version
```

Pull the model (does this once, ~2GB download):

```powershell
ollama pull qwen2.5:3b
```

Test it works:

```powershell
ollama run qwen2.5:3b "say hello"
```

If that replies, Ollama's good. Leave it running in the background —
`ollama serve` starts automatically as a service on Windows after install,
so you usually don't need to start it manually.

---

## 2. Set up Python environment

Extract the zip anywhere, e.g. `C:\Users\<you>\zaza-assistant`. Open a
terminal in that folder:

```powershell
cd zaza-assistant
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

This installs OpenWakeWord, faster-whisper, sounddevice, pyttsx3, pycaw,
pyperclip, and the packaging tools (pyinstaller, pystray).

---

## 3. Speech models — no manual download needed

**OpenWakeWord** downloads its wake word model (~few MB) automatically
the first time you run `main.py`.

**Whisper** downloads the `base.en` model (~150MB) automatically on first
run for command transcription.

Both need internet once; after that everything is cached locally and
fully offline.

---

## 4. Run it

Voice mode (mic required):

```powershell
python main.py
```

On startup it checks your mic (shows volume level), loads the wake word
engine, then says "Josh is online. Say 'Hey Jarvis' to activate."

Say **"Hey Jarvis"**, wait for it to say "Yes?", then give your command:
- "what time is it"
- "what's today's date"
- "open chrome"
- "open my documents folder"
- "close notepad"
- "what's my battery at"
- "search my documents for CSC 466"
- "set volume to 50 percent"
- "pause the music" / "next track" / "skip"
- "what's in my clipboard"
- "remind me in 10 minutes to check the oven"
- "take a screenshot"

Text mode (no mic, good for quick testing):

```powershell
python main.py --text
```

Say "stop" or "exit" any time to shut it down.

---

## 5. Customize it

**Rename the assistant** → `config.py`:
```python
ASSISTANT_NAME = "Josh"   # what it calls itself in speech
```
Note: the wake word ("Hey Jarvis") is determined by the OpenWakeWord model,
not the assistant name. See below to change it.

**Change the wake word** → `config.py`:
```python
WAKE_MODEL = "hey_jarvis"   # also available: "alexa", "hey_mycroft"
WAKE_THRESHOLD = 0.5        # raise to reduce false triggers, lower for easier triggering
```

**Trade Whisper speed for accuracy (or vice versa)** → `config.py`:
```python
WHISPER_MODEL_SIZE = "base.en"   # tiny.en = fastest, small.en = most accurate
```

**Adjust how long it waits for you to finish talking** → `config.py`:
```python
MAX_COMMAND_SECONDS = 8     # hard cap, in case silence detection fails
SILENCE_DURATION = 0.8      # seconds of quiet before it decides you're done
```

**Change TTS voice** → `config.py`:
```python
TTS_VOICE_INDEX = 0   # 0 = default, try 1, 2, etc. for different voices
```
To see available voices:
```powershell
python -c "import pyttsx3; e=pyttsx3.init(); [print(i,v.name) for i,v in enumerate(e.getProperty('voices'))]"
```

**Add apps it can open** → `config.py`, `APP_PATHS` dict. If an app doesn't
open with just its short name, give the full `.exe` path instead:
```python
APP_PATHS = {
    "antigravity": r"C:\Users\<you>\AppData\Local\Programs\Antigravity\Antigravity.exe",
}
```

**Add new tools/actions** → `tools.py`. Pattern to follow:
1. Write a function `def my_tool(args: dict) -> str:` that returns a string
2. Register it in the `TOOLS` dict at the bottom with a description + JSON
   schema for its arguments — the LLM reads that description to decide when
   to call it, so be specific.

No other file needs touching — `llm_brain.py` auto-generates the tool list
Ollama sees from whatever's in `TOOLS`.

---

## 6. Troubleshooting

| Problem | Fix |
|---|---|
| "I can't reach Ollama" | Run `ollama serve` manually in a terminal, leave it open |
| Wake word never triggers | Check mic permissions (Settings → Privacy → Microphone), try lowering `WAKE_THRESHOLD` in config.py to 0.3 |
| Startup says "Mic seems silent" | Check Windows mic permissions, make sure no other app has exclusive mic access |
| Mic not picking up anything | Check Windows mic permissions: Settings → Privacy → Microphone |
| Commands transcribe poorly | Bump `WHISPER_MODEL_SIZE` up to `small.en` in config.py for more accuracy (slower) |
| It cuts you off mid-sentence or waits too long | Tune `SILENCE_DURATION` (lower = cuts off sooner, higher = waits longer) in config.py |
| First run hangs after "Loading..." | That's the one-time model download — needs internet, just let it finish |
| App won't open by short name | Add its full `.exe` path to `APP_PATHS` in config.py |
| Slow responses | 3B model should be fast on 16GB RAM; if sluggish, close other heavy apps, or try `llama3.2:1b` for speed over accuracy |
| Volume control doesn't work | Make sure pycaw is installed: `pip install pycaw` |

---

## 7. Package it as a standalone app (no terminal, no venv activation)

Once voice mode works fine via `python main.py`, turn it into a real
installed-feeling app:

```powershell
venv\Scripts\activate
build.bat
```

This produces `dist\ZazaAssistant.exe` — a double-clickable app, no Python
or terminal needed to run it.

**Make it launch automatically at login:**

Right-click `setup_task_scheduler.bat` → **Run as administrator**. This
registers it with Windows Task Scheduler to start silently every time you
log in — no console window, no manual launch.

To test immediately without logging out/in:
```powershell
schtasks /Run /TN "ZazaAssistant"
```

To remove the auto-launch later: run `remove_task_scheduler.bat` as admin.

**Since `--noconsole` hides all output**, two things replace it:
- A **tray icon** (navy/gold, first letter of your assistant name) appears in
  the system tray — right-click it → Quit to stop the assistant cleanly.
- All prints/errors get redirected to `zaza.log` next to the .exe, so if
  something's not working, check that file first.

**Full picture after this step:** PC boots → Ollama service already running
in background → Task Scheduler silently launches `ZazaAssistant.exe` →
tray icon appears → it's listening for "Hey Jarvis." No terminal, no venv,
no manual anything.

**Rebuilding after code changes:** just re-run `build.bat`. It overwrites
the old .exe; the scheduled task keeps pointing at the same path so you
don't need to re-register it.

---

## 8. Available tools (what you can say)

| Tool | Example Commands |
|---|---|
| Time | "what time is it" |
| Date | "what's today's date" |
| Open app | "open chrome", "open notepad", "open calculator" |
| Close app | "close notepad", "close chrome" |
| Open folder | "open my documents", "open downloads" |
| Open file | "open [full path to file]" |
| Search files | "search my documents for homework" |
| Open website | "open google.com", "go to youtube" |
| System info | "how much disk space do I have" |
| Battery | "what's my battery at" |
| Volume | "set volume to 50 percent", "mute", "max volume" |
| Media | "pause the music", "next track", "skip", "play" |
| Clipboard | "what's in my clipboard", "what did I copy" |
| Reminder | "remind me in 10 minutes to check the oven" |
| Screenshot | "take a screenshot" |
| Type text | "type hello world", "write a note in notepad" |
| Lock screen | "lock my computer", "lock screen" |
| Power controls | "shutdown my PC", "restart", "put my PC to sleep" |
| List running apps | "what apps are running", "what's open" |
| Minimize windows | "show desktop", "minimize everything" |
| Read file | "read me [file path]", "what's in [file path]" |
| Create file | "create a file called notes", "make a note called todo" |
| Uptime | "how long has my PC been running" |
| Recycle Bin | "empty the trash", "clear the recycle bin" |

The assistant also remembers the last 5 exchanges, so follow-up commands
like "open the first one" after a file search work.

---

## 9. Security & PIN Verification

If certain actions are too sensitive (e.g., shutting down the PC or emptying the trash), you can protect them with a voice PIN.
1. Set `SECURITY_PIN = 1234` in `config.py`.
2. Add the tool names to the `PROTECTED_TOOLS` list.
3. When requested, the assistant will pause and ask you to speak your PIN (e.g. "one two three four") before executing the action.

---

## 10. Testing & Diagnostics

The project currently uses manual end-to-end testing rather than automated suites like `pytest`.
- **Voice Test:** Run `python main.py`
- **Text-Only Test:** Run `python main.py --text` (bypasses microphone, great for testing LLM logic)
- **Microphone Diagnostics:** Run `python diagnose_mic.py` if the wake word isn't triggering to calibrate your ambient noise and test audio thresholds.

---

## 11. Performance notes for your specs (16GB RAM, 512GB SSD)

- `qwen2.5:3b` quantized sits around 2GB in RAM while loaded — no strain
- OpenWakeWord uses ~1-3% CPU for wake word detection (much less than the
  old Whisper polling approach)
- Whisper `base.en` (commands) runs comfortably on CPU
- First response after starting Ollama is slower (model loads into memory),
  subsequent ones are fast
- Everything here runs 100% offline once all models are downloaded — no
  data leaves your machine, no recurring cost
