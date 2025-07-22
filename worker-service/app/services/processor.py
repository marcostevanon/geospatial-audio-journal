import httpx
from typing import Dict, Any, Optional
from ..core.config import settings

async def process_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Process the received data"""
    # Add your processing logic here
    return {
        "original_data": data,
        "processed_result": "Sample processed result",
        "status": "completed"
    }

async def notify_backend(processed_data: Dict[str, Any], callback_url: Optional[str] = None):
    """Notify the Node.js backend about the completed processing"""
    target_url = callback_url or f"{settings.NODE_BACKEND_URL}/api/worker/callback"
    
    async with httpx.AsyncClient() as client:
        await client.post(target_url, json=processed_data, timeout=10.0) 