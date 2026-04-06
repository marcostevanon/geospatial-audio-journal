from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from core.text_emotion_recognition.transformer import get_emotions_from_text
import time

text_router = APIRouter()


class TextEmotionRequest(BaseModel):
    text: str


@text_router.post("/emotion")
async def text_emotion(request: TextEmotionRequest):
    """Analyze text for emotions using a transformer model."""
    try:
        start = time.time()
        emotions = get_emotions_from_text(request.text)
        print(f"Emotions: {emotions}")
        execution_time = round(time.time() - start, 2)
        return {"emotions": emotions, "execution_time": execution_time}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
