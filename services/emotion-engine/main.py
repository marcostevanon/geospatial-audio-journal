from fastapi import FastAPI
import logging

from routes.audio import audio_router
from routes.text import text_router
from routes.analyze import analyze_router

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(audio_router, prefix="/api/audio")
app.include_router(text_router, prefix="/api/text")
app.include_router(analyze_router, prefix="/api/analyze")

logging.basicConfig(level=logging.INFO)
