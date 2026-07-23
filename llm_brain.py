"""
Zaza Assistant — LLM Brain
Sends the user's command to a local Ollama model with tool definitions.
If the model decides to call a tool, we execute it and feed the result back
so the model can give a natural final answer.

Features:
- Sliding window of recent in-session exchanges (5 turns)
- Persistent memory across sessions (saved to disk)
- Personality-driven system prompt
"""

import json
from collections import deque
from datetime import datetime

import requests

from config import OLLAMA_URL, OLLAMA_MODEL, ASSISTANT_NAME
from tools import get_ollama_tool_schema, execute_tool
from memory import get_recent_summary, save_interaction
from text_to_speech import speak

# ── Personality & system prompt ──────────────────────────

def _build_system_prompt() -> str:
    """Builds a dynamic system prompt with personality and memory context."""
    hour = datetime.now().hour
    if hour < 12:
        time_context = "It's morning."
    elif hour < 17:
        time_context = "It's afternoon."
    else:
        time_context = "It's evening."

    prompt = f"""You are {ASSISTANT_NAME}, a sharp, witty local voice assistant running on the user's PC.
You're not a corporate chatbot — you're more like a helpful friend who lives in the computer.

{time_context}

Personality:
- Be conversational and natural, not robotic. Use casual, friendly language.
- Show enthusiasm when doing tasks. Say things like "On it!", "Got it!", "Done!" naturally.
- If the user says "thanks" or compliments you, respond warmly and briefly.
- If something goes wrong, be honest but reassuring — don't dump error messages.
- Add brief personality — a little humor or energy is good, but keep it short.

You have these tools:
- Time/date, open/close apps, open folders/files, search files, open websites
- System info, battery status, volume control, media playback (play/pause/next/skip)
- Read clipboard, set reminders, take screenshots, type text into apps
- Lock screen, shutdown/restart/sleep PC, list running apps, minimize all windows
- Read file contents aloud, create text files, system uptime, empty recycle bin

Rules:
- If the user's request matches a tool, call it immediately. Don't describe what you'd do — just do it.
- Keep replies SHORT (1-2 sentences max). Everything gets read aloud via text-to-speech.
- For follow-ups, use conversation context. Understand "it", "that", "the first one", etc.
- Never invent file paths or app names you weren't told — ask if unclear.
- When typing text for the user, use the type_text tool — don't just say what you'd type.
"""

    # Add persistent memory context if available
    memory = get_recent_summary(3)
    if memory:
        prompt += f"\nRecent history from past sessions:\n{memory}\n"

    return prompt


# Sliding window of in-session conversation (5 user+assistant pairs)
_history = deque(maxlen=10)


def _chat_stream(messages: list) -> dict:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "tools": get_ollama_tool_schema(),
        "stream": True,
    }
    resp = requests.post(OLLAMA_URL, json=payload, stream=True, timeout=60)
    resp.raise_for_status()

    full_message = {"role": "assistant", "content": ""}
    sentence_buffer = ""
    started_printing = False

    for line in resp.iter_lines():
        if line:
            chunk = json.loads(line)
            msg = chunk.get("message", {})

            # Content streaming
            content = msg.get("content", "")
            if content:
                if not started_printing:
                    print(f"{ASSISTANT_NAME}: ", end="", flush=True)
                    started_printing = True
                    
                full_message["content"] += content
                print(content, end="", flush=True)
                sentence_buffer += content

                # Check for sentence completion to dispatch to TTS
                if any(p in sentence_buffer for p in ['. ', '? ', '! ', '\n']):
                    speak(sentence_buffer.strip(), print_out=False)
                    sentence_buffer = ""

            # Tool calls streaming
            tc = msg.get("tool_calls", [])
            if tc:
                if "tool_calls" not in full_message:
                    full_message["tool_calls"] = []
                full_message["tool_calls"].extend(tc)

            if chunk.get("done"):
                break

    if sentence_buffer.strip():
        speak(sentence_buffer.strip(), print_out=False)

    if started_printing:
        print()  # Final newline after streaming ends
        
    return {"message": full_message}


def think(user_text: str) -> str:
    """Takes a transcribed command, returns the final spoken reply."""
    messages = [
        {"role": "system", "content": _build_system_prompt()},
    ]

    # Include in-session conversation history for follow-up context
    messages.extend(list(_history))

    messages.append({"role": "user", "content": user_text})

    try:
        response = _chat_stream(messages)
    except requests.exceptions.ConnectionError:
        err = "I can't reach Ollama. Make sure it's running — try 'ollama serve' in a terminal."
        speak(err)
        return err
    except Exception:
        err = "Something went wrong talking to the model."
        speak(err)
        return err

    message = response.get("message", {})
    tool_calls = message.get("tool_calls")

    if not tool_calls:
        reply = message.get("content", "").strip()
        
        # Robust fallback for models that output raw JSON or python-like function calls
        if not tool_calls:
            import re, json
            
            # 1. Try to find a python-like call: tool_name({"arg": "val"})
            for match in re.finditer(r'([a-zA-Z0-9_]+)\s*\(\s*(\{.*?\})\s*\)', reply):
                name = match.group(1)
                if name in TOOLS:
                    try:
                        args = json.loads(match.group(2))
                        tool_calls = [{"function": {"name": name, "arguments": args}}]
                        break
                    except Exception:
                        pass
            
            # 2. Try to find JSON objects line by line
            if not tool_calls:
                for line in reply.split('\n'):
                    if "{" not in line or "}" not in line: continue
                    
                    # Extract the JSON portion of the line
                    json_str = line[line.find("{"):line.rfind("}")+1]
                    # Quick fix for trailing commas before closing braces
                    json_str = re.sub(r',\s*\}', '}', json_str)
                    
                    try:
                        parsed = json.loads(json_str)
                        fobj = None
                        
                        # Support OpenAI-style wrappers {"type":"function", "function": {"name": ...}}
                        if "type" in parsed and parsed["type"] == "function" and "function" in parsed:
                            if isinstance(parsed["function"], dict):
                                fobj = parsed["function"]
                            elif isinstance(parsed["function"], str):
                                fobj = {"name": parsed["function"]}
                                if "parameters" in parsed: fobj["parameters"] = parsed["parameters"]
                                elif "param" in parsed: fobj["parameters"] = parsed["param"]
                        # Support direct JSON {"name": ...}
                        elif "name" in parsed:
                            fobj = parsed
                            
                        # If a valid tool is found
                        if fobj and "name" in fobj and fobj["name"] in TOOLS:
                            args = fobj.get("parameters", fobj.get("arguments", fobj.get("param", {})))
                            if isinstance(args, str):
                                try: args = json.loads(args)
                                except Exception: args = {}
                            if isinstance(args, dict):
                                tool_calls = [{"function": {"name": fobj["name"], "arguments": args}}]
                                break
                    except Exception:
                        pass

        if not tool_calls:
            if not reply:
                reply = "I didn't quite catch that."
                speak(reply)
            # Save to both in-session and persistent memory
            _history.append({"role": "user", "content": user_text})
            _history.append({"role": "assistant", "content": reply})
            save_interaction(user_text, reply)
            return reply

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
                
        # Auto-correct hallucinated tool names like "open_notepad" -> "open_application"
        if name.startswith("open_") and name not in ["open_application", "open_folder", "open_file", "open_website"]:
            app_name = name.replace("open_", "")
            name = "open_application"
            if isinstance(args, dict):
                args["app_name"] = app_name
                
        if name.startswith("close_") and name not in ["close_application", "close_active_window"]:
            app_name = name.replace("close_", "")
            name = "close_application"
            if isinstance(args, dict):
                args["app_name"] = app_name

        try:
            result = execute_tool(name, args)
        except Exception as e:
            result = f"Error executing tool {name}: {e}"
            print(result)
            
        messages.append({
            "role": "tool",
            "content": result,
        })

    try:
        final = _chat_stream(messages)
        reply = final.get("message", {}).get("content", "").strip()
        if not reply:
            reply = "Done."
            speak(reply)
    except Exception:
        reply = "Done."
        speak(reply)

    # Save to both in-session and persistent memory
    _history.append({"role": "user", "content": user_text})
    _history.append({"role": "assistant", "content": reply})
    save_interaction(user_text, reply)

    return reply
