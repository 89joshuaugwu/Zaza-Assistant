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

from config import APP_PATHS, FOLDER_PATHS, BASE_DIR, SECURITY_PIN, PROTECTED_TOOLS


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
    """args: {'app_name': str} — kills the process by matching name (Windows/Linux)."""
    import psutil
    app_name = (args or {}).get("app_name", "").strip().lower()
    if not app_name:
        return "You didn't tell me which app to close."

    # 1. Check if we have a known mapping in APP_PATHS
    mapped_name = APP_PATHS.get(app_name, app_name)
    exe_name = mapped_name if mapped_name.endswith(".exe") else f"{mapped_name}.exe"
    
    killed = 0
    # 2. Iterate through all running processes
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            p_name = proc.info['name'].lower()
            # Match against known exe name OR fuzzy match the spoken word
            if p_name == exe_name or app_name in p_name.replace(".exe", "") or mapped_name in p_name.replace(".exe", ""):
                proc.kill()
                killed += 1
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    if killed > 0:
        return f"Closed {app_name}."
    return f"I couldn't find {app_name} running."


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


def search_the_web(args: dict):
    """args: {'query': str}"""
    query = (args or {}).get("query", "").strip()
    if not query:
        return "What do you want me to search for?"
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))
        if not results:
            return f"I couldn't find any results for {query}."
        
        snippets = [f"{r.get('title', '')}: {r.get('body', '')}" for r in results]
        combined = " ".join(snippets)
        return f"Search results for '{query}': {combined[:600]}..."
    except ImportError:
        return "The duckduckgo-search module is not installed."
    except Exception as e:
        return f"Search failed: {e}"


def close_active_window(_args=None):
    if platform.system() == "Windows":
        try:
            import pyautogui
            pyautogui.hotkey('alt', 'f4')
            return "Closed active window."
        except ImportError:
            return "The pyautogui module is not installed."
        except Exception as e:
            return f"Couldn't close window: {e}"
    return "This tool only works on Windows."


def switch_window(_args=None):
    if platform.system() == "Windows":
        try:
            import pyautogui
            pyautogui.hotkey('alt', 'tab')
            return "Switched window."
        except ImportError:
            return "The pyautogui module is not installed."
        except Exception as e:
            return f"Couldn't switch window: {e}"
    return "This tool only works on Windows."


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

    import datetime
    target_time = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
    time_str = target_time.strftime("%I:%M %p")  # e.g., 04:30 PM

    def _remind():
        from text_to_speech import speak
        speak(f"Reminder: {message}")

    timer = threading.Timer(minutes * 60, _remind)
    timer.daemon = True
    timer.start()

    return f"Got it — I've set your reminder. I will remind you at exactly {time_str} ({minutes} minutes from now) about: {message}"


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


def type_text(args: dict):
    """Types text into the currently focused window (or opens an app first).
    Uses clipboard paste for reliability — works with any characters."""
    text = (args or {}).get("text", "").strip()
    if not text:
        return "What should I type?"

    app_name = (args or {}).get("app_name", "").strip().lower()
    if app_name:
        # Open the app first, then wait for it to focus
        open_application({"app_name": app_name})
        import time
        time.sleep(2)

    try:
        import pyperclip
        import time

        # Save current clipboard, paste our text, then restore
        old_clipboard = ""
        try:
            old_clipboard = pyperclip.paste()
        except Exception:
            pass

        pyperclip.copy(text)
        time.sleep(0.1)

        # Simulate Ctrl+V via Windows keybd_event
        VK_CONTROL = 0x11
        VK_V = 0x56
        KEYEVENTF_KEYUP = 0x0002

        ctypes.windll.user32.keybd_event(VK_CONTROL, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_V, 0, 0, 0)
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
        ctypes.windll.user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

        time.sleep(0.3)
        try:
            pyperclip.copy(old_clipboard)  # restore clipboard
        except Exception:
            pass

        return "Done — typed the text."
    except Exception:
        return "Couldn't type the text. Make sure the target window is focused."


def lock_screen(_args=None):
    """Locks the Windows workstation."""
    try:
        ctypes.windll.user32.LockWorkStation()
        return "Locking your screen now."
    except Exception:
        return "Couldn't lock the screen."


def system_power(args: dict):
    """args: {'action': str} — shutdown, restart, sleep, or cancel."""
    action = (args or {}).get("action", "").strip().lower()

    if action in ("shutdown", "shut down", "power off"):
        subprocess.Popen(["shutdown", "/s", "/t", "60"])
        return "Shutting down in 60 seconds. Say 'cancel shutdown' to stop."
    elif action in ("restart", "reboot"):
        subprocess.Popen(["shutdown", "/r", "/t", "60"])
        return "Restarting in 60 seconds. Say 'cancel shutdown' to stop."
    elif action == "sleep":
        subprocess.Popen(["rundll32.exe", "powrprof.dll,SetSuspendState", "0", "1", "0"])
        return "Putting your PC to sleep."
    elif action in ("cancel", "cancel shutdown", "abort"):
        subprocess.Popen(["shutdown", "/a"])
        return "Shutdown cancelled."
    else:
        return "I can shutdown, restart, sleep, or cancel a pending shutdown."


def list_running_apps(_args=None):
    """Lists the most notable running applications."""
    try:
        # Get unique process names, filter out system processes
        system_procs = {"svchost", "csrss", "wininit", "services", "lsass",
                        "smss", "dwm", "conhost", "dllhost", "sihost",
                        "fontdrvhost", "winlogon", "logonui", "system",
                        "registry", "idle", "runtimebroker", "searchhost",
                        "startmenuexperiencehost", "shellexperiencehost",
                        "textinputhost", "taskhostw", "ctfmon", "audiodg"}
        apps = set()
        for proc in psutil.process_iter(["name"]):
            name = proc.info["name"]
            if name:
                base = name.lower().replace(".exe", "")
                if base not in system_procs and not base.startswith("svchost"):
                    apps.add(name.replace(".exe", ""))
        if not apps:
            return "No notable apps running."
        # Sort and limit
        app_list = sorted(apps)[:15]
        return f"Running apps: {', '.join(app_list)}"
    except Exception:
        return "Couldn't list running apps."


def minimize_all_windows(_args=None):
    """Minimizes all windows (show desktop)."""
    try:
        # Simulate Win+D (show desktop)
        VK_LWIN = 0x5B
        VK_D = 0x44
        KEYEVENTF_KEYUP = 0x0002
        ctypes.windll.user32.keybd_event(VK_LWIN, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_D, 0, 0, 0)
        import time
        time.sleep(0.05)
        ctypes.windll.user32.keybd_event(VK_D, 0, KEYEVENTF_KEYUP, 0)
        ctypes.windll.user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)
        return "Done — showing the desktop."
    except Exception:
        return "Couldn't minimize windows."


def read_file_contents(args: dict):
    """args: {'file_path': str} — reads and speaks the contents of a text file."""
    file_path = (args or {}).get("file_path", "").strip()
    if not file_path:
        return "Which file should I read?"
    if not os.path.isfile(file_path):
        return "I can't find that file."
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(2000)  # limit to 2000 chars for TTS
        if not content.strip():
            return "The file is empty."
        if len(content) >= 2000:
            return f"Here's the beginning of the file: {content}... (file is longer, I read the first 2000 characters)"
        return f"Here's what the file says: {content}"
    except Exception:
        return "Couldn't read that file. It might not be a text file."


def create_text_file(args: dict):
    """args: {'filename': str, 'content': str, 'directory': str (optional)}"""
    filename = (args or {}).get("filename", "").strip()
    content = (args or {}).get("content", "").strip()
    directory = (args or {}).get("directory", "").strip()

    if not filename:
        return "What should I name the file?"
    if not content:
        return "What should I write in the file?"

    # Default to desktop
    if not directory:
        directory = FOLDER_PATHS.get(
            "desktop", os.path.join(os.path.expanduser("~"), "Desktop")
        )

    # Add .txt if no extension
    if "." not in filename:
        filename += ".txt"

    path = os.path.join(directory, filename)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Created {filename} on your desktop."
    except Exception:
        return f"Couldn't create the file."


def get_system_uptime(_args=None):
    """Returns how long the PC has been running."""
    try:
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.datetime.now() - boot_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes = remainder // 60
        if hours > 0:
            return f"Your PC has been on for {hours} hours and {minutes} minutes."
        return f"Your PC has been on for {minutes} minutes."
    except Exception:
        return "Couldn't determine uptime."


def empty_recycle_bin(_args=None):
    """Empties the Windows recycle bin."""
    try:
        # SHEmptyRecycleBin(hwnd, path, flags)
        # flags: 0x07 = SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x07)
        return "Recycle bin emptied."
    except Exception:
        return "Couldn't empty the recycle bin."


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
    "search_the_web": {
        "func": search_the_web,
        "description": "Search the internet for real-time information, weather, or facts. DO NOT use this for local files.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "The search query"}},
            "required": ["query"],
        },
    },
    "close_active_window": {
        "func": close_active_window,
        "description": "Closes the currently active/foreground window.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    "switch_window": {
        "func": switch_window,
        "description": "Switches to the previous window (simulates Alt+Tab).",
        "parameters": {"type": "object", "properties": {}, "required": []},
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
    "type_text": {
        "func": type_text,
        "description": "Type text into the currently focused application window. Can optionally open an app first (e.g. notepad) then type into it. Use this when the user says 'write ... in notepad', 'type ... in word', etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The text to type"},
                "app_name": {"type": "string", "description": "Optional: app to open first before typing (e.g. notepad, word)"},
            },
            "required": ["text"],
        },
    },
    "lock_screen": {
        "func": lock_screen,
        "description": "Lock the Windows screen. Use when the user says 'lock my computer', 'lock screen', 'lock my PC'.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    "system_power": {
        "func": system_power,
        "description": "Shutdown, restart, sleep the PC, or cancel a pending shutdown. Shutdown/restart have a 60-second delay so the user can cancel.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "One of: shutdown, restart, sleep, cancel"},
            },
            "required": ["action"],
        },
    },
    "list_running_apps": {
        "func": list_running_apps,
        "description": "List notable running applications (filters out system processes). Use when the user asks 'what apps are running', 'what's open', etc.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    "minimize_all_windows": {
        "func": minimize_all_windows,
        "description": "Minimize all windows and show the desktop. Use for 'show desktop', 'minimize everything', 'clear my screen'.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    "read_file_contents": {
        "func": read_file_contents,
        "description": "Read and speak the contents of a text file. Use when the user says 'read me [file]', 'what's in [file]', etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {"type": "string", "description": "Full path to the text file to read"},
            },
            "required": ["file_path"],
        },
    },
    "create_text_file": {
        "func": create_text_file,
        "description": "Create a new text file with content. Defaults to saving on the desktop. Use for 'create a file called X with Y', 'make a note called X'.",
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {"type": "string", "description": "Name for the file (e.g. 'notes', 'todo')"},
                "content": {"type": "string", "description": "Text content to write in the file"},
                "directory": {"type": "string", "description": "Optional: directory to save in (defaults to desktop)"},
            },
            "required": ["filename", "content"],
        },
    },
    "get_system_uptime": {
        "func": get_system_uptime,
        "description": "Check how long the PC has been running since last boot.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
    "empty_recycle_bin": {
        "func": empty_recycle_bin,
        "description": "Empty the Windows recycle bin permanently. Use when the user says 'empty the trash', 'clear recycle bin'.",
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

    # Check if this tool requires PIN verification
    if SECURITY_PIN is not None and name in PROTECTED_TOOLS:
        verified = _verify_pin()
        if not verified:
            return "Access denied. PIN verification failed."

    return TOOLS[name]["func"](args)


# ── Voice PIN verification ────────────────────────────────

def _parse_spoken_number(text: str):
    """Parse a number from Whisper transcription of spoken digits.

    Handles:
      - Raw digits: "742" → 742
      - Digit words: "seven four two" → 742
      - Full words: "seven hundred forty two" → 742
      - Mixed: "7 hundred 42" → 742
    """
    if not text:
        return None

    text = text.lower().strip().rstrip(".!?,")

    # 1) Try direct integer parse
    try:
        return int(text)
    except ValueError:
        pass

    # 2) Try extracting all digit characters
    digits_only = "".join(c for c in text if c.isdigit())
    if digits_only:
        try:
            return int(digits_only)
        except ValueError:
            pass

    words = text.replace("-", " ").replace(",", " ").split()
    # Remove filler words
    words = [w for w in words if w not in ("and", "the", "a", "is", "my", "pin")]

    # 3) Full word-to-number FIRST (for "seven hundred forty two" → 742)
    #    This must run before digit-by-digit to avoid "seven" + "two" → 72
    ones = {
        "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
        "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
        "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
        "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
        "eighteen": 18, "nineteen": 19,
    }
    tens = {
        "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
        "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    }

    result = 0
    current = 0
    found_any = False
    has_multiplier = any(w in ("hundred", "thousand") for w in words)
    has_tens = any(w in tens for w in words)

    for w in words:
        if w in ones:
            current += ones[w]
            found_any = True
        elif w in tens:
            current += tens[w]
            found_any = True
        elif w == "hundred":
            if current == 0:
                current = 1
            current *= 100
            found_any = True
        elif w == "thousand":
            if current == 0:
                current = 1
            current *= 1000
            result += current
            current = 0
            found_any = True

    if found_any and (has_multiplier or has_tens):
        return result + current

    # 4) Digit-by-digit fallback (for "seven four two" → 742)
    word_to_digit = {
        "zero": "0", "oh": "0", "o": "0",
        "one": "1", "two": "2", "to": "2", "too": "2",
        "three": "3", "four": "4", "for": "4",
        "five": "5", "six": "6", "seven": "7",
        "eight": "8", "nine": "9",
    }

    digit_str = ""
    for w in words:
        if w in word_to_digit:
            digit_str += word_to_digit[w]
    if digit_str:
        try:
            return int(digit_str)
        except ValueError:
            pass

    # 5) If full word found something without multiplier (single word like "fifty")
    if found_any:
        return result + current

    return None


def _verify_pin() -> bool:
    """Ask the user to speak their PIN and verify it.
    Gives 2 attempts before denying access."""
    from text_to_speech import speak, wait_until_done
    from whisper_stt import listen_for_command

    for attempt in range(2):
        if attempt == 0:
            speak("This action requires admin access. What's your security PIN?")
        else:
            speak("Wrong PIN. Try once more.")

        wait_until_done()
        
        spoken = listen_for_command()
        print(f"  PIN attempt {attempt + 1}: heard '{spoken}'")

        if not spoken:
            speak("I didn't hear anything.")
            continue

        # Check for cancel
        if spoken.lower().strip() in ("cancel", "never mind", "nevermind", "stop", "forget it"):
            speak("Cancelled.")
            return False

        parsed = _parse_spoken_number(spoken)
        print(f"  Parsed number: {parsed}")

        if parsed is not None and parsed == SECURITY_PIN:
            speak("Verified.")
            return True

    speak("Access denied.")
    return False
