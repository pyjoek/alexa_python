# Alexa Python — New Version (Local LLM)

This is a full rebuild of the original voice assistant.

**Old version problems:**
- Hardcoded `if/elif` for every command
- Relied on cloud services (Google Speech, Wikipedia, pywhatkit/YouTube, etc.)
- No real conversation ability

**New version:**
- Uses **your local Ollama model** as the brain
- Free-form conversation (not just keyword matching)
- Keeps speech recognition + text-to-speech
- Local tools only (time, lock screen, open sites, jokes, etc.)
- Conversation history so it remembers what you said

## Requirements

1. Ollama running locally (you already have this from `local_LLM`)
2. A model pulled (recommended: `qwen2.5:1.5b` or `qwen3:4b`)

```bash
# If Ollama is not already running
docker run -d --name ollama --restart unless-stopped -p 127.0.0.1:11434:11434 -v ollama:/root/.ollama ollama/ollama

# Pull a model if needed
docker exec -it ollama ollama pull qwen2.5:1.5b
```

## Install Python packages

```bash
cd new_version
pip install -r requirements.txt
```

> Note: `pyaudio` can be annoying on Linux. If it fails:
> ```bash
> sudo apt install portaudio19-dev python3-pyaudio
> ```

## Run

```bash
python assistant.py
```

It will greet you, then listen continuously.
Say **"exit"**, **"quit"** or **"goodbye"** to stop.

## Configuration

Edit the top of `assistant.py`:

```python
OLLAMA_HOST = "http://127.0.0.1:11434"
MODEL = "qwen2.5:1.5b"          # change to whatever you have
SYSTEM_PROMPT = "..."           # personality
```

## How it works

1. Listens with microphone (`speech_recognition`)
2. Transcribes (currently Google STT — easy to swap later for Whisper)
3. Sends text + conversation history to your local Ollama
4. Speaks the reply with `pyttsx3` (fully offline)
5. Can call simple local tools when the model asks for them

No Wikipedia, no pywhatkit, no internet required for thinking.
