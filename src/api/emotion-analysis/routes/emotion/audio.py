from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from core.whisper import analyze_and_aggregate_emotions
import tempfile, os
import librosa

router = APIRouter()


def load_audio(file: UploadFile) -> tuple:
    """Save uploaded file to temp and load as audio array."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        content = file.file.read()
        temp_file.write(content)
        temp_file.flush()
        audio_array, sampling_rate = librosa.load(temp_file.name, sr=16000)
    os.unlink(temp_file.name)
    return audio_array, sampling_rate


def analyze_emotions(audio_array, sampling_rate):
    """Placeholder for emotion analysis logic."""
    print(sampling_rate)

    emotions = analyze_and_aggregate_emotions(audio_array)
    return emotions


@router.post("/emotion/audio")
async def analyze_audio_emotion(file: UploadFile = File(...)):
    """Analyze audio file for emotions."""
    try:
        audio_array, sampling_rate = load_audio(file)
        emotions = analyze_emotions(audio_array, sampling_rate)
        return JSONResponse(content={"emotions": emotions})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
