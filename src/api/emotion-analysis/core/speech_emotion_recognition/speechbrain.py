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
from speechbrain.inference.classifiers import EncoderClassifier
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

SPEECHBRAIN_MODEL_ID = "speechbrain/emotion-recognition-wav2vec2-IEMOCAP"  # should be HuggingFace model name, not a local path
SPEECHBRAIN_MODEL_DIR = ".cache/emotion-recognition-wav2vec2-IEMOCAP"

speechbrain_model = EncoderClassifier.from_hparams(
    source=SPEECHBRAIN_MODEL_ID,
    savedir=SPEECHBRAIN_MODEL_DIR,
    run_opts={"device": "cpu"},
)


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
    wav_lens = torch.tensor([1.0])
    feats = speechbrain_model.mods.wav2vec2(waveform, wav_lens)
    outputs = speechbrain_model.mods.output_mlp(feats)
    probs = torch.nn.functional.softmax(outputs, dim=-1)
    probs = probs.mean(dim=1).squeeze().tolist()
    # Top emotions
    top_k = min(5, len(probs))
    top_k_idx = torch.topk(torch.tensor(probs), top_k).indices.tolist()
    valid_indices = [
        idx
        for idx in top_k_idx
        if idx in speechbrain_model.hparams.label_encoder.ind2lab
    ]
    return [
        {
            "emotion": speechbrain_model.hparams.label_encoder.ind2lab[idx],
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
    Split audio, analyze each chunk, and aggregate emotion confidences by averaging.
    Returns a dict: {emotion: avg_confidence}
    """
    logger.info("Starting audio analysis and aggregation (SpeechBrain).")
    chunks = split_audio_into_chunks(audio_array, 30.0, sample_rate)
    emotion_scores = defaultdict(list)
    for i, chunk in enumerate(chunks):
        logger.info(f"Analyzing chunk {i+1}/{len(chunks)}.")
        emotions = get_emotions_from_audio(chunk, sample_rate=sample_rate)
        for e in emotions:
            emotion_scores[e["emotion"]].append(e["confidence"])
    aggregated = {
        emotion: round(float(np.mean(scores)), 2)
        for emotion, scores in emotion_scores.items()
    }
    logger.info(f"Aggregated emotion scores: {aggregated}")
    return aggregated
