"""Repo-service FastAPI application."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Header
from fastapi.responses import JSONResponse

from github_handler import extract_pr_event as gh_extract, verify_signature
from gitlab_handler import (
    extract_pr_event as gl_extract,
    verify_token as gl_verify_token,
)
from kafka_producer import producer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

PR_EVENTS_TOPIC = "pr.events"


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    producer.close()


app = FastAPI(title="CodeGuardian Repo Service", version="1.0.0", lifespan=lifespan)


def _send_to_kafka(event: dict):
    key = str(event.get("pr_id", "unknown"))
    producer.produce_event(PR_EVENTS_TOPIC, key=key, value=event)


@app.post("/webhooks/github", tags=["webhooks"])
async def github_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_hub_signature_256: str = Header(default=""),
    x_github_event: str = Header(default=""),
):
    body = await request.body()
    # Signature verification (skip if no secret configured)
    secret = request.headers.get("x-webhook-secret", "default-secret")
    if not verify_signature(body, secret, x_hub_signature_256):
        if x_hub_signature_256:  # Only reject if a signature was provided
            raise HTTPException(status_code=400, detail="Invalid signature")

    if x_github_event != "pull_request":
        return JSONResponse({"message": "Event ignored"})

    import json
    payload = json.loads(body)
    event = gh_extract(payload)
    if event:
        background_tasks.add_task(_send_to_kafka, event)
        return {"message": "PR event queued", "pr_id": event["pr_id"]}
    return {"message": "Action ignored"}


@app.post("/webhooks/gitlab", tags=["webhooks"])
async def gitlab_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_gitlab_token: str = Header(default=""),
):
    secret = request.headers.get("x-webhook-secret", "default-secret")
    if x_gitlab_token and not gl_verify_token(x_gitlab_token, secret):
        raise HTTPException(status_code=400, detail="Invalid token")

    import json
    body = await request.body()
    payload = json.loads(body)
    if payload.get("object_kind") != "merge_request":
        return JSONResponse({"message": "Event ignored"})

    event = gl_extract(payload)
    if event:
        background_tasks.add_task(_send_to_kafka, event)
        return {"message": "MR event queued", "pr_id": event["pr_id"]}
    return {"message": "Action ignored"}


@app.get("/health", tags=["ops"])
async def health():
    return {"status": "ok", "service": "repo-service"}
