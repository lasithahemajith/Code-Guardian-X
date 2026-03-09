from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class RepositoryConnect(BaseModel):
    name: str
    provider: str = "github"
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None


class RepositoryResponse(BaseModel):
    id: int
    name: str
    provider: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewIssue(BaseModel):
    file: Optional[str] = None
    line: Optional[int] = None
    type: Optional[str] = None
    severity: str
    message: str
    suggestion: Optional[str] = None


class PRReviewResponse(BaseModel):
    pr_id: int
    status: str
    summary: dict
    issues: List[ReviewIssue] = []


class AlertResponse(BaseModel):
    id: int
    severity: str
    issue_type: str
    file: Optional[str] = None
    line: Optional[int] = None
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "developer"  # admin | developer | viewer
