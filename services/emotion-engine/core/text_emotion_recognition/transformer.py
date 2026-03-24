import logging
import time

logger = logging.getLogger(__name__)

TEXT_EMOTION_MODEL_ID = "MilaNLProc/feel-it-italian-emotion" # 4 emotions
# TEXT_EMOTION_MODEL_ID = "SamLowe/roberta-base-go_emotions"

_text_emotion_model = None
_text_emotion_tokenizer = None


def get_text_emotion_model():
    """Lazy load the text emotion model."""
    global _text_emotion_model
    if _text_emotion_model is None:
        import torch
        from transformers import AutoModelForSequenceClassification
        
        # Force CPU for stability during demo
        device = "cpu"
        # if torch.backends.mps.is_available():
        #     device = "mps"
        # elif torch.cuda.is_available():
        #     device = "cuda"

        logger.info(
            f"Loading text emotion model '{TEXT_EMOTION_MODEL_ID}' on {device}..."
        )
        _text_emotion_model = AutoModelForSequenceClassification.from_pretrained(
            TEXT_EMOTION_MODEL_ID,
            force_download=False,
            local_files_only=False,
            cache_dir=".cache",
        ).to(device)
        logger.info("Text emotion model loaded successfully.")
    return _text_emotion_model


def get_text_emotion_tokenizer():
    """Lazy load the text emotion tokenizer."""
    global _text_emotion_tokenizer
    if _text_emotion_tokenizer is None:
        logger.info(f"Loading tokenizer for '{TEXT_EMOTION_MODEL_ID}'...")
        from transformers import AutoTokenizer
        _text_emotion_tokenizer = AutoTokenizer.from_pretrained(
            TEXT_EMOTION_MODEL_ID,
            force_download=False,
            local_files_only=False,
            cache_dir=".cache",
        )
    return _text_emotion_tokenizer

def get_emotions_from_text(text: str, max_length: int = 512):
    """
    Get emotion predictions from text using a transformer model.
    Returns a dict: {<emotion>: float, ...} with values rounded to 2 decimals,
    ordered by percentage descending.
    """
    logger.info(f"Analyzing text for emotions: {text[:50]}...")
    tokenizer = get_text_emotion_tokenizer()
    model = get_text_emotion_model()
    
    inputs = tokenizer(
        text, return_tensors="pt", truncation=True, max_length=max_length, padding=True
    )
    # Move inputs to same device as model
    inputs = {k: v.to(model.device) for k, v in inputs.items()}
    
    import torch
    with torch.no_grad():
        outputs = model(**inputs)
    probs = torch.nn.functional.softmax(outputs.logits, dim=-1).squeeze().tolist()
    # Collect and sort by probability descending
    emotions = [
        (label, round(float(probs[idx]) * 100, 2))
        for idx, label in model.config.id2label.items()
    ]
    emotions.sort(key=lambda x: x[1], reverse=True)
    result = {label: score for label, score in emotions}
    return result
