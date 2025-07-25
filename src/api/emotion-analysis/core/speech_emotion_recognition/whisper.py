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

EMOTION_LABEL_MAP = {
    "happy": "hap",
    "neutral": "neu",
    "sad": "sad",
    "angry": "ang",
    "fearful": "fea",
    "disgust": "dis",
}


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
            "emotion": EMOTION_LABEL_MAP.get(whisper_model.config.id2label[idx], whisper_model.config.id2label[idx])[:3],
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
    Split audio, analyze each chunk, return per-chunk emotions and aggregated averages.
    Returns:
        {
            "per_chunk": [ {emotion1: conf, ...}, ... ],
            "aggregated": {emotion: avg_confidence, ... }
        }
    """
    logger.info("Starting audio analysis and aggregation (Whisper).")
    chunks = split_audio_into_chunks(audio_array, 30.0, sample_rate)
    emotion_scores = defaultdict(list)
    per_chunk = []
    # Use model's id2label for emotion keys, fallback to default
    emotion_labels = list(getattr(whisper_model.config, "id2label", {}).values())
    if not emotion_labels:
        emotion_labels = ["sad", "fearful", "happy", "neutral", "disgust"]
    # Map emotion_labels to 3-char codes
    emotion_labels = [EMOTION_LABEL_MAP.get(label, label)[:3] for label in emotion_labels]
    for i, chunk in enumerate(chunks):
        logger.info(f"Analyzing chunk {i+1}/{len(chunks)}.")
        emotions = get_emotions_from_audio(chunk)
        chunk_dict = {label: 0.0 for label in emotion_labels}
        for e in emotions:
            if e["emotion"] in chunk_dict:
                chunk_dict[e["emotion"]] = round(e["confidence"], 2)
                emotion_scores[e["emotion"]].append(e["confidence"])
        per_chunk.append(chunk_dict)
    aggregated = {
        label: (
            round(float(np.mean(emotion_scores[label])), 2)
            if emotion_scores[label]
            else 0.0
        )
        for label in emotion_labels
    }
    aggregated = dict(sorted(aggregated.items(), key=lambda item: item[1], reverse=True))
    logger.info(f"Aggregated emotion scores: {aggregated}")
    return {"per_chunk": per_chunk, "aggregated": aggregated}
