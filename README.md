# chatz

A full-stack AI assistant application featuring:
- **Conversational AI** powered by Meta Llama-3 (via HuggingFace Inference API)
- **Speech recognition** and **text-to-speech** for voice interaction
- **Persistent conversation history** with MongoDB
- **Frontend** (likely React) and **Python backend**

---

## Project Structure

```
chatz/
├── llama_assistant.py      # Main CLI assistant (Python)
├── requirements.txt        # Python dependencies
├── backend/                # Backend API and logic (Python)
├── frontend/               # Frontend app (JS/React)
├── .git/                   # Git repository
```

### backend/
- `main.py`         — Backend entry point
- `models.py`       — Data models
- `db.py`           — Database connection logic
- `chatz_llm.py`    — LLM integration

### frontend/
- `src/`            — Frontend source code
- `public/`         — Static assets
- `package.json`    — Frontend dependencies
- `README.md`       — Frontend-specific documentation

---

## Features

- **Conversational AI**: Chat with an assistant powered by Llama-3 (HuggingFace Inference API)
- **Voice Support**: Speak to the assistant and hear responses (SpeechRecognition, pyttsx3)
- **Conversation Management**: Start, continue, delete, and rename conversations
- **Password Protection**: Optionally protect conversations with a password
- **Persistent Storage**: All conversations are stored in MongoDB
- **CLI and Web UI**: Interact via command line or web interface

---

## Setup

### 1. Python Backend & CLI Assistant

#### Install dependencies
```bash
pip install -r requirements.txt
```

#### Environment variables
- Set your HuggingFace API key as `HF_TOKEN` (already set in llama_assistant.py, but best practice is to use environment variables)
- Set your MongoDB connection string if needed

#### Run the CLI assistant
```bash
python llama_assistant.py
```

### 2. Backend API
Navigate to `backend/` and follow any instructions in its files (e.g., `main.py`).

### 3. Frontend
Navigate to `frontend/` and follow its `README.md` for setup (likely involves `npm install` and `npm start`).

---

## Dependencies

- `transformers`, `huggingface_hub`, `torch` — LLM API
- `pymongo` — MongoDB client
- `SpeechRecognition`, `pyaudio` — Speech-to-text
- `pyttsx3` — Text-to-speech

---

## Usage

- **CLI**: Run `python llama_assistant.py` and follow prompts to chat, manage conversations, and use voice features.
- **Web**: Start the backend and frontend as described above, then access the web UI in your browser.

---

## Notes
- Make sure MongoDB is accessible from your environment.
- For voice features, ensure your microphone and speakers are working.
- For more details, see the `frontend/README.md` and backend source files.

---

## License
This project is for educational and personal use. Please check individual package licenses for details. 