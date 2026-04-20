from fastapi import Request
from fastapi.exceptions import HTTPException

from app.core.config import app_config

async def validate_api_key(request: Request, call_next):
    api_key = request.headers.get("X-API-Key")
    if api_key != app_config.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return await call_next(request)