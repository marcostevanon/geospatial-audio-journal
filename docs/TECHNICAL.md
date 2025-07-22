# Technical Documentation

## Architecture

The application consists of two main components:
1. Node.js application (Telegram client and orchestrator)
2. Python FastAPI service (Emotion analysis)

## Environment Variables

Required environment variables in `.env`:
```env
API_ID=your_api_id
API_HASH=your_api_hash
PHONE_NUMBER=your_phone_number
PASSWORD=your_2fa_password  # Optional
SESSION_STRING=your_session_string  # Optional
TARGET_CHAT_ID=target_chat_id
```
