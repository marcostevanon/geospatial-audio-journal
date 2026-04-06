# AI-Powered Geospatial Audio Journal — Agent Orchestration Rules

## Project Overview
A full-stack system that ingests Telegram voice messages, runs ML pipelines
(Whisper → SpeechBrain) to extract emotion/mental state metrics,
and maps results onto historical geospatial data.

**Stack:**
- Backend: Python, FastAPI (services/emotion-engine/)
- ML: openai-whisper, transformers, librosa, SpeechBrain, Ollama
- Frontend: TypeScript, Next.js 16, Firebase, BullMQ (services/web/)
- Worker: TypeScript, BullMQ, Firebase Admin (services/worker/)
- Telegram: TypeScript, MTProto (services/telegram/)
- Infra: Docker Compose, Redis 7

---

## Agent Team (4 agents)

| Agent      | Mode      | Owns                                              |
|------------|-----------|---------------------------------------------------|
| `planner`  | primary   | Orchestration, architecture decisions              |
| `backend`  | subagent  | emotion-engine, worker, telegram                   |
| `frontend` | subagent  | web                                               |
| `review`   | subagent  | Code review — read-only, structured feedback      |

---

## Orchestration Rules

### 1. Always Start With Planner
The `planner` agent MUST be consulted before any implementation begins.
It produces a task breakdown that all other agents follow.

### 2. Execution Order Per Feature
```
planner → backend → frontend → review
```
Never start `frontend` before `backend` has defined the API contract.

### 3. Subagent Context Passing
Each subagent receives ONLY a summarized brief from the previous step.
Full file contents must NOT be passed between agents — use file paths instead.
Example: "See `services/emotion-engine/routes/audio.py` for the audio API."

### 4. Git Discipline
- `git commit` always requires user approval (ask)
- `git push` is always denied (user handles push manually)
- Conventional commits only: `feat:`, `fix:`, `chore:`, `test:`, `docs:`

### 5. File Ownership
| Path                       | Owner    |
|----------------------------|----------|
| `services/emotion-engine/` | backend  |
| `services/worker/`         | backend  |
| `services/telegram/`       | backend  |
| `services/web/`            | frontend |
| `docker-compose.yml`        | backend  |

No agent edits outside its owned paths without explicit user approval.

### 6. Backend Guardrails
- Never call emotion-engine API directly from frontend — always through BullMQ
- Ollama calls wrapped in `try/except` with graceful degradation
- Audio temp files must be deleted in `finally` block

### 7. Review Gate
Before any feature is marked complete, invoke `@review`.
Reviewer output format:
```
## Review: <feature>
### ✅ Approved
### ⚠️ Suggestions (non-blocking)
### ❌ Blockers (must fix before merge)
```

### 8. No Hardcoded Secrets
Any agent finding a hardcoded secret must STOP and report it immediately.
All secrets via environment variables in `secrets/` folder — never commit real credentials.
