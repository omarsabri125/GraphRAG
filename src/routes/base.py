from fastapi import APIRouter, Depends
from typing import Union
from schemes.HealthCheckResponse import HealthCheckSuccess, HealthCheckError
from helpers.config import get_settings, Settings
import logging

base_router = APIRouter(
    prefix="/api/v1",
    tags=["graph-rag"],
)
logger = logging.getLogger("uvicorn.error")

@base_router.get("/health", response_model=Union[HealthCheckSuccess, HealthCheckError])
async def health_check(app_config: Settings = Depends(get_settings)):
    try:
        logger.info("Health check endpoint called.")
        return HealthCheckSuccess(status="ok", app_name=app_config.APP_NAME)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckError(status="error", message=str(e))
