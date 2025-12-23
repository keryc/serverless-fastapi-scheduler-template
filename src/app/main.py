import os

from fastapi import FastAPI

from .api.v1.health import router as health_router
from .core.config import settings
from .core.logging import configure_logging

configure_logging()

root_path = settings.ROOT_PATH or os.getenv("ROOT_PATH") or ""
app = FastAPI(title="Serverless FastAPI Scheduler Template", version="1.0.0", root_path=root_path)
app.include_router(health_router, prefix="/api/v1")
