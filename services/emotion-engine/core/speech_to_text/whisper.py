import whisper
import numpy as np
import tempfile
import soundfile as sf
import logging

logger = logging.getLogger(__name__)

# Transcription model - use large-v3 for better accuracy
# "tiny" - 39M parameters (fastest, least accurate)
# "base" - 74M parameters
# "small" - 244M parameters
# "medium" - 769M parameters
# "large" - 1.5B parameters
# "large-v2" - 1.5B parameters (improved version)
# "large-v3" - 1.5B parameters (latest version)

WHISPER_MODEL_SIZE = "large-v3"
whisper_model = whisper.load_model(WHISPER_MODEL_SIZE)


def transcribe_audio(audio_array: np.ndarray, sample_rate: int = 16000) -> dict:
    """
    Transcribe a full audio numpy array using Whisper.
    Returns a dict with transcription, language, and segments.
    """
    # Save numpy array to a temporary WAV file for Whisper
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_wav:
        sf.write(temp_wav.name, audio_array, sample_rate)
        temp_wav.flush()
        temp_path = temp_wav.name
    try:
        result = whisper_model.transcribe(
            temp_path,
            language=None,  # Auto-detect language
            task="transcribe",
            fp16=False,
            temperature=0.0,
            best_of=5,
            beam_size=5,
            condition_on_previous_text=True,
            no_speech_threshold=0.6,
            compression_ratio_threshold=2.4,
            logprob_threshold=-1.0,
        )
        return {
            "transcription": result["text"],
            "language": result["language"],
            "average_confidence": round(
                float(
                    np.mean(
                        [
                            segment.get("avg_logprob", 0)
                            for segment in result["segments"]
                        ]
                    )
                ),
                3,
            ),
        }
    finally:
        import os

        os.unlink(temp_path)
