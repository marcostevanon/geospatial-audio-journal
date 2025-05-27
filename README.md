# Telegram Voice Message Emotion Analyzer

This project analyzes voice messages from Telegram using two different emotion recognition models:
1. Whisper Large V3 (8 emotions)
2. SpeechBrain IEMOCAP (4 emotions)

## Features

- Downloads and analyzes voice messages from Telegram
- Uses Python FastAPI microservice for emotion analysis
- Provides detailed audio analysis (duration, bitrate, sample rate, etc.)
- Generates waveform visualization
- Supports multiple emotion recognition models

## Prerequisites

- Node.js 16+ and npm
- Python 3.9+
- FFmpeg (for audio processing)
- Telegram API credentials

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd telegram-emotion-app
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Set up Python environment:
```bash
# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
cd emotion-analysis-service
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with your Telegram API credentials:
```env
API_ID=your_api_id
API_HASH=your_api_hash
PHONE_NUMBER=your_phone_number
PASSWORD=your_2fa_password  # Optional
SESSION_STRING=your_session_string  # Optional
TARGET_CHAT_ID=target_chat_id
```

## Usage

1. Start the Python emotion analysis service:
```bash
cd emotion-analysis-service
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uvicorn main:app --reload
```

2. In a new terminal, run the Node.js application:
```bash
npm run dev
```

3. The application will:
   - Connect to Telegram
   - Download the latest voice message from the target chat
   - Analyze the audio using both emotion recognition models
   - Display detailed analysis results

## Project Structure

```
.
├── src/                    # Node.js application
│   ├── index.ts           # Main application logic
│   ├── config.ts          # Configuration management
│   ├── seraas-client.ts   # Python service client
│   └── types.ts           # TypeScript type definitions
├── emotion-analysis-service/         # Python emotion analysis service
│   ├── main.py           # FastAPI application
│   └── requirements.txt   # Python dependencies
└── .env                   # Environment variables
```

## Dependencies

### Node.js
- telegram: Telegram client library
- axios: HTTP client
- form-data: Form data handling
- typescript: TypeScript support

### Python
- fastapi: Web framework
- uvicorn: ASGI server
- transformers: Hugging Face transformers
- speechbrain: Speech processing toolkit
- torch: PyTorch
- librosa: Audio processing
