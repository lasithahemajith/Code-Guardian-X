from __future__ import annotations

import secrets
from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import Response
from sqlalchemy.orm import Session

from auth import authenticate_user, create_access_token, get_current_user, require_admin
from database import create_tables, get_db
from models import PullRequest, Repository, ReviewResult
from schemas import (
    AlertResponse,
    PRReviewResponse,
    RepositoryConnect,
    RepositoryResponse,
    Token,
    UserCreate,
)

# ---------- Metrics ----------
REQUEST_COUNT = Counter("api_gateway_requests_total", "Total HTTP requests", ["method", "endpoint"])
REQUEST_LATENCY = Histogram("api_gateway_request_latency_seconds", "HTTP request latency")

# ---------- Rate limiter ----------
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(
    title="CodeGuardian API Gateway",
    description="AI-powered code review platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Auth ----------
@app.post("/auth/login", response_model=Token, tags=["auth"])
@limiter.limit("10/minute")
async def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm)):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return Token(access_token=token)


@app.post("/auth/register", tags=["auth"])
async def register(user: UserCreate, _: dict = Depends(require_admin)):
    return {"message": f"User '{user.username}' registered with role '{user.role}'"}


# ---------- Repositories ----------
@app.post("/repositories/connect", response_model=RepositoryResponse, tags=["repositories"])
async def connect_repository(
    data: RepositoryConnect,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    secret = data.webhook_secret or secrets.token_hex(32)
    existing = db.query(Repository).filter(Repository.name == data.name).first()
    if existing:
        raise HTTPException(status_code=409, detail="Repository already connected")
    repo = Repository(name=data.name, provider=data.provider, webhook_secret=secret)
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return repo


@app.get("/repositories", response_model=List[RepositoryResponse], tags=["repositories"])
async def list_repositories(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return db.query(Repository).all()


# ---------- Reviews ----------
@app.get("/reviews/{pr_id}", response_model=PRReviewResponse, tags=["reviews"])
async def get_review(pr_id: int, db: Session = Depends(get_db)):
    pr = db.query(PullRequest).filter(PullRequest.id == pr_id).first()
    if not pr:
        raise HTTPException(status_code=404, detail="PR not found")
    results = db.query(ReviewResult).filter(ReviewResult.pr_id == pr_id).all()
    summary: dict = {}
    for r in results:
        summary[r.severity] = summary.get(r.severity, 0) + 1
    issues = [
        {"severity": r.severity, "type": r.issue_type, "file": r.file,
         "line": r.line, "message": r.description}
        for r in results
    ]
    return PRReviewResponse(pr_id=pr_id, status=pr.status, summary=summary, issues=issues)


# ---------- Alerts ----------
@app.get("/alerts", response_model=List[AlertResponse], tags=["alerts"])
async def get_alerts(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return db.query(ReviewResult).order_by(ReviewResult.created_at.desc()).limit(100).all()


# ---------- Health & Metrics ----------
@app.get("/health", tags=["ops"])
async def health():
    return {"status": "ok", "service": "api-gateway"}


@app.get("/metrics", tags=["ops"])
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
