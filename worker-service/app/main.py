from fastapi import FastAPI
from .api.routes import router

app = FastAPI(title="Worker Service")
app.include_router(router)