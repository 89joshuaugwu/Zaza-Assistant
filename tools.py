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

from config import APP_PATHS, FOLDER_PATHS


def get_current_time(_args=None) -> str:
    now = datetime.datetime.now()
    return f"It's {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d')}."


def get_current_date(_args=None) -> str:
    now = datetime.datetime.now()
    return f"Today is {now.strftime('%A, %B %d, %Y')}."


def open_application(args: dict) -> str:
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
        return f"I couldn't find '{app_name}' installed. Add it to APP_PATHS in config.py with its full path."
    except Exception as e:
        return f"Something went wrong opening {app_name}: {e}"


def close_application(args: dict) -> str:
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
    except Exception as e:
        return f"Couldn't close {app_name}: {e}"


def open_folder(args: dict) -> str:
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
    except Exception as e:
        return f"Couldn't open {folder_name}: {e}"


def open_file(args: dict) -> str:
    """args: {'file_path': str} — opens any file with its default program."""
    file_path = (args or {}).get("file_path", "").strip()
    if not file_path:
        return "Which file should I open?"
    if not os.path.isfile(file_path):
        return f"I can't find the file: {file_path}"
    try:
        if platform.system() == "Windows":
            os.startfile(file_path)  # noqa
        else:
            subprocess.Popen(["xdg-open", file_path])
        return f"Opening {os.path.basename(file_path)}."
    except Exception as e:
        return f"Couldn't open that file: {e}"


def search_files(args: dict) -> str:
    """args: {'query': str, 'directory': str (optional, defaults to Documents)}"""
    query = (args or {}).get("query", "").strip().lower()
    directory = (args or {}).get("directory") or FOLDER_PATHS["documents"]

    if not query:
        return "What file are you looking for?"
    if not os.path.isdir(directory):
        return f"That directory doesn't exist: {directory}"

    matches = []
    for root, _, files in os.walk(directory):
        for f in files:
            if query in f.lower():
                matches.append(os.path.join(root, f))
        if len(matches) >= 5:
            break

    if not matches:
        return f"No files matching '{query}' found in {directory}."
    listing = "; ".join(os.path.basename(m) for m in matches[:5])
    return f"Found {len(matches)} file(s): {listing}"


def open_website(args: dict) -> str:
    """args: {'url': str}"""
    url = (args or {}).get("url", "").strip()
    if not url:
        return "Which website should I open?"
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opening {url}."


def get_system_info(_args=None) -> str:
    total, used, free = shutil.disk_usage("/")
    free_gb = free // (2**30)
    total_gb = total // (2**30)
    return (
        f"Running {platform.system()} {platform.release()} on {platform.machine()}. "
        f"{free_gb}GB free out of {total_gb}GB."
    )


def get_battery_status(_args=None) -> str:
    try:
        import psutil
        battery = psutil.sensors_battery()
        if battery is None:
            return "No battery detected — probably running on a desktop."
        plugged = "charging" if battery.power_plugged else "on battery"
        return f"Battery is at {battery.percent}%, currently {plugged}."
    except ImportError:
        return "Install psutil (pip install psutil) for battery status."


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


def execute_tool(name: str, args: dict) -> str:
    if name not in TOOLS:
        return f"Unknown tool: {name}"
    return TOOLS[name]["func"](args)
