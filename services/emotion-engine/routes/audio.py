from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import warnings

# Suppress noisy librosa and future warnings for the demo
warnings.filterwarnings("ignore", category=UserWarning, module="librosa")
warnings.filterwarnings("ignore", category=FutureWarning, module="librosa")
warnings.filterwarnings("ignore", category=UserWarning, module="torch")
from core.speech_to_text.whisper import transcribe_audio
from core.text_emotion_recognition.transformer import get_emotions_from_text
from core.speech_emotion_recognition.whisper import (
    analyze_and_aggregate_emotions as whisper_analyze_and_aggregate_emotions,
)
from core.speech_emotion_recognition.speechbrain import (
    analyze_and_aggregate_emotions as speechbrain_analyze_and_aggregate_emotions,
)
import tempfile, os
import librosa
import numpy as np
import time
import traceback

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
        result = transcribe_audio(audio_array, sample_rate=sampling_rate)
        execution_time = round(time.time() - start_time, 2)
        if isinstance(result, dict):
            result["execution_time"] = execution_time
            return JSONResponse(content=result)
        return JSONResponse(
            content={"result": result, "execution_time": execution_time}
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
        return JSONResponse(
            content={
                "whisper": whisper_emotions,
                "whisper_execution_time": round(whisper_time, 2),
                "speechbrain": speechbrain_emotions,
                "speechbrain_execution_time": round(speechbrain_time, 2),
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@audio_router.post("/analyze")
async def analyze_pipeline(file: UploadFile = File(...)):
    """Transcribe audio and analyze emotions on the resulting text."""
    try:
        # 1. Load Audio
        audio_array, sampling_rate = load_audio(file)
        
        # 2. Transcribe Audio (Whisper)
        start_time = time.time()
        whisper_result = transcribe_audio(audio_array, sample_rate=sampling_rate)
        transcription_time = round(time.time() - start_time, 2)
        
        transcription_text = whisper_result.get("transcription", "")
        
        if not transcription_text.strip():
            # If no transcription was found, return empty emotions
            return JSONResponse({
                "transcription": "",
                "language": whisper_result.get("language", "unknown"),
                "average_confidence": whisper_result.get("average_confidence", 0.0),
                "emotions": {},
                "transcription_time": transcription_time,
                "emotion_time": 0.0,
                "total_time": transcription_time
            })
            
        # 3. Emotion Recognition from Text (Transformer)
        start_emotion = time.time()
        emotions = get_emotions_from_text(transcription_text)
        emotion_time = round(time.time() - start_emotion, 2)
        
        return JSONResponse({
            "transcription": transcription_text,
            "language": whisper_result.get("language", "unknown"),
            "average_confidence": whisper_result.get("average_confidence", 0.0),
            "emotions": emotions,
            "transcription_time": transcription_time,
            "emotion_time": emotion_time,
            "total_time": round(transcription_time + emotion_time, 2)
        })
        
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
