# AI-Powered Geospatial Audio Journal

Analyze emotions in Telegram voice messages, extract mental state metrics, and map them to historical geospatial data. This project uses advanced AI models (Whisper V3, SpeechBrain, GPT-4) to process raw audio and semantics.

## Architecture & Structure

The repository has been restructured into discrete services for better AI-assisted development and isolation of concerns:

- `services/telegram/`: Node.js MTProto client that downloads messages.
- `services/emotion-engine/`: Python FastAPI service running local ML models.
- `services/core-api/`: Orchestration and data integration logic (Notion sync, state of mind evaluation).
- `data-scripts/`: Utilities for batch ingestion (e.g., Polarsteps location parsing, historical audio imports).
- `secrets/`: Centralized storage for environment files and sensitive keys (ignored by git).
- `docs/decisions/`: Architecture Decision Records (ADRs) logging key technical choices.

## Setup & Secrets

This project uses a centralized `secrets/` folder at the root level to manage sensitive configurations. **This folder is ignored by Git.**

### 1. Initialize Secrets
Copy the example files and fill in your actual credentials:
```bash
cp secrets/web.env.example secrets/web.env
cp secrets/worker.env.example secrets/worker.env
cp secrets/root.env.example secrets/root.env
```

### 2. Firebase Configuration
- **Web UI & Worker**: Create a Firebase project, enable **Storage**, and create a bucket.
- **Worker Authentication**: Generate a **Service Account JSON** from Firebase Project Settings > Service Accounts and save it as `secrets/service-account.json`.

### 3. Firebase CORS & Rules
To enable audio uploads from `localhost:3000`:
- **Rules**: In Firebase Console > Storage > Rules, allow writes to the `audio_uploads/` path. (development only)

## Quick Start (Development)

### Prerequisites
- [Docker](https://www.docker.com/) installed and running.
- Firebase project configured:
  - `secrets/web.env` — Firebase public config (`NEXT_PUBLIC_FIREBASE_*` keys).
  - `secrets/worker.env` — Firebase service account path (`FIREBASE_SERVICE_ACCOUNT_PATH`) and storage bucket (`FIREBASE_STORAGE_BUCKET`).

### One Command Start
The entire stack (Redis, Emotion Engine, Worker, Web UI) is orchestrated with Docker Compose:

```bash
docker compose up --build
```

This will start:
| Service | Port | Description |
|---|---|---|
| **Web UI** | `localhost:3000` | Next.js audio recording interface |
| **Emotion Engine** | `localhost:8000` | Python FastAPI ML backend |
| **Worker** | — | BullMQ job consumer (no exposed port) |
| **Redis** | `localhost:6379` | Message queue |

All services support **hot reloading** — code changes are reflected immediately without restarting containers.

To stop:
```bash
docker compose down
```

<details>
<summary><strong>Manual Start (without Docker)</strong></summary>

If you prefer running services natively, start each in a separate terminal:

**1. Redis**
```bash
docker compose up redis -d
```

**2. Emotion Engine**
```bash
cd services/emotion-engine
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**3. Worker**
```bash
cd services/worker
npm install && npm run dev
```

**4. Web UI**
```bash
cd services/web
npm install && npm run dev
```

</details>

*(Optional)* **Telegram Bot**: See `services/telegram/` for setup instructions.

For AI development guidelines, refer to `.cursorrules` at the project root.