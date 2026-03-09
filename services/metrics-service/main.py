"""Metrics service — exposes Prometheus metrics for CodeGuardian."""
from __future__ import annotations

import logging

from fastapi import FastAPI
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.responses import Response

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ---------- Prometheus metrics ----------
PR_REVIEWS_TOTAL = Counter(
    "codeguardian_pr_reviews_total",
    "Total number of PRs reviewed",
    ["provider", "status"],
)
REVIEW_LATENCY = Histogram(
    "codeguardian_review_latency_seconds",
    "End-to-end review latency in seconds",
    buckets=[1, 5, 10, 30, 60, 120, 300],
)
AI_INFERENCE_TIME = Histogram(
    "codeguardian_ai_inference_seconds",
    "AI model inference time in seconds",
    buckets=[0.1, 0.5, 1, 2, 5, 10, 30],
)
ISSUES_DETECTED = Counter(
    "codeguardian_issues_detected_total",
    "Total issues detected",
    ["issue_type", "severity", "source"],
)

app = FastAPI(title="CodeGuardian Metrics Service", version="1.0.0")


@app.get("/health", tags=["ops"])
async def health():
    return {"status": "ok", "service": "metrics-service"}


@app.get("/metrics", tags=["ops"])
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/record/review", tags=["metrics"])
async def record_review(provider: str = "github", status: str = "completed", latency: float = 0.0):
    PR_REVIEWS_TOTAL.labels(provider=provider, status=status).inc()
    if latency > 0:
        REVIEW_LATENCY.observe(latency)
    return {"recorded": True}


@app.post("/record/issue", tags=["metrics"])
async def record_issue(issue_type: str = "security", severity: str = "medium", source: str = "ai"):
    ISSUES_DETECTED.labels(issue_type=issue_type, severity=severity, source=source).inc()
    return {"recorded": True}
