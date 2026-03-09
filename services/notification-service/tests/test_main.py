"""Tests for notification-service."""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from notifiers import format_summary, GitHubNotifier, SlackNotifier

SAMPLE_REVIEW = {
    "pr_id": 42,
    "repo": "company/backend",
    "summary": {"critical": 1, "high": 2, "medium": 3, "low": 0, "info": 0},
    "issues": [
        {"file": "auth.py", "line": 45, "severity": "critical", "type": "security",
         "message": "SQL injection", "suggestion": "Use parameterized queries"},
        {"file": "utils.py", "line": 12, "severity": "high", "type": "performance",
         "message": "Inefficient loop", "suggestion": None},
    ],
}


def test_format_summary_contains_pr_id():
    summary = format_summary(SAMPLE_REVIEW)
    assert "42" in summary


def test_format_summary_includes_issues():
    summary = format_summary(SAMPLE_REVIEW)
    assert "SQL injection" in summary
    assert "auth.py" in summary
    assert "parameterized queries" in summary


@pytest.mark.asyncio
async def test_slack_no_webhook_returns_false(monkeypatch):
    monkeypatch.delenv("SLACK_WEBHOOK_URL", raising=False)
    import notifiers
    notifiers.SLACK_WEBHOOK_URL = ""
    slack = SlackNotifier()
    result = await slack.send_message(SAMPLE_REVIEW)
    assert result is False


@pytest.mark.asyncio
async def test_github_no_token_returns_false(monkeypatch):
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    import notifiers
    notifiers.GITHUB_TOKEN = ""
    gh = GitHubNotifier()
    result = await gh.post_pr_comment("company/repo", 1, SAMPLE_REVIEW)
    assert result is False


@pytest.mark.asyncio
async def test_slack_sends_with_webhook(monkeypatch):
    import notifiers
    notifiers.SLACK_WEBHOOK_URL = "https://hooks.slack.com/services/test"

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    mock_post = AsyncMock()
    mock_post.__aenter__ = AsyncMock(return_value=mock_response)
    mock_post.__aexit__ = AsyncMock(return_value=False)
    mock_session.post = MagicMock(return_value=mock_post)

    with patch("notifiers.aiohttp.ClientSession", return_value=mock_session):
        slack = SlackNotifier()
        result = await slack.send_message(SAMPLE_REVIEW)
    assert result is True


def test_health_endpoint():
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
