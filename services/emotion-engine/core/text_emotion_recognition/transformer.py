import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import logging
import time

logger = logging.getLogger(__name__)

# TEXT_EMOTION_MODEL_ID = "MilaNLProc/feel-it-italian-emotion" # 4 emotions
TEXT_EMOTION_MODEL_ID = "SamLowe/roberta-base-go_emotions" # 28 emotions
# TEXT_EMOTION_MODEL_ID = "arpanghoshal/EmoRoBERTa" # 28 emotions
# TEXT_EMOTION_MODEL_ID = "bhadresh-savani/bert-base-uncased-emotion" # 6 emotions
text_emotion_model = AutoModelForSequenceClassification.from_pretrained(
    TEXT_EMOTION_MODEL_ID,
    force_download=False,
    local_files_only=False,
    cache_dir=".cache",
)
text_emotion_tokenizer = AutoTokenizer.from_pretrained(
    TEXT_EMOTION_MODEL_ID,
    force_download=False,
    local_files_only=False,
    cache_dir=".cache",
)

def get_emotions_from_text(text: str, max_length: int = 512):
    """
    Get emotion predictions from text using a transformer model.
    Returns a dict: {<emotion>: float, ...} with values rounded to 2 decimals,
    ordered by percentage descending.
    """
    logger.info(f"Analyzing text for emotions: {text[:50]}...")
    inputs = text_emotion_tokenizer(
        text, return_tensors="pt", truncation=True, max_length=max_length, padding=True
    )
    with torch.no_grad():
        outputs = text_emotion_model(**inputs)
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1).squeeze().tolist()
    # Collect and sort by probability descending
    emotions = [
        (label, round(float(probs[idx]) * 100, 2))
        for idx, label in text_emotion_model.config.id2label.items()
    ]
    emotions.sort(key=lambda x: x[1], reverse=True)
    result = {label: score for label, score in emotions}
    return result
