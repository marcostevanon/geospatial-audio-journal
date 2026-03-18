from fastapi import FastAPI
import logging

from routes.audio import audio_router
from routes.text import text_router

import os

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(audio_router, prefix="/api/audio")
app.include_router(text_router, prefix="/api/text")

logging.basicConfig(level=logging.INFO)
