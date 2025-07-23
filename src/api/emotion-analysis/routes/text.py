from fastapi import APIRouter, HTTPException

text_router = APIRouter()

@text_router.post("/emotion")
async def text_emotion_stub():
    """Stub for text-based emotion recognition."""
    raise HTTPException(status_code=501, detail="Text emotion recognition not implemented yet.")

@text_router.post("/generate")
async def text_generate_stub():
    """Stub for LLM text generation."""
    raise HTTPException(status_code=501, detail="Text generation not implemented yet.") 