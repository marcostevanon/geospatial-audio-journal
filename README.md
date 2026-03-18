# AI-Powered Geospatial Audio Journal

Analyze emotions in Telegram voice messages, extract mental state metrics, and map them to historical geospatial data. This project uses advanced AI models (Whisper V3, SpeechBrain, GPT-4) to process raw audio and semantics.

## Architecture & Structure

The repository has been restructured into discrete services for better AI-assisted development and isolation of concerns:

- `services/telegram-bot/`: Node.js MTProto client that downloads messages.
- `services/emotion-engine/`: Python FastAPI service running local ML models.
- `services/core-api/`: Orchestration and data integration logic (Notion sync, state of mind evaluation).
- `data-scripts/`: Utilities for batch ingestion (e.g., Polarsteps location parsing, historical audio imports).
- `docs/decisions/`: Architecture Decision Records (ADRs) logging key technical choices.

## Quick Start (Development)

The project consists of multiple independent services. To run the full audio recording and analysis pipeline, follow these steps in separate terminal windows:

### 1. Start Redis (Message Queue)
We use Redis and BullMQ to handle background audio processing. Ensure Docker is running.
```bash
docker compose up -d
```

### 2. Python Emotion Engine (AI Backend)
This FastAPI service runs the ML models (Whisper/SpeechBrain) for emotion analysis.
```bash
cd services/emotion-engine
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 3. Node.js Worker (Job Consumer)
This worker listens to Redis, downloads the audio from Firebase, and sends it to the Emotion Engine. 
*(Requires Firebase credentials in `services/worker/.env` or `.env.local`)*
```bash
cd services/worker
npm install
npm run dev
```

### 4. Next.js Web UI (Frontend)
The web interface for recording and uploading audio.
*(Requires Firebase public config in `services/web/.env.local`)*
```bash
cd services/web
npm install
npm run dev
```

*(Optional)* **Node.js Telegram Bot**:
If you also want to ingest Telegram audio messages:
```bash
cd services/telegram-bot
npm install
npm run dev
```

For AI development guidelines, please refer to the `.cursorrules` file at the root of the repository.