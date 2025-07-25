from fastapi import FastAPI
import logging

from routes.audio import audio_router
from routes.text import text_router

import os

os.environ["HF_HOME"] = ".cache"

app = FastAPI()
app.include_router(audio_router, prefix="/api/audio")
app.include_router(text_router, prefix="/api/text")

logging.basicConfig(level=logging.INFO)
