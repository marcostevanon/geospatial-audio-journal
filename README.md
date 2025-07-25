# Telegram Voice Message Emotion Analyzer

Analyze emotions in Telegram voice messages using advanced AI models. This application downloads voice messages from Telegram and provides detailed emotion analysis using two different AI models.

## Quick Start

1. Clone and install dependencies:
```bash
git clone <repository-url>
cd telegram-emotion-app
npm install
```

2. Set up Python environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
cd emotion-analysis-service
pip install -r requirements.txt
```

3. Create `.env` file with your Telegram credentials:
```env
API_ID=your_api_id
API_HASH=your_api_hash
PHONE_NUMBER=your_phone_number
TARGET_CHAT_ID=target_chat_id
```

4. Start the services:
```bash
# Terminal 1 - Start Python service
cd emotion-analysis-service
uvicorn main:app --reload

# Terminal 2 - Start Node.js app
npm run dev
```

## Features

- 🎙️ Voice message analysis from Telegram
- 🤖 Dual AI model analysis (Whisper V3 & SpeechBrain)
- 📊 Detailed audio analysis and visualization
- 🔄 Real-time processing
- 📱 Easy-to-use interface

## Requirements

- Node.js 16+
- Python 3.9+
- FFmpeg
- Telegram API credentials

## Documentation

For detailed technical documentation, see the [docs](./docs) folder.

## License

[Add your license here]



### Workflow

- Audio Emotion Analysis
- Speech to Text Transcription
- Text Correction
- Text Emotion Analysis