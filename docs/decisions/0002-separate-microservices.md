# Architecture Decision Record: Microservice Split

## Status
Accepted

## Context
The application relies heavily on two different ecosystems: Node.js (for Telegram integration via MTProto, easy webhook support) and Python (for HuggingFace ML models and heavy compute tasks). Mixing these under a single `src/` tree causes dependency conflicts and deployment complexity.

## Decision
We will separate the project into independent services under the `services/` directory:
-   `services/telegram`: Manages the MTProto connection.
-   `services/emotion-engine`: An isolated Python API serving ML predictions.
-   `services/core-api`: The central orchestration API handling business logic (e.g. state of mind, Notion sync).

## Consequences
- Requires running multiple development servers locally.
- Clarifies dependency chains (NPM vs Pip) and simplifies Dockerization per-service.
