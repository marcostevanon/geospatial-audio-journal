from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import warnings
import tempfile
import os
import librosa
import time

from core.speech_to_text.whisper import transcribe_audio
from core.speech_emotion_recognition.whisper import (
    analyze_and_aggregate_emotions as whisper_analyze_and_aggregate_emotions,
)
from core.speech_emotion_recognition.speechbrain import (
    analyze_and_aggregate_emotions as speechbrain_analyze_and_aggregate_emotions,
)

# Suppress noisy librosa and future warnings for the demo
warnings.filterwarnings("ignore", category=UserWarning, module="librosa")
warnings.filterwarnings("ignore", category=FutureWarning, module="librosa")
warnings.filterwarnings("ignore", category=UserWarning, module="torch")

audio_router = APIRouter()


def load_audio(file: UploadFile) -> tuple:
    """Save uploaded file to temp and load as audio array."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        content = file.file.read()
        temp_file.write(content)
        temp_file.flush()
        audio_array, sampling_rate = librosa.load(temp_file.name, sr=16000)
    os.unlink(temp_file.name)
    return audio_array, sampling_rate


@audio_router.post("/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...)):
    """Transcribe an audio file using Whisper."""
    try:
        audio_array, sampling_rate = load_audio(file)
        start_time = time.time()
        whisper_result = transcribe_audio(audio_array, sample_rate=sampling_rate)
        execution_time = round(time.time() - start_time, 2)
        return JSONResponse(
            content={"result": whisper_result, "execution_time": execution_time}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@audio_router.post("/emotion")
async def analyze_audio_emotion(file: UploadFile = File(...)):
    """Analyze audio file for emotions using both Whisper and SpeechBrain."""
    try:
        audio_array, sampling_rate = load_audio(file)
        start_whisper = time.time()
        whisper_emotions = whisper_analyze_and_aggregate_emotions(
            audio_array, sample_rate=sampling_rate
        )
        whisper_time = time.time() - start_whisper
        start_speechbrain = time.time()
        speechbrain_emotions = speechbrain_analyze_and_aggregate_emotions(
            audio_array, sample_rate=sampling_rate
        )
        speechbrain_time = time.time() - start_speechbrain

        combined_emotions = {}
        combined_emotions.update(whisper_emotions.get("aggregated", {}))
        combined_emotions.update(speechbrain_emotions.get("aggregated", {}))

        return JSONResponse(
            content={
                "emotions": combined_emotions,
                "whisper": whisper_emotions,
                "whisper_execution_time": round(whisper_time, 2),
                "speechbrain": speechbrain_emotions,
                "speechbrain_execution_time": round(speechbrain_time, 2),
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
