# Zaza Assistant

Offline, local, voice-controlled PC assistant. No API keys, no subscriptions,
no internet required after setup (aside from two one-time model downloads).
Runs entirely on your HP 255 G10.

Wake word + command transcription (faster-whisper) → local LLM decides which
tool to call (Ollama + Qwen2.5:3b) → action executes (open app/file/folder,
check time, etc.) → text-to-speech reads the result back (pyttsx3).

**Both the wake word and your commands go through Whisper now.** Vosk was
tried first for the wake word (cheaper on CPU/battery for always-on
listening) but its small model struggled with non-dictionary words like
"zaza." Whisper is meaningfully more accurate for both, at the cost of
higher idle CPU/battery use since it's actively transcribing short chunks
every couple seconds while waiting, rather than passively listening. Vosk
is left in the project as an optional fallback if you'd rather trade some
accuracy back for lower power draw — see the note in `config.py`.

Total disk footprint: ~5-9GB (Ollama model + Whisper tiny.en + base.en,
Vosk optional). Your 80GB free is plenty.

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

This installs Vosk, faster-whisper, sounddevice, pyttsx3, and the packaging
tools (pyinstaller, pystray).

Note: `sounddevice` needs PortAudio — on Windows this ships bundled with the
pip wheel, so **you almost certainly don't need anything extra here.** Only
if `python main.py` later throws a PortAudio-related error, try:

```powershell
pip install pipwin
pipwin install pyaudio
```

⚠️ Heads up: `pipwin` depends on `js2py`, which is unmaintained and breaks on
newer Python versions (`RuntimeError: Your python version made changes to
the bytecode`). If you hit that, skip pipwin entirely and instead download a
prebuilt PyAudio wheel manually from
https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio matching your Python
version, then `pip install <downloaded_file>.whl`. In practice this whole
step is rarely needed — don't run it preemptively.

---

## 3. Speech models — no manual download needed

Whisper downloads both models it needs automatically the first time you run
`main.py`: `tiny.en` (~40MB, for wake-word polling) and `base.en` (~150MB,
for command transcription). That first run needs internet; after that it's
cached locally and fully offline.

**Skip this whole section unless you want the Vosk fallback.** If you'd
rather trade some accuracy for lower CPU/battery use on the wake word (see
the note in `config.py`), you can optionally set up Vosk instead:

1. Go to: https://alphacephei.com/vosk/models
2. Download `vosk-model-small-en-us-0.15.zip`
3. Extract it into `zaza-assistant/models/`
4. Rename the extracted folder to exactly: `vosk-model-small-en-us`
5. In `main.py`, swap `from whisper_stt import listen_for_wake_word` back to
   `from speech_to_text import listen_for_wake_word`

---

## 4. Run it

Voice mode (mic required):

```powershell
python main.py
```

Say **"Hey Zaza"**, wait for it to say "Yes?", then give your command — talk
normally, it stops recording on its own once you go quiet:
- "what time is it"
- "what's today's date"
- "open chrome"
- "open my documents folder"
- "close notepad"
- "what's my battery at"
- "search my documents for CSC 466"

Text mode (no mic, good for quick testing):

```powershell
python main.py --text
```

Say "stop" or "exit" any time to shut it down.

---

## 5. Customize it

**Rename the assistant / change wake word** → `config.py`:
```python
ASSISTANT_NAME = "Zaza"
WAKE_WORD = "hey zaza"
```
With Whisper handling the wake word now, made-up names like "Zaza" work
fine — it's much better than Vosk at unusual words. You can go back to
something short and common if you ever switch back to the optional Vosk
fallback (see step 3).

**Trade wake-word responsiveness/accuracy for CPU/battery** → `config.py`:
```python
WAKE_WHISPER_MODEL_SIZE = "tiny.en"  # bump to "base.en" for more accuracy, slower polling
WAKE_POLL_SECONDS = 2.5              # shorter = more responsive, more CPU use
```

**Adjust how long it waits for you to finish talking** → `config.py`:
```python
MAX_COMMAND_SECONDS = 8     # hard cap, in case silence detection fails
SILENCE_DURATION = 1.2      # seconds of quiet before it decides you're done
```

**Trade Whisper speed for accuracy (or vice versa)** → `config.py`:
```python
WHISPER_MODEL_SIZE = "base.en"   # tiny.en = fastest, small.en = most accurate
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
| Wake word never triggers | Whisper is much better at unusual words than Vosk was, but check `WAKE_WORD` in config.py matches what you're actually saying — it's a substring match, case-insensitive |
| Mic not picking up anything | Check Windows mic permissions: Settings → Privacy → Microphone |
| Commands transcribe poorly | Bump `WHISPER_MODEL_SIZE` up to `small.en` in config.py for more accuracy (slower) |
| It cuts you off mid-sentence or waits too long | Tune `SILENCE_DURATION` (lower = cuts off sooner, higher = waits longer) in config.py |
| First run hangs after "Loading Whisper..." | That's the one-time model download (~40MB + ~150MB) — needs internet, just let it finish |
| High CPU/fan noise while idle | Expected — it's polling with Whisper every `WAKE_POLL_SECONDS`. Increase that value, or switch to the optional Vosk fallback (step 3) for near-zero idle cost |
| App won't open by short name | Add its full `.exe` path to `APP_PATHS` in config.py |
| Slow responses | 3B model should be fast on 16GB RAM; if sluggish, close other heavy apps, or try `llama3.2:1b` for speed over accuracy |

---

## 7. Package it as a standalone app (no terminal, no venv activation)

Once voice mode works fine via `python main.py`, turn it into a real
installed-feeling app:

```powershell
venv\Scripts\activate
build.bat
```

This produces `dist\ZazaAssistant.exe` — a double-clickable app, no Python
or terminal needed to run it. The `models\` folder gets copied next to it
automatically (the .exe reads it from there at runtime, not bundled inside).

Note: the Whisper model cache (downloaded in step 3) lives in your Windows
user profile, not the project folder, so it's already available to the
packaged .exe too — no extra copying needed there.

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
- A **tray icon** (navy/gold "Z", matches your PenWork4Me brand) appears in
  the system tray — right-click it → Quit to stop the assistant cleanly.
- All prints/errors get redirected to `zaza.log` next to the .exe, so if
  something's not working, check that file first.

**Full picture after this step:** PC boots → Ollama service already running
in background → Task Scheduler silently launches `ZazaAssistant.exe` →
tray icon appears → it's listening for "Hey Zaza." No terminal, no venv,
no manual anything.

**Rebuilding after code changes:** just re-run `build.bat`. It overwrites
the old .exe; the scheduled task keeps pointing at the same path so you
don't need to re-register it.

---

## 8. Performance notes for your specs (16GB RAM, 512GB SSD)

- `qwen2.5:3b` quantized sits around 2GB in RAM while loaded — no strain
- Whisper `tiny.en` (wake word) and `base.en` (commands) both run
  comfortably on CPU — wake-word polling adds ongoing background CPU use
  while idle, worth knowing if you run on battery a lot (see step 6)
- First response after starting Ollama is slower (model loads into memory),
  subsequent ones are fast
- Everything here runs 100% offline once Ollama and both Whisper models are
  downloaded — no data leaves your machine, no recurring cost
