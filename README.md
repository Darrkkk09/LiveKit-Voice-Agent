# VAIU AI - Voice Agent Phone Number Collection System

An end-to-end, production-ready AI Voice Agent built for the **VAIU AI**. The agent naturally collects, parses, validates, and stores 10-digit Indian mobile numbers through natural conversation in English, Hindi, and Hinglish.

Built using **Option A: LiveKit Agents**, **Deepgram STT**, **Microsoft Edge-TTS**, **FastAPI**, **SQLite**, and **React + Tailwind CSS**.

---

## 📋 Deliverables Checklist

- [x] **Public GitHub Repository** with clean folder structure.
- [x] **README.md** with complete setup steps and environment variable requirements.
- [x] **parsePhoneNumber() module** with inline comments and 100% deterministic parsing (0% LLM).
- [x] **Working Voice Agent** (LiveKit Agents + Deepgram + Edge-TTS) running locally.
- [x] **Backend API + Database** (FastAPI + SQLite) storing validated records.
- [x] **Web Dashboard** (React + Tailwind CSS) with live data, search/filter, stats, and delete actions.
- [x] **Unit Test Suite** covering all grouping styles, language patterns, multipliers, self-corrections, and validation rules.

---

## 🏗️ Repository Architecture

```text
LiveKit-Voice-Agent/
├── backend/
│   ├── agent.py               # LiveKit Voice Agent worker (State Machine, Audio Streaming, Edge-TTS)
│   ├── phone_parser.py        # 100% Deterministic multilingual phone number parser
│   ├── server.py              # FastAPI REST server with SQLite database
│   ├── test_parser.py         # Pytest test suite covering all grouping & language edge cases
│   ├── requirements.txt       # Python dependencies
│   └── .env.example           # Environment template file
└── frontend/
    ├── src/
    │   ├── App.jsx            # React dashboard UI with Axios integration
    │   ├── main.jsx           # React app entrypoint
    │   └── style.css          # Tailwind CSS styles
    ├── index.html             # Vite HTML entrypoint
    ├── vite.config.js         # Vite configuration with React & Tailwind plugins
    └── package.json           # Frontend dependencies
```

---

## ⚡ Key Features & Implementation Details

| Feature | Description | Status |
| :--- | :--- | :---: |
| **Deterministic Parsing** | `phone_parser.py` uses regex token normalization & dictionaries — 0% LLM guessing | ✅ |
| **Indian Mobile Format** | Strictly validates 10 digits starting with `6`, `7`, `8`, or `9` (`^[6-9]\d{9}$`) | ✅ |
| **Grouping Styles** | Handles singles, pairs, triples, 5+5 chunks, and full digit streams | ✅ |
| **Multilingual Support** | English, Hindi (transliterated & Devanagari), Hinglish (`en`, `hi`, `mixed`) | ✅ |
| **Special Patterns** | `double 7` → 77, `triple 9` → 999, `do 8` → 88, `oh`/`shunya`/`sifar` → 0 | ✅ |
| **Self-Corrections** | Intercepts correction words (`wait`, `sorry`, `galat`, `phir se`) and restarts accumulation | ✅ |
| **Pause & Resume** | Waits up to 4 seconds during silent pauses before prompting user to continue | ✅ |
| **Digit-by-Digit Confirmation**| Reads back number digit by digit (`"9… 8… 7… 6… 5… 4… 3… 2… 1… 0"`) | ✅ |
| **Pre-STT Noise Layer** | Silero VAD + WebRTC APM noise suppression filtering before STT | ✅ |
| **Backend REST API** | FastAPI SQLite endpoints (`POST`, `GET`, `DELETE` `/api/phone`) | ✅ |
| **Web Dashboard** | React + Tailwind dashboard with live search, language breakdown stats & delete actions | ✅ |

---

## ⚙️ Environment Variables

Create a `backend/.env` file in the `backend/` folder (refer to `backend/.env.example`):

```env
LIVEKIT_URL=wss://your-livekit-project.livekit.cloud
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
DEEPGRAM_API_KEY=your_deepgram_api_key
BACKEND_URL=http://localhost:8000/api/phone
```

---

## 🛠️ Setup & Running Locally

### 1. Backend REST Server
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python server.py
```
*Backend API server runs at `http://localhost:8000`.*

### 2. LiveKit Voice Agent Worker
In a new terminal:
```bash
cd backend
venv\Scripts\activate
python agent.py dev
```
*The agent worker connects to your LiveKit Cloud room session.*

### 3. Frontend Dashboard
In a new terminal:
```bash
cd frontend
npm install
npm run dev
```
*Dashboard opens at `http://localhost:5173`.*

### 4. Run Pytest Unit Test Suite
```bash
cd backend
python -m pytest test_parser.py
```

---

## 🔊 Technical Write-Up: Pre-STT Noise Suppression & VAD

Audio captured from telephony or web client microphones often contains noise (traffic, room echo, background chatter). The voice agent employs a multi-tiered noise reduction pipeline:

1. **WebRTC APM (Audio Processing Module)**:
   - **Acoustic Echo Cancellation (AEC)**: Prevents agent speaker output from looping into STT.
   - **Noise Suppression (NS)** & **Automatic Gain Control (AGC)**: Normalizes gain and filters out stationary background noise.
2. **Silero VAD (Voice Activity Detection)**:
   - Analyzes PCM audio frames to isolate human speech boundaries.
   - Blocks non-speech silence and ambient noise frames from being processed.
3. **Deepgram STT (Streaming Nova-2)**:
   - Configured with `smart_format=True` and `numerals=True` for fast, accurate streaming transcription across English and Hindi.
