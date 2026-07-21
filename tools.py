"""
Zaza Assistant — Tools
Every function here is an "action" the LLM can decide to call.
Each one returns a plain string that gets spoken back to the user.
"""

import os
import subprocess
import datetime
import platform
import shutil
import webbrowser
import threading
import ctypes

import psutil

from config import APP_PATHS, FOLDER_PATHS, BASE_DIR


# ── Existing tools (with bug fixes) ──────────────────────


def get_current_time(_args=None):
    now = datetime.datetime.now()
    return f"It's {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d')}."


def get_current_date(_args=None):
    now = datetime.datetime.now()
    return f"Today is {now.strftime('%A, %B %d, %Y')}."


def open_application(args: dict):
    """args: {'app_name': str}"""
    app_name = (args or {}).get("app_name", "").strip().lower()
    if not app_name:
        return "You didn't tell me which app to open."

    target = APP_PATHS.get(app_name)
    if not target:
        # fuzzy fallback: try substring match against known apps
        for key, val in APP_PATHS.items():
            if app_name in key or key in app_name:
                target = val
                break

    if not target:
        # last resort: try running it as typed (works if it's in PATH)
        target = app_name

    try:
        if platform.system() == "Windows":
            os.startfile(target)  # noqa
        else:
            subprocess.Popen([target])
        return f"Opening {app_name}."
    except FileNotFoundError:
        return f"I couldn't find {app_name}. You can add it to APP_PATHS in config.py."
    except Exception:
        return f"Couldn't open {app_name}. Check if it's installed."


def close_application(args: dict):
    """args: {'app_name': str} — kills the process by image name (Windows)."""
    app_name = (args or {}).get("app_name", "").strip().lower()
    if not app_name:
        return "You didn't tell me which app to close."

    process_name = APP_PATHS.get(app_name, app_name)
    exe = process_name if process_name.endswith(".exe") else f"{process_name}.exe"

    try:
        if platform.system() == "Windows":
            result = subprocess.run(
                ["taskkill", "/IM", exe, "/F"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                return f"Closed {app_name}."
            return f"{app_name} doesn't seem to be running."
        else:
            subprocess.run(["pkill", "-f", process_name])
            return f"Closed {app_name}."
    except Exception:
        return f"Couldn't close {app_name}."


def open_folder(args: dict):
    """args: {'folder_name': str} — one of documents/downloads/desktop/pictures, or a raw path."""
    folder_name = (args or {}).get("folder_name", "").strip().lower()
    if not folder_name:
        return "Which folder do you want opened?"

    path = FOLDER_PATHS.get(folder_name, folder_name)
    if not os.path.isdir(path):
        return f"I couldn't find the folder '{folder_name}'."

    try:
        if platform.system() == "Windows":
            os.startfile(path)  # noqa
        else:
            subprocess.Popen(["xdg-open", path])
        return f"Opening {folder_name}."
    except Exception:
        return f"Couldn't open {folder_name}."


def open_file(args: dict):
    """args: {'file_path': str} — opens any file with its default program."""
    file_path = (args or {}).get("file_path", "").strip()
    if not file_path:
        return "Which file should I open?"
    if not os.path.isfile(file_path):
        return "I can't find that file."
    try:
        if platform.system() == "Windows":
            os.startfile(file_path)  # noqa
        else:
            subprocess.Popen(["xdg-open", file_path])
        return f"Opening {os.path.basename(file_path)}."
    except Exception:
        return "Couldn't open that file."


def search_files(args: dict):
    """args: {'query': str, 'directory': str (optional, defaults to Documents)}"""
    query = (args or {}).get("query", "").strip().lower()
    directory = (args or {}).get("directory") or FOLDER_PATHS["documents"]

    if not query:
        return "What file are you looking for?"
    if not os.path.isdir(directory):
        return "That directory doesn't exist."

    matches = []
    for root, _, files in os.walk(directory):
        for f in files:
            if query in f.lower():
                matches.append(os.path.join(root, f))
        if len(matches) >= 5:
            break

    if not matches:
        return f"No files matching '{query}' found."
    listing = "; ".join(os.path.basename(m) for m in matches[:5])
    return f"Found {len(matches)} file(s): {listing}"


def open_website(args: dict):
    """args: {'url': str}"""
    url = (args or {}).get("url", "").strip()
    if not url:
        return "Which website should I open?"
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opening {url}."


def get_system_info(_args=None):
    # Use the system drive on Windows instead of "/" which may pick the wrong drive
    if platform.system() == "Windows":
        drive = os.environ.get("SYSTEMDRIVE", "C:") + "\\"
    else:
        drive = "/"
    total, used, free = shutil.disk_usage(drive)
    free_gb = free // (2**30)
    total_gb = total // (2**30)
    return (
        f"Running {platform.system()} {platform.release()} on {platform.machine()}. "
        f"{free_gb}GB free out of {total_gb}GB."
    )


def get_battery_status(_args=None):
    battery = psutil.sensors_battery()
    if battery is None:
        return "No battery detected — probably running on a desktop."
    plugged = "charging" if battery.power_plugged else "on battery"
    return f"Battery is at {battery.percent}%, currently {plugged}."


# ── New tools ─────────────────────────────────────────────


def set_volume(args: dict):
    """args: {'level': int} — sets system volume to a percentage (0-100)."""
    level = (args or {}).get("level", 50)
    try:
        level = int(level)
        level = max(0, min(100, level))
    except (TypeError, ValueError):
        return "Tell me a number between 0 and 100."

    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
        from comtypes import CLSCTX_ALL
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_, CLSCTX_ALL, None
        )
        volume = interface.QueryInterface(IAudioEndpointVolume)
        volume.SetMasterVolumeLevelScalar(level / 100.0, None)
        return f"Volume set to {level}%."
    except Exception:
        return "Couldn't change the volume. Make sure pycaw is installed."


def media_control(args: dict):
    """args: {'action': str} — play, pause, next, previous."""
    action = (args or {}).get("action", "").strip().lower()
    if not action:
        return "What should I do — play, pause, next track, or previous?"

    VK_MEDIA_PLAY_PAUSE = 0xB3
    VK_MEDIA_NEXT_TRACK = 0xB0
    VK_MEDIA_PREV_TRACK = 0xB1

    key_map = {
        "play": VK_MEDIA_PLAY_PAUSE,
        "pause": VK_MEDIA_PLAY_PAUSE,
        "play pause": VK_MEDIA_PLAY_PAUSE,
        "toggle": VK_MEDIA_PLAY_PAUSE,
        "next": VK_MEDIA_NEXT_TRACK,
        "next track": VK_MEDIA_NEXT_TRACK,
        "skip": VK_MEDIA_NEXT_TRACK,
        "previous": VK_MEDIA_PREV_TRACK,
        "previous track": VK_MEDIA_PREV_TRACK,
        "back": VK_MEDIA_PREV_TRACK,
    }

    vk = key_map.get(action)
    if not vk:
        return f"I don't know the media action '{action}'. Try play, pause, next, or previous."

    try:
        ctypes.windll.user32.keybd_event(vk, 0, 0, 0)
        ctypes.windll.user32.keybd_event(vk, 0, 2, 0)  # key up
        return f"Done — {action}."
    except Exception:
        return "Couldn't send the media key."


def get_clipboard(_args=None):
    """Reads the current clipboard contents."""
    try:
        import pyperclip
        content = pyperclip.paste()
        if not content:
            return "Clipboard is empty."
        if len(content) > 200:
            return f"Clipboard has {len(content)} characters. It starts with: {content[:200]}"
        return f"Clipboard contains: {content}"
    except Exception:
        return "Couldn't read the clipboard."


def set_reminder(args: dict):
    """args: {'minutes': number, 'message': str}"""
    minutes = (args or {}).get("minutes", 1)
    message = (args or {}).get("message", "Time's up!")
    try:
        minutes = float(minutes)
    except (TypeError, ValueError):
        return "Tell me how many minutes for the reminder."

    if minutes <= 0 or minutes > 1440:
        return "Pick a time between 1 minute and 24 hours."

    def _remind():
        from text_to_speech import speak
        speak(f"Reminder: {message}")

    timer = threading.Timer(minutes * 60, _remind)
    timer.daemon = True
    timer.start()

    if minutes == 1:
        return f"Got it — I'll remind you in 1 minute: {message}"
    return f"Got it — I'll remind you in {minutes:.0f} minutes: {message}"


def take_screenshot(_args=None):
    """Takes a screenshot and saves it to the desktop."""
    try:
        from PIL import ImageGrab
        desktop = FOLDER_PATHS.get(
            "desktop", os.path.join(os.path.expanduser("~"), "Desktop")
        )
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        path = os.path.join(desktop, filename)
        img = ImageGrab.grab()
        img.save(path)
        return f"Screenshot saved as {filename} on your desktop."
    except Exception:
        return "Couldn't take a screenshot."


# ── Registry: maps tool name -> (function, JSON schema for the LLM) ──

TOOLS = {
    "get_current_time": {
        "func": get_current_time,
        "description": "Get the current time.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    "get_current_date": {
        "func": get_current_date,
        "description": "Get today's date.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    "open_application": {
        "func": open_application,
        "description": "Open a desktop application by name, e.g. chrome, notepad, vscode, calculator.",
        "parameters": {
            "type": "object",
            "properties": {"app_name": {"type": "string", "description": "Name of the app to open"}},
            "required": ["app_name"],
        },
    },
    "close_application": {
        "func": close_application,
        "description": "Close/kill a running desktop application by name.",
        "parameters": {
            "type": "object",
            "properties": {"app_name": {"type": "string", "description": "Name of the app to close"}},
            "required": ["app_name"],
        },
    },
    "open_folder": {
        "func": open_folder,
        "description": "Open a common folder like documents, downloads, desktop, pictures, or a full path.",
        "parameters": {
            "type": "object",
            "properties": {"folder_name": {"type": "string", "description": "Folder name or full path"}},
            "required": ["folder_name"],
        },
    },
    "open_file": {
        "func": open_file,
        "description": "Open a specific file by its full path with the default program.",
        "parameters": {
            "type": "object",
            "properties": {"file_path": {"type": "string", "description": "Full path to the file"}},
            "required": ["file_path"],
        },
    },
    "search_files": {
        "func": search_files,
        "description": "Search for files by name inside a directory (defaults to Documents).",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Filename or partial filename to search for"},
                "directory": {"type": "string", "description": "Directory to search in (optional)"},
            },
            "required": ["query"],
        },
    },
    "open_website": {
        "func": open_website,
        "description": "Open a website in the default browser.",
        "parameters": {
            "type": "object",
            "properties": {"url": {"type": "string", "description": "URL or domain to open"}},
            "required": ["url"],
        },
    },
    "get_system_info": {
        "func": get_system_info,
        "description": "Get OS info and free disk space.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    "get_battery_status": {
        "func": get_battery_status,
        "description": "Get current battery percentage and charging status.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    "set_volume": {
        "func": set_volume,
        "description": "Set the system volume to a percentage (0-100). Use for 'set volume to 50 percent', 'turn volume up', 'mute' (0), 'max volume' (100), etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "level": {"type": "integer", "description": "Volume level from 0 (mute) to 100 (max)"},
            },
            "required": ["level"],
        },
    },
    "media_control": {
        "func": media_control,
        "description": "Control media playback — play, pause, next track, previous track. Works with Spotify, YouTube, and any media player.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "One of: play, pause, next, previous, skip, back"},
            },
            "required": ["action"],
        },
    },
    "get_clipboard": {
        "func": get_clipboard,
        "description": "Read what's currently copied to the clipboard.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    "set_reminder": {
        "func": set_reminder,
        "description": "Set a timed reminder that will be spoken aloud after the given number of minutes.",
        "parameters": {
            "type": "object",
            "properties": {
                "minutes": {"type": "number", "description": "How many minutes until the reminder"},
                "message": {"type": "string", "description": "What to remind about"},
            },
            "required": ["minutes", "message"],
        },
    },
    "take_screenshot": {
        "func": take_screenshot,
        "description": "Take a screenshot of the entire screen and save it to the desktop.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}


def get_ollama_tool_schema():
    """Formats TOOLS into the schema Ollama's /api/chat expects."""
    schema = []
    for name, spec in TOOLS.items():
        schema.append({
            "type": "function",
            "function": {
                "name": name,
                "description": spec["description"],
                "parameters": spec["parameters"],
            },
        })
    return schema


def execute_tool(name: str, args: dict):
    if name not in TOOLS:
        return f"Unknown tool: {name}"
    return TOOLS[name]["func"](args)
