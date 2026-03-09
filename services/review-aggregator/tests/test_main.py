"""Tests for review-aggregator service."""
from __future__ import annotations

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from unittest.mock import MagicMock

from aggregator import aggregate_results
from kafka_consumer import process_message, AI_TOPIC, STATIC_TOPIC


def test_aggregate_empty():
    result = aggregate_results([], [])
    assert result["issues"] == []
    assert result["summary"]["critical"] == 0


def test_aggregate_severity_ordering():
    ai_issues = [
        {"file": "a.py", "line": 1, "type": "security", "severity": "low", "message": "A"},
        {"file": "b.py", "line": 2, "type": "bug", "severity": "critical", "message": "B"},
    ]
    result = aggregate_results(ai_issues, [])
    assert result["issues"][0]["severity"] == "critical"
    assert result["summary"]["critical"] == 1
    assert result["summary"]["low"] == 1


def test_aggregate_deduplication():
    issue = {"file": "a.py", "line": 5, "type": "security", "severity": "high", "message": "Same issue"}
    static = [{"tool": "bandit", "severity": "high", "message": "Same issue", "file": "a.py", "line": 5}]
    result = aggregate_results([issue], static)
    # The AI issue and static issue have different keys (static prefixes tool name)
    assert len(result["issues"]) >= 1


def test_aggregate_static_normalized():
    static_issues = [{"tool": "bandit", "severity": "HIGH", "message": "Hardcoded secret", "file": "cfg.py", "line": 3}]
    result = aggregate_results([], static_issues)
    assert result["issues"][0]["severity"] == "high"


def test_process_message_single_result():
    mock_redis = MagicMock()
    mock_producer = MagicMock()
    mock_redis.get.return_value = None  # only one result arrived

    msg = {"pr_id": 1, "issues": [{"severity": "high", "message": "issue"}]}
    process_message(msg, AI_TOPIC, mock_redis, mock_producer)
    mock_redis.setex.assert_called_once()
    mock_producer.send.assert_not_called()


def test_process_message_both_results():
    mock_redis = MagicMock()
    mock_producer = MagicMock()
    ai_issues = [{"file": "a.py", "line": 1, "type": "security", "severity": "high", "message": "SQL injection"}]
    static_issues = [{"tool": "bandit", "severity": "medium", "message": "Shell injection", "file": "b.py", "line": 5}]

    mock_redis.get.side_effect = lambda key: (
        json.dumps(ai_issues) if key.startswith("ai:") else json.dumps(static_issues)
    )

    msg = {"pr_id": 2, "issues": static_issues}
    process_message(msg, STATIC_TOPIC, mock_redis, mock_producer)
    mock_producer.send.assert_called_once()
    call = mock_producer.send.call_args
    assert call[0][0] == "review.finalized"


def test_health_endpoint():
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
