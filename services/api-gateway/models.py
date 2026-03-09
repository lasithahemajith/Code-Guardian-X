from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def _now():
    return datetime.now(timezone.utc)


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    provider = Column(String, nullable=False)  # github | gitlab | bitbucket
    webhook_secret = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now)


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repo_id = Column(Integer, ForeignKey("repositories.id"), nullable=False)
    pr_number = Column(Integer, nullable=False)
    author = Column(String)
    status = Column(String, default="pending")  # pending | analyzing | completed
    created_at = Column(DateTime(timezone=True), default=_now)


class ReviewResult(Base):
    __tablename__ = "review_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pr_id = Column(Integer, ForeignKey("pull_requests.id"), nullable=False)
    severity = Column(String)
    issue_type = Column(String)
    file = Column(String, nullable=True)
    line = Column(Integer, nullable=True)
    description = Column(String)
    created_at = Column(DateTime(timezone=True), default=_now)
