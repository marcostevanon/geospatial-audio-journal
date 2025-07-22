from fastapi import FastAPI
from routes.emotion.audio import router
import logging

app = FastAPI()
app.include_router(router)

logging.basicConfig(level=logging.INFO)
