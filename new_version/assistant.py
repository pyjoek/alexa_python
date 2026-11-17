#!/usr/bin/env python3
"""
Local-LLM voice assistant (rebuild of alexa_python)
Uses Ollama for thinking instead of cloud services + hardcoded rules.
"""

import datetime
import json
import re
import subprocess
import webbrowser
from typing import Optional

import ollama
import pyttsx3
import speech_recognition as sr

# ----------------------------------------------------------------------------
# Config — change these to match your local setup
# ----------------------------------------------------------------------------
OLLAMA_HOST = "http://127.0.0.1:11434"
MODEL = "qwen2.5:1.5b"          # or qwen3:4b, llama3.2, etc.
OWNER_NAME = "Joel"
ASSISTANT_NAME = "Jarvis"

SYSTEM_PROMPT = f"""You are {ASSISTANT_NAME}, a concise and helpful voice assistant for {OWNER_NAME}.
You run completely offline on his local machine.

Personality:
- Direct, calm, slightly dry sense of humour
- Keep spoken answers short (1-3 sentences) unless he asks for detail
- Never invent facts about him

You can use these tools by writing exactly one of these lines when needed:
TOOL: get_time
TOOL: lock_screen
TOOL: open_google
TOOL: open_youtube
TOOL: tell_joke
TOOL: exit

Otherwise just reply normally in plain text. Do not explain the tools.
"""

# ----------------------------------------------------------------------------
# Voice I/O
# ----------------------------------------------------------------------------
engine = pyttsx3.init()
voices = engine.getProperty("voices")
# Prefer a female/clear voice if available
if len(voices) > 1:
    engine.setProperty("voice", voices[1].id)
engine.setProperty("rate", 165)


def speak(text: str):
    print(f"{ASSISTANT_NAME}: {text}")
    engine.say(text)
    engine.runAndWait()


def listen() -> Optional[str]:
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.pause_threshold = 0.8
        r.adjust_for_ambient_noise(source, duration=0.4)
        print("Listening...")
        try:
            audio = r.listen(source, timeout=8, phrase_time_limit=12)
        except sr.WaitTimeoutError:
            return None

    try:
        # Still using Google STT for accuracy.
        # Later you can swap this for local Whisper / Vosk.
        query = r.recognize_google(audio, language="en-in")
        print(f"You: {query}")
        return query.strip()
    except sr.UnknownValueError:
        speak("I didn't catch that. Can you say it again?")
        return None
    except sr.RequestError:
        speak("Speech recognition needs internet right now. Check your connection.")
        return None


# ----------------------------------------------------------------------------
# Local tools the model can call
# ----------------------------------------------------------------------------
def get_time() -> str:
    now = datetime.datetime.now().strftime("%I:%M %p")
    return f"The time is {now}"


def lock_screen() -> str:
    try:
        # Works on most Linux desktops
        subprocess.run(["loginctl", "lock-session"], check=False)
        return "Locking the screen."
    except Exception:
        return "I couldn't lock the screen on this system."


def open_google() -> str:
    webbrowser.open("https://www.google.com")
    return "Opening Google."


def open_youtube() -> str:
    webbrowser.open("https://www.youtube.com")
    return "Opening YouTube."


def tell_joke() -> str:
    jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs.",
        "There are only 10 kinds of people in the world: those who understand binary and those who don't.",
        "A SQL query walks into a bar, walks up to two tables and asks: Can I join you?",
        "Why did the developer go broke? Because he used up all his cache.",
    ]
    import random
    return random.choice(jokes)


TOOLS = {
    "get_time": get_time,
    "lock_screen": lock_screen,
    "open_google": open_google,
    "open_youtube": open_youtube,
    "tell_joke": tell_joke,
}


def run_tool(name: str) -> str:
    fn = TOOLS.get(name)
    if not fn:
        return f"I don't know the tool '{name}'."
    return fn()


# ----------------------------------------------------------------------------
# LLM brain (Ollama)
# ----------------------------------------------------------------------------
client = ollama.Client(host=OLLAMA_HOST)

history = [
    {"role": "system", "content": SYSTEM_PROMPT},
]


def ask_llm(user_text: str) -> str:
    history.append({"role": "user", "content": user_text})

    try:
        response = client.chat(
            model=MODEL,
            messages=history,
            options={
                "temperature": 0.6,
                "num_ctx": 4096,
            },
        )
        reply = response["message"]["content"].strip()
    except Exception as e:
        reply = f"I can't reach the local model right now. Is Ollama running? ({e})"

    # Keep history reasonable
    if len(history) > 16:
        # keep system + last few turns
        history[:] = [history[0]] + history[-10:]

    history.append({"role": "assistant", "content": reply})
    return reply


def extract_tool(reply: str) -> Optional[str]:
    """Look for TOOL: name in the model reply."""
    match = re.search(r"TOOL:\s*(\w+)", reply, re.IGNORECASE)
    if match:
        return match.group(1).lower()
    return None


# ----------------------------------------------------------------------------
# Main loop
# ----------------------------------------------------------------------------
def main():
    hour = datetime.datetime.now().hour
    if hour < 12:
        greet = "Good morning"
    elif hour < 18:
        greet = "Good afternoon"
    else:
        greet = "Good evening"

    speak(f"{greet}, {OWNER_NAME}. {ASSISTANT_NAME} is online and running fully local.")

    while True:
        query = listen()
        if not query:
            continue

        lower = query.lower()

        # Quick local exits (don't even bother the model)
        if any(w in lower for w in ("exit", "quit", "goodbye", "shut down", "stop listening")):
            speak("Goodbye. Going offline.")
            break

        # Ask the local LLM
        reply = ask_llm(query)

        # Check if the model wants a tool
        tool_name = extract_tool(reply)
        if tool_name:
            if tool_name == "exit":
                speak("Goodbye.")
                break
            tool_result = run_tool(tool_name)
            speak(tool_result)
            # Optional: feed the tool result back so the model knows it happened
            history.append({"role": "user", "content": f"[tool result] {tool_result}"})
            history.append({"role": "assistant", "content": tool_result})
        else:
            # Clean any leftover TOOL: lines just in case
            clean = re.sub(r"TOOL:\s*\w+", "", reply).strip()
            if clean:
                speak(clean)


if __name__ == "__main__":
    main()
