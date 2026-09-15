"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.materials import router as materials_router
from app.core.config import get_settings
from app.core.logging import configure_logging

logger = logging.getLogger(__name__)

settings = get_settings()
configure_logging(settings.logging_level)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Load the demo dataset so the dashboard is populated on first visit."""
    from app.api.routes.materials import load_demo_data
    load_demo_data()
    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://172.16.147.64:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health_router)
app.include_router(materials_router)
