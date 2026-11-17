#!/usr/bin/env python3
"""
Standalone local voice assistant.

Uses Ollama as the brain. No external agents or other projects required.
"""

from __future__ import annotations

import datetime
import platform
import random
import re
import subprocess
import webbrowser
from typing import Optional

import ollama
import pyttsx3
import speech_recognition as sr

# =============================================================================
# CONFIGURATION — edit these values
# =============================================================================
OLLAMA_HOST = "http://127.0.0.1:11434"
MODEL = "qwen2.5:1.5b"
STT_ENGINE = "google"               # "google" or "whisper"
WAKE_WORD = "jarvis"
OWNER_NAME = "Joel"
ASSISTANT_NAME = "Jarvis"

# Only used when STT_ENGINE = "whisper"
WHISPER_MODEL = "base"              # tiny | base | small | medium
WHISPER_DEVICE = "cpu"              # "cpu" or "cuda"

SYSTEM_PROMPT = f"""You are {ASSISTANT_NAME}, a concise personal voice assistant for {OWNER_NAME}.
You run completely locally using Ollama.

Style rules:
- Calm, direct, and slightly dry humour
- Keep spoken answers short (1 to 3 sentences) unless more detail is asked
- Never invent personal facts about the user

When you need to perform an action, reply with exactly one of these lines and nothing else:
TOOL: get_time
TOOL: lock_screen
TOOL: open_google
TOOL: open_youtube
TOOL: open_url <url>
TOOL: tell_joke
TOOL: system_info
TOOL: exit

If no action is needed, just answer in normal English.
"""

# =============================================================================
# Text-to-speech (offline)
# =============================================================================
engine = pyttsx3.init()
voices = engine.getProperty("voices")
if len(voices) > 1:
    engine.setProperty("voice", voices[1].id)
engine.setProperty("rate", 165)


def speak(text: str) -> None:
    print(f"{ASSISTANT_NAME}: {text}")
    engine.say(text)
    engine.runAndWait()


# =============================================================================
# Speech-to-text
# =============================================================================
_whisper_model = None


def _load_whisper():
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model
    try:
        from faster_whisper import WhisperModel
        print(f"Loading Whisper '{WHISPER_MODEL}' on {WHISPER_DEVICE}...")
        _whisper_model = WhisperModel(
            WHISPER_MODEL, device=WHISPER_DEVICE, compute_type="int8"
        )
        return _whisper_model
    except ImportError:
        speak("faster-whisper not installed. Using Google speech recognition instead.")
        return None
    except Exception as e:
        speak(f"Could not load Whisper: {e}. Falling back to Google.")
        return None


def listen(timeout: float = 8, phrase_limit: float = 12) -> Optional[str]:
    """Listen for one utterance and return the transcript."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.pause_threshold = 0.7
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        print("Listening...")
        try:
            audio = recognizer.listen(
                source, timeout=timeout, phrase_time_limit=phrase_limit
            )
        except sr.WaitTimeoutError:
            return None

    # Local Whisper path
    if STT_ENGINE == "whisper":
        model = _load_whisper()
        if model is not None:
            try:
                import io
                wav_bytes = io.BytesIO(audio.get_wav_data())
                segments, _ = model.transcribe(wav_bytes, language="en", beam_size=1)
                text = " ".join(seg.text for seg in segments).strip()
                if text:
                    print(f"You: {text}")
                    return text
                return None
            except Exception as e:
                print(f"Whisper error: {e}")

    # Google path (default)
    try:
        text = recognizer.recognize_google(audio, language="en-in")
        print(f"You: {text}")
        return text.strip()
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        speak("Speech recognition needs an internet connection right now.")
        return None


def wait_for_wake_word() -> None:
    """Block until the wake word is detected."""
    print(f"Waiting for wake word '{WAKE_WORD}'...")
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.pause_threshold = 0.5
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        while True:
            try:
                audio = recognizer.listen(source, timeout=None, phrase_time_limit=3)
                try:
                    text = recognizer.recognize_google(audio, language="en-in").lower()
                    print(f"(heard: {text})")
                    if WAKE_WORD in text:
                        return
                except (sr.UnknownValueError, sr.RequestError):
                    continue
            except Exception:
                continue


# =============================================================================
# Local tools (self-contained)
# =============================================================================
def tool_get_time() -> str:
    return f"The time is {datetime.datetime.now().strftime('%I:%M %p')}"


def tool_lock_screen() -> str:
    try:
        subprocess.run(["loginctl", "lock-session"], check=False)
        return "Locking the screen now."
    except Exception:
        return "I could not lock the screen on this system."


def tool_open_google() -> str:
    webbrowser.open("https://www.google.com")
    return "Opening Google."


def tool_open_youtube() -> str:
    webbrowser.open("https://www.youtube.com")
    return "Opening YouTube."


def tool_open_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opening {url}"


def tool_tell_joke() -> str:
    jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs.",
        "There are only 10 kinds of people: those who understand binary and those who don't.",
        "A SQL query walks into a bar, walks up to two tables and asks: Can I join you?",
        "Why did the developer go broke? He used up all his cache.",
        "I would tell you a UDP joke, but you might not get it.",
    ]
    return random.choice(jokes)


def tool_system_info() -> str:
    uname = platform.uname()
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.4)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        return (
            f"Running {uname.system} {uname.release} on {uname.machine}. "
            f"CPU at {cpu} percent, memory {mem.percent} percent used, "
            f"disk {disk.percent} percent used."
        )
    except ImportError:
        return (
            f"System: {uname.system} {uname.release} ({uname.machine}). "
            "Install psutil if you want more detailed stats."
        )


def run_tool(raw: str) -> str:
    """Execute a tool command returned by the model."""
    parts = raw.strip().split(maxsplit=1)
    name = parts[0].lower()
    argument = parts[1] if len(parts) > 1 else ""

    if name == "get_time":
        return tool_get_time()
    if name == "lock_screen":
        return tool_lock_screen()
    if name == "open_google":
        return tool_open_google()
    if name == "open_youtube":
        return tool_open_youtube()
    if name == "open_url":
        return tool_open_url(argument) if argument else "Please give me a URL."
    if name == "tell_joke":
        return tool_tell_joke()
    if name == "system_info":
        return tool_system_info()
    if name == "exit":
        return "__EXIT__"

    return f"I do not know the tool '{name}'."


# =============================================================================
# LLM (Ollama)
# =============================================================================
client = ollama.Client(host=OLLAMA_HOST)
history: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]


def ask_llm(user_text: str) -> str:
    history.append({"role": "user", "content": user_text})

    try:
        response = client.chat(
            model=MODEL,
            messages=history,
            options={"temperature": 0.55, "num_ctx": 4096},
        )
        reply = response["message"]["content"].strip()
    except Exception as e:
        reply = f"I cannot reach the local model. Is Ollama running? ({e})"

    # Keep history short so the context window stays healthy
    if len(history) > 14:
        history[:] = [history[0]] + history[-8:]

    history.append({"role": "assistant", "content": reply})
    return reply


def extract_tool(reply: str) -> Optional[str]:
    match = re.search(r"TOOL:\s*(.+)", reply, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


# =============================================================================
# Main loop
# =============================================================================
def main() -> None:
    hour = datetime.datetime.now().hour
    if hour < 12:
        greeting = "Good morning"
    elif hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    speak(f"{greeting}, {OWNER_NAME}. {ASSISTANT_NAME} is online.")

    while True:
        # Wait for wake word
        wait_for_wake_word()
        speak("Yes?")

        # Listen for the actual request
        query = listen(timeout=10, phrase_limit=15)
        if not query:
            speak("I did not catch that.")
            continue

        lower = query.lower()

        # Fast local exit
        if any(word in lower for word in ("exit", "quit", "goodbye", "shut down", "go to sleep")):
            speak("Going offline. Goodbye.")
            break

        # Send to local LLM
        reply = ask_llm(query)

        # Handle tool or normal reply
        tool_command = extract_tool(reply)
        if tool_command:
            result = run_tool(tool_command)
            if result == "__EXIT__":
                speak("Going offline. Goodbye.")
                break
            speak(result)
            history.append({"role": "user", "content": f"[tool result] {result}"})
            history.append({"role": "assistant", "content": result})
        else:
            clean = re.sub(r"TOOL:\s*.+", "", reply).strip()
            if clean:
                speak(clean)


if __name__ == "__main__":
    main()
