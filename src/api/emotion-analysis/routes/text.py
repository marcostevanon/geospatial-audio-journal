from fastapi import APIRouter, HTTPException, Body, Query
from pydantic import BaseModel
from core.text_emotion_recognition.transformer import get_emotions_from_text
from core.ollama.correct import correct_text_with_ollama
import time
import difflib

text_router = APIRouter()


class TextEmotionRequest(BaseModel):
    text: str


@text_router.post("/emotion")
async def text_emotion(request: TextEmotionRequest):
    """Analyze text for emotions using a transformer model."""
    try:
        start = time.time()
        emotions = get_emotions_from_text(request.text)
        execution_time = round(time.time() - start, 2)
        return {"emotions": emotions, "execution_time": execution_time}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@text_router.post("/ollama")
async def ollama(
    request: TextEmotionRequest,
    model: str = Query("llama3.2", description="Ollama model to use for correction"),
):
    """Correct text using a local Ollama model. Model can be set via query param."""
    try:
        start = time.time()
        corrected = correct_text_with_ollama(request.text, model=model)
        exec_time = round(time.time() - start, 2)
        original_words = request.text.split()
        corrected_words = corrected.split()
        diff = list(difflib.ndiff(original_words, corrected_words))
        modified = [w[2:] for w in diff if w.startswith("- ") or w.startswith("+ ")]
        return {
            "corrected": corrected,
            "model": model,
            "execution_time": exec_time,
            "modified_words": modified,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @text_router.post("/generate")
# async def text_generate_stub():
#     """Stub for LLM text generation."""
#     raise HTTPException(status_code=501, detail="Text generation not implemented yet.")
