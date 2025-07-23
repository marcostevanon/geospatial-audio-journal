from fastapi import FastAPI
from routes.emotion.audio import router
from routes.transcribe import router as transcribe_router
import logging

app = FastAPI()
app.include_router(router)
app.include_router(transcribe_router)

logging.basicConfig(level=logging.INFO)
