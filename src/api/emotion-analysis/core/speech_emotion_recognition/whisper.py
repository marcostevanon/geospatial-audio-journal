import numpy as np
import torch
from transformers import AutoModelForAudioClassification, AutoFeatureExtractor
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

WHISPER_MODEL_ID = "firdhokk/speech-emotion-recognition-with-openai-whisper-large-v3"
whisper_model = AutoModelForAudioClassification.from_pretrained(
    WHISPER_MODEL_ID, force_download=False, cache_dir=".cache"
)
whisper_feature_extractor = AutoFeatureExtractor.from_pretrained(WHISPER_MODEL_ID)


def get_emotions_from_audio(
    audio_array: np.ndarray,
    max_duration: float = 30.0,  # 30 seconds is typical for Whisper
):
    """
    Get emotion predictions from a Whisper-based model.
    Returns a list of dicts: [{"emotion": str, "confidence": float}, ...]
    """
    logger.info(f"Analyzing audio chunk of length {len(audio_array)} samples.")
    # Convert to mono if needed
    if len(audio_array.shape) > 1:
        audio_array = np.mean(audio_array, axis=0)
    # Pad or truncate to 30 seconds (480,000 samples at 16kHz)
    target_length = int(whisper_feature_extractor.sampling_rate * max_duration)
    if len(audio_array) == target_length:
        audio_array = audio_array
    elif len(audio_array) < target_length:
        logger.info(
            f"Padding audio from {len(audio_array)} to {target_length} samples."
        )
        audio_array = np.pad(audio_array, (0, target_length - len(audio_array)))
    else:
        logger.info(
            f"Truncating audio from {len(audio_array)} to {target_length} samples."
        )
        audio_array = audio_array[:target_length]
    # Feature extraction
    inputs = whisper_feature_extractor(
        audio_array,
        sampling_rate=whisper_feature_extractor.sampling_rate,
        return_tensors="pt",
    )
    # Model inference
    with torch.no_grad():
        outputs = whisper_model(**inputs)
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1).squeeze().tolist()
    # Top emotions
    top_k = min(5, len(probs))
    top_k_idx = torch.topk(torch.tensor(probs), top_k).indices.tolist()
    # logger.info(
    #     f"Top emotions: {[whisper_model.config.id2label[idx] for idx in top_k_idx]}"
    # )
    return [
        {
            "emotion": whisper_model.config.id2label[idx],
            "confidence": float(probs[idx]) * 100,
        }
        for idx in top_k_idx
    ]


def split_audio_into_chunks(
    audio_array: np.ndarray, chunk_duration_sec: float = 30.0, sample_rate: int = 16000
):
    """
    Split audio into non-overlapping chunks of chunk_duration_sec seconds.
    Returns a list of np.ndarray chunks.
    """
    chunk_size = int(chunk_duration_sec * sample_rate)
    chunks = [
        audio_array[i : i + chunk_size] for i in range(0, len(audio_array), chunk_size)
    ]
    logger.info(
        f"Split audio into {len(chunks)} chunk(s) of {chunk_size} samples each."
    )
    return chunks


def analyze_and_aggregate_emotions(audio_array: np.ndarray, sample_rate: int = 16000):
    """
    Split audio, analyze each chunk, and aggregate emotion confidences by averaging.
    Returns a dict: {emotion: avg_confidence}
    """
    logger.info("Starting audio analysis and aggregation (Whisper).")
    chunks = split_audio_into_chunks(audio_array, 30.0, sample_rate)
    emotion_scores = defaultdict(list)
    for i, chunk in enumerate(chunks):
        logger.info(f"Analyzing chunk {i+1}/{len(chunks)}.")
        emotions = get_emotions_from_audio(chunk)
        for e in emotions:
            emotion_scores[e["emotion"]].append(e["confidence"])
    aggregated = {
        emotion: round(float(np.mean(scores)), 2) for emotion, scores in emotion_scores.items()
    }
    logger.info(f"Aggregated emotion scores: {aggregated}")
    return aggregated
