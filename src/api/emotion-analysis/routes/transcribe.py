from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from core.whisper_transcribe import transcribe_audio
import tempfile, os
import librosa
import numpy as np

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

@router.post("/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...)):
    """Transcribe an audio file using Whisper."""
    try:
        audio_array, sampling_rate = load_audio(file)
        result = transcribe_audio(audio_array, sample_rate=sampling_rate)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 