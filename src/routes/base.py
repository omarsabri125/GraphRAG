from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from helpers.config import get_settings, Settings
import logging

base_router = APIRouter(
    prefix="/api/v1",
    tags=["graph-rag"],
)
logger = logging.getLogger("uvicorn.error")

@base_router.get("/health")
async def health_check(app_config: Settings = Depends(get_settings)):
    try:
        logger.info("Health check endpoint called.")
        return {"status": "ok",
                "app_name": app_config.APP_NAME}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})
