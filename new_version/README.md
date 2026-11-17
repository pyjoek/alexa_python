# Alexa Python — New Version (Local LLM)

Full rebuild of the original voice assistant.

**Key improvements over the original:**
- Brain runs on **your local Ollama model** (no Wikipedia / pywhatkit / cloud APIs for thinking)
- Free conversation + short-term memory
- Optional **wake word** ("Jarvis") so it doesn't listen all the time
- Optional **local Whisper** speech-to-text (fully offline)
- Expandable local tools

## Requirements

### 1. Ollama (you already have this)
```bash
# Make sure a model is pulled
docker exec -it ollama ollama pull qwen2.5:1.5b
# or a stronger one if you have RAM: qwen3:4b / llama3.2:3b etc.
```

### 2. Python packages
```bash
cd new_version
pip install -r requirements.txt
```

> On Linux if `pyaudio` fails:
> ```bash
> sudo apt install portaudio19-dev python3-pyaudio
> ```

### Optional: Local Whisper (fully offline STT)
```bash
pip install faster-whisper
```
Then set `STT_ENGINE = "whisper"` in `assistant.py`.

## How to run

```bash
python assistant.py
```

By default it starts in **wake-word mode**:
- It waits silently until you say **"Jarvis"**
- Then it listens for your command
- After answering it goes back to waiting for the wake word

Say **"exit"**, **"quit"** or **"goodbye"** to stop completely.

## Configuration (top of assistant.py)

```python
OLLAMA_HOST = "http://127.0.0.1:11434"
MODEL = "qwen2.5:1.5b"
STT_ENGINE = "google"          # "google" or "whisper"
WAKE_WORD = "jarvis"
OWNER_NAME = "Joel"
ASSISTANT_NAME = "Jarvis"
```

## Tools the model can use

The assistant can trigger these by saying `TOOL: name`:

| Tool            | What it does                  |
|-----------------|-------------------------------|
| get_time        | Current time                  |
| lock_screen     | Lock the session              |
| open_google     | Open Google                   |
| open_youtube    | Open YouTube                  |
| open_url        | Open any URL you mention      |
| tell_joke       | Random programmer joke        |
| system_info     | Basic CPU / memory / disk     |
| exit            | Shut down the assistant       |

You can easily add more tools in the `TOOLS` dict.

## Architecture

1. Wake word detected → listen for command
2. Speech → text (Google or local Whisper)
3. Text + history → local Ollama
4. Reply (or tool) → spoken with pyttsx3 (offline)
5. Back to wake-word listening
