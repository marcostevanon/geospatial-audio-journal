from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from ..services.processor import process_data, notify_backend

router = APIRouter()

class ProcessingRequest(BaseModel):
    data: Dict[str, Any]
    callback_url: Optional[str] = None

async def process_and_notify(data: Dict[str, Any], callback_url: Optional[str] = None):
    """Process data and notify backend"""
    processed_data = await process_data(data)
    await notify_backend(processed_data, callback_url)

@router.post("/process")
async def process_request(request: ProcessingRequest, background_tasks: BackgroundTasks):
    """Endpoint to receive data for processing"""
    try:
        background_tasks.add_task(process_and_notify, request.data, request.callback_url)
        return {"status": "accepted", "message": "Processing started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"} 