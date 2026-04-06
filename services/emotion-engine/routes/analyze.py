import warnings
import time
import librosa

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from core.speech_to_text.whisper import transcribe_audio
from core.text_emotion_recognition.transformer import get_emotions_from_text
from core.speech_emotion_recognition.whisper import (
    analyze_and_aggregate_emotions as whisper_analyze_and_aggregate_emotions,
)
from core.speech_emotion_recognition.speechbrain import (
    analyze_and_aggregate_emotions as speechbrain_analyze_and_aggregate_emotions,
)

# Suppress noisy librosa and future warnings
warnings.filterwarnings("ignore", category=UserWarning, module="librosa")
warnings.filterwarnings("ignore", category=FutureWarning, module="librosa")
warnings.filterwarnings("ignore", category=UserWarning, module="torch")

analyze_router = APIRouter()


def load_audio(file: UploadFile):
    """Save uploaded file to temp and load as audio array (16kHz mono)."""
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
        content = file.file.read()
        temp_file.write(content)
        temp_file.flush()
        audio_array, sampling_rate = librosa.load(temp_file.name, sr=16000)
    os.unlink(temp_file.name)
    return audio_array, sampling_rate


@analyze_router.post("")
async def analyze_full(file: UploadFile = File(...)):
    """
    Full audio analysis: transcription + audio emotions + text emotions.

    Runs the complete pipeline:
    1. Transcribe audio to text (Whisper)
    2. Extract emotions from audio signal (Whisper SER + SpeechBrain)
    3. Extract emotions from transcribed text (xlm-emo-t)
    """
    try:
        # 1. Load audio
        audio_array, sampling_rate = load_audio(file)
        duration = round(len(audio_array) / sampling_rate, 2)

        # 2. Transcribe audio (Whisper)
        start_transcribe = time.time()
        whisper_result = transcribe_audio(audio_array, sample_rate=sampling_rate)
        transcription_time = round(time.time() - start_transcribe, 2)

        transcription_text = whisper_result.get("transcription", "")

        # 3. Audio-based emotions (Whisper + SpeechBrain)
        start_audio_emotion = time.time()
        whisper_emotions = whisper_analyze_and_aggregate_emotions(
            audio_array, sample_rate=sampling_rate
        )
        speechbrain_emotions = speechbrain_analyze_and_aggregate_emotions(
            audio_array, sample_rate=sampling_rate
        )
        audio_emotion_time = round(time.time() - start_audio_emotion, 2)

        # Combine audio emotions from both models
        combined_audio_emotions = {}
        combined_audio_emotions.update(whisper_emotions.get("aggregated", {}))
        combined_audio_emotions.update(speechbrain_emotions.get("aggregated", {}))

        # 4. Text-based emotions (only if transcription exists)
        if not transcription_text.strip():
            return JSONResponse(
                content={
                    "transcription": transcription_text,
                    "language": whisper_result.get("language", "unknown"),
                    "average_confidence": whisper_result.get("average_confidence", 0.0),
                    "duration": duration,
                    "emotions": combined_audio_emotions,
                    "audio_emotions": combined_audio_emotions,
                    "text_emotions": {},
                    "whisper_emotions": whisper_emotions,
                    "speechbrain_emotions": speechbrain_emotions,
                    "timing": {
                        "transcription": transcription_time,
                        "audio_emotion": audio_emotion_time,
                        "text_emotion": 0.0,
                        "total": round(transcription_time + audio_emotion_time, 2),
                    },
                }
            )

        start_text_emotion = time.time()
        text_emotions = get_emotions_from_text(transcription_text)
        text_emotion_time = round(time.time() - start_text_emotion, 2)

        total_time = round(
            transcription_time + audio_emotion_time + text_emotion_time, 2
        )

        # Merge all emotions into single dict for backward compatibility
        all_emotions = {**combined_audio_emotions, **text_emotions}

        return JSONResponse(
            content={
                "transcription": transcription_text,
                "language": whisper_result.get("language", "unknown"),
                "average_confidence": whisper_result.get("average_confidence", 0.0),
                "duration": duration,
                "emotions": all_emotions,
                "audio_emotions": combined_audio_emotions,
                "text_emotions": text_emotions,
                "whisper_emotions": whisper_emotions,
                "speechbrain_emotions": speechbrain_emotions,
                "timing": {
                    "transcription": transcription_time,
                    "audio_emotion": audio_emotion_time,
                    "text_emotion": text_emotion_time,
                    "total": total_time,
                },
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
