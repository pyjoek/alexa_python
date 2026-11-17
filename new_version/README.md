# Local Voice Assistant

A self-contained voice assistant that runs entirely on your machine.

It uses your local Ollama model as the brain. No cloud AI, no external agents, no other projects required.

## Features

- Wake-word activation ("Jarvis")
- Free conversation powered by local LLM
- Short-term conversation memory
- Optional fully offline speech-to-text (Whisper)
- Offline text-to-speech
- Simple local tools (time, lock screen, open sites, system info, jokes)

## Requirements

1. **Ollama** running locally with any model you like
   ```bash
   # Example
   ollama pull qwen2.5:1.5b
   ```

2. **Python packages**
   ```bash
   pip install -r requirements.txt
   ```

   On Linux if PyAudio fails:
   ```bash
   sudo apt install portaudio19-dev python3-pyaudio
   ```

3. **(Optional)** Fully offline speech recognition
   ```bash
   pip install faster-whisper
   ```
   Then set `STT_ENGINE = "whisper"` in `assistant.py`.

## Run

```bash
python assistant.py
```

The assistant starts in wake-word mode. Say **"Jarvis"** to activate it, then speak your request.

Say **"goodbye"**, **"exit"** or **"quit"** to stop.

## Configuration

All settings are at the top of `assistant.py`:

```python
OLLAMA_HOST = "http://127.0.0.1:11434"
MODEL = "qwen2.5:1.5b"
STT_ENGINE = "google"          # or "whisper"
WAKE_WORD = "jarvis"
OWNER_NAME = "Joel"
ASSISTANT_NAME = "Jarvis"
```

## Available Tools

The model can trigger these when needed:

| Tool          | Action                        |
|---------------|-------------------------------|
| get_time      | Tell current time             |
| lock_screen   | Lock the desktop              |
| open_google   | Open Google in browser        |
| open_youtube  | Open YouTube                  |
| open_url      | Open any URL you give it      |
| tell_joke     | Tell a short joke             |
| system_info   | Basic CPU / RAM / disk info   |
| exit          | Shut down the assistant       |

You can add more tools by editing the `TOOLS` section in `assistant.py`.

## Notes

- This project is completely independent. It does not import or depend on any other repository or agent.
- Speech-to-text defaults to Google for better accuracy. Switch to Whisper when you want full offline operation.
- Text-to-speech is already offline (`pyttsx3`).
