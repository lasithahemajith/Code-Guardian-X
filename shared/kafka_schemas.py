"""Pydantic schemas for Kafka event messages shared across services."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class FileContent(BaseModel):
    file: str
    code: str


class PREvent(BaseModel):
    repo: str
    pr_id: int
    author: str
    files: List[str] = Field(default_factory=list)
    diff_url: str = ""
    provider: str = "github"  # github | gitlab | bitbucket
    timestamp: datetime = Field(default_factory=_now)


class CodeAnalysisReady(BaseModel):
    pr_id: int
    files: List[FileContent] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=_now)


class ReviewIssue(BaseModel):
    file: str
    line: Optional[int] = None
    type: str  # security | performance | bug | maintainability
    severity: str  # critical | high | medium | low | info
    message: str
    suggestion: Optional[str] = None


class StaticIssue(BaseModel):
    tool: str
    severity: str
    message: str
    file: Optional[str] = None
    line: Optional[int] = None


class AIReviewCompleted(BaseModel):
    pr_id: int
    issues: List[ReviewIssue] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=_now)


class StaticAnalysisCompleted(BaseModel):
    pr_id: int
    issues: List[StaticIssue] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=_now)


class ReviewSummary(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0


class ReviewFinalized(BaseModel):
    pr_id: int
    summary: ReviewSummary = Field(default_factory=ReviewSummary)
    issues: List[dict] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=_now)
