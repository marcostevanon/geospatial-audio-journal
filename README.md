# AI-Powered Geospatial Audio Journal (formerly emotions-map)

Analyze emotions in Telegram voice messages, extract mental state metrics, and map them to historical geospatial data. This project uses advanced AI models (Whisper V3, SpeechBrain, GPT-4) to process raw audio and semantics.

## Architecture & Structure

The repository has been restructured into discrete services for better AI-assisted development and isolation of concerns:

- `services/telegram-bot/`: Node.js MTProto client that downloads messages.
- `services/emotion-engine/`: Python FastAPI service running local ML models.
- `services/core-api/`: Orchestration and data integration logic (Notion sync, state of mind evaluation).
- `data-scripts/`: Utilities for batch ingestion (e.g., Polarsteps location parsing, historical audio imports).
- `docs/decisions/`: Architecture Decision Records (ADRs) logging key technical choices.

## Quick Start (Development)

The services run independently. See their respective directories for detailed setups.

1. **Python Emotion Engine**:
```bash
cd services/emotion-engine
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

2. **Node.js Telegram Bot**:
```bash
cd services/telegram-bot
npm install
npm run dev
```

For AI development, please refer to the `.cursorrules` file at the root of the repository.