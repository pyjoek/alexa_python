#!/usr/bin/env python3
"""
Local-LLM voice assistant (rebuild of alexa_python)

Features:
- Brain = your local Ollama model
- Wake-word mode ("Jarvis")
- Optional fully-offline STT via faster-whisper
- Expandable local tools
- Short conversation memory
"""

from __future__ import annotations

import datetime
import platform
import random
import re
import shutil
import subprocess
import webbrowser
from typing import Optional

import ollama
import pyttsx3
import speech_recognition as sr

# =============================================================================
# CONFIG — edit these
# =============================================================================
OLLAMA_HOST = "http://127.0.0.1:11434"
MODEL = "qwen2.5:1.5b"              # change to whatever you pulled
STT_ENGINE = "google"               # "google" or "whisper"
WAKE_WORD = "jarvis"                # say this to activate
OWNER_NAME = "Joel"
ASSISTANT_NAME = "Jarvis"

# Whisper settings (only used if STT_ENGINE == "whisper")
WHISPER_MODEL = "base"              # tiny / base / small / medium
WHISPER_DEVICE = "cpu"              # "cpu" or "cuda"

SYSTEM_PROMPT = f"""You are {ASSISTANT_NAME}, a concise personal voice assistant for {OWNER_NAME}.
You run 100% locally on his machine using Ollama.

Style:
- Calm, direct, slightly dry humour
- Keep spoken replies short (1–3 sentences) unless he asks for more
- Never invent personal facts about him

Available tools — when you need one, reply with EXACTLY one of these lines and nothing else:
TOOL: get_time
TOOL: lock_screen
TOOL: open_google
TOOL: open_youtube
TOOL: open_url <url>
TOOL: tell_joke
TOOL: system_info
TOOL: exit

If no tool is needed, just answer in normal English.
"""

# =============================================================================
# Voice output (fully offline)
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
        print(f"Loading Whisper model '{WHISPER_MODEL}' on {WHISPER_DEVICE}...")
        _whisper_model = WhisperModel(WHISPER_MODEL, device=WHISPER_DEVICE, compute_type="int8")
        return _whisper_model
    except ImportError:
        speak("faster-whisper is not installed. Falling back to Google speech recognition.")
        return None
    except Exception as e:
        speak(f"Could not load Whisper: {e}. Falling back to Google.")
        return None


def listen(timeout: float = 8, phrase_limit: float = 12) -> Optional[str]:
    """Capture one utterance and return the transcript."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.pause_threshold = 0.7
        r.adjust_for_ambient_noise(source, duration=0.3)
        print("Listening...")
        try:
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
        except sr.WaitTimeoutError:
            return None

    # ---- Local Whisper path ----
    if STT_ENGINE == "whisper":
        model = _load_whisper()
        if model is not None:
            try:
                # speech_recognition gives us WAV data in memory
                import io
                import wave
                raw = io.BytesIO(audio.get_wav_data())
                segments, _ = model.transcribe(raw, language="en", beam_size=1)
                text = " ".join(seg.text for seg in segments).strip()
                if text:
                    print(f"You: {text}")
                    return text
                return None
            except Exception as e:
                print(f"Whisper error: {e}")
                # fall through to Google

    # ---- Google path (default) ----
    try:
        text = r.recognize_google(audio, language="en-in")
        print(f"You: {text}")
        return text.strip()
    except sr.UnknownValueError:
        return None
    except sr.RequestError:
        speak("Speech service needs internet right now.")
        return None


def listen_for_wake_word() -> bool:
    """Block until the wake word is heard. Returns True when detected."""
    print(f"Waiting for wake word '{WAKE_WORD}'...")
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.pause_threshold = 0.5
        r.adjust_for_ambient_noise(source, duration=0.3)
        while True:
            try:
                audio = r.listen(source, timeout=None, phrase_time_limit=3)
                try:
                    text = r.recognize_google(audio, language="en-in").lower()
                    print(f"(heard: {text})")
                    if WAKE_WORD in text:
                        return True
                except (sr.UnknownValueError, sr.RequestError):
                    continue
            except Exception:
                continue


# =============================================================================
# Local tools
# =============================================================================
def get_time() -> str:
    return f"The time is {datetime.datetime.now().strftime('%I:%M %p')}"


def lock_screen() -> str:
    try:
        subprocess.run(["loginctl", "lock-session"], check=False)
        return "Locking the screen now."
    except Exception:
        return "I couldn't lock the screen on this system."


def open_google() -> str:
    webbrowser.open("https://www.google.com")
    return "Opening Google."


def open_youtube() -> str:
    webbrowser.open("https://www.youtube.com")
    return "Opening YouTube."


def open_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opening {url}"


def tell_joke() -> str:
    jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs.",
        "There are only 10 kinds of people: those who understand binary and those who don't.",
        "A SQL query walks into a bar, walks up to two tables and asks: Can I join you?",
        "Why did the developer go broke? He used up all his cache.",
        "I would tell you a UDP joke, but you might not get it.",
    ]
    return random.choice(jokes)


def system_info() -> str:
    uname = platform.uname()
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        return (
            f"Running {uname.system} {uname.release} on {uname.machine}. "
            f"CPU {cpu} percent, memory {mem.percent} percent used, "
            f"disk {disk.percent} percent used."
        )
    except ImportError:
        return f"System: {uname.system} {uname.release} ({uname.machine}). Install psutil for more details."


TOOLS = {
    "get_time": lambda: get_time(),
    "lock_screen": lambda: lock_screen(),
    "open_google": lambda: open_google(),
    "open_youtube": lambda: open_youtube(),
    "tell_joke": lambda: tell_joke(),
    "system_info": lambda: system_info(),
}


def run_tool(raw: str) -> str:
    """raw is the full TOOL: line, e.g. 'open_url https://example.com'"""
    parts = raw.strip().split(maxsplit=1)
    name = parts[0].lower()
    arg = parts[1] if len(parts) > 1 else ""

    if name == "open_url":
        return open_url(arg) if arg else "Please give me a URL."
    if name == "exit":
        return "__EXIT__"
    fn = TOOLS.get(name)
    if not fn:
        return f"I don't know the tool '{name}'."
    return fn()


# =============================================================================
# LLM brain
# =============================================================================
client = ollama.Client(host=OLLAMA_HOST)
history: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]


def ask_llm(user_text: str) -> str:
    history.append({"role": "user", "content": user_text})

    try:
        resp = client.chat(
            model=MODEL,
            messages=history,
            options={"temperature": 0.55, "num_ctx": 4096},
        )
        reply = resp["message"]["content"].strip()
    except Exception as e:
        reply = f"I can't reach the local model. Is Ollama running? ({e})"

    # Keep history short
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
    greet = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"

    speak(f"{greet}, {OWNER_NAME}. {ASSISTANT_NAME} is online and fully local.")

    while True:
        # 1. Wait for wake word
        listen_for_wake_word()
        speak("Yes?")

        # 2. Listen for the actual command
        query = listen(timeout=10, phrase_limit=15)
        if not query:
            speak("I didn't catch that.")
            continue

        lower = query.lower()

        # Quick local exit without bothering the model
        if any(w in lower for w in ("exit", "quit", "goodbye", "shut down", "go to sleep")):
            speak("Going offline. Goodbye.")
            break

        # 3. Ask the local LLM
        reply = ask_llm(query)

        # 4. Tool or normal reply
        tool_raw = extract_tool(reply)
        if tool_raw:
            result = run_tool(tool_raw)
            if result == "__EXIT__":
                speak("Going offline. Goodbye.")
                break
            speak(result)
            # Feed result back so the model knows what happened
            history.append({"role": "user", "content": f"[tool result] {result}"})
            history.append({"role": "assistant", "content": result})
        else:
            clean = re.sub(r"TOOL:\s*.+", "", reply).strip()
            if clean:
                speak(clean)


if __name__ == "__main__":
    main()
