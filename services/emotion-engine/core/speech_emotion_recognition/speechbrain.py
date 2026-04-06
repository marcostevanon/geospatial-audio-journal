# TODO:
# High priority:
# -
#
# Low priority:
# - Add unit tests for get_emotions_from_audio
# - Handle edge cases (e.g., empty audio, wrong sample rate)
# - Support GPU inference if available
# - Add batch processing for multiple audio inputs


import numpy as np
import torch
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

SPEECHBRAIN_MODEL_ID = "speechbrain/emotion-recognition-wav2vec2-IEMOCAP"
SPEECHBRAIN_MODEL_DIR = ".cache/emotion-recognition-wav2vec2-IEMOCAP"

_speechbrain_model = None


def get_speechbrain_model():
    """Lazy load the SpeechBrain model."""
    global _speechbrain_model
    if _speechbrain_model is None:
        from speechbrain.inference.classifiers import EncoderClassifier

        device = "cpu"
        if torch.backends.mps.is_available():
            device = "mps"
        elif torch.cuda.is_available():
            device = "cuda"

        logger.info(
            f"Loading SpeechBrain model '{SPEECHBRAIN_MODEL_ID}' on {device}..."
        )
        _speechbrain_model = EncoderClassifier.from_hparams(
            source=SPEECHBRAIN_MODEL_ID,
            savedir=SPEECHBRAIN_MODEL_DIR,
            run_opts={"device": device},
        )
        logger.info("SpeechBrain model loaded successfully.")
    return _speechbrain_model


def get_emotions_from_audio(
    audio_array: np.ndarray,
    max_duration: float = 30.0,  # 30 seconds typical
    sample_rate: int = 16000,
):
    """
    Get emotion predictions from SpeechBrain model.
    Returns a list of dicts: [{"emotion": str, "confidence": float}, ...]
    """
    logger.info(f"Analyzing audio chunk of length {len(audio_array)} samples.")
    # Convert to mono if needed
    if len(audio_array.shape) > 1:
        audio_array = np.mean(audio_array, axis=0)
    # Pad or truncate to max_duration
    target_length = int(sample_rate * max_duration)
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
    # Preprocess for SpeechBrain
    waveform = torch.FloatTensor(audio_array)
    if waveform.abs().max() > 0:
        waveform = waveform / waveform.abs().max()
    if waveform.ndim > 1:
        waveform = waveform.mean(dim=1)
    waveform = waveform.unsqueeze(0)
    # Model inference
    model = get_speechbrain_model()
    waveform = waveform.to(next(model.mods.wav2vec2.parameters()).device)
    wav_lens = torch.tensor([1.0]).to(waveform.device)
    feats = model.mods.wav2vec2(waveform, wav_lens)
    outputs = model.mods.output_mlp(feats)
    probs = torch.nn.functional.softmax(outputs, dim=-1)
    probs = probs.mean(dim=1).squeeze().tolist()
    # Top emotions
    top_k = min(5, len(probs))
    top_k_idx = torch.topk(torch.tensor(probs), top_k).indices.tolist()
    valid_indices = [
        idx for idx in top_k_idx if idx in model.hparams.label_encoder.ind2lab
    ]
    return [
        {
            "emotion": model.hparams.label_encoder.ind2lab[idx],
            "confidence": float(probs[idx]) * 100,
        }
        for idx in valid_indices
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
    logger.info("Starting audio analysis and aggregation (SpeechBrain).")
    chunks = split_audio_into_chunks(audio_array, 30.0, sample_rate)
    emotion_scores = defaultdict(list)
    per_chunk = []
    model = get_speechbrain_model()
    emotion_labels = list(getattr(model.hparams.label_encoder, "ind2lab", {}).values())
    if not emotion_labels:
        emotion_labels = ["sad", "fearful", "happy", "neutral", "disgust"]
    for i, chunk in enumerate(chunks):
        logger.info(f"Analyzing chunk {i + 1}/{len(chunks)}.")
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
    aggregated = dict(
        sorted(aggregated.items(), key=lambda item: item[1], reverse=True)
    )
    logger.info(f"Aggregated emotion scores: {aggregated}")
    return {"per_chunk": per_chunk, "aggregated": aggregated}
