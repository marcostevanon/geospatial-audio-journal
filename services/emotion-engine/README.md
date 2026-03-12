# Emotion Analysis API

## Run locally
cd services/emotion-engine
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
deactivate
