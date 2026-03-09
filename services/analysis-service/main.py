"""Analysis service FastAPI application."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from kafka_consumer import start_consumer_thread, stop_consumer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_consumer_thread()
    yield
    stop_consumer()


app = FastAPI(title="CodeGuardian Analysis Service", version="1.0.0", lifespan=lifespan)


@app.get("/health", tags=["ops"])
async def health():
    return {"status": "ok", "service": "analysis-service"}
