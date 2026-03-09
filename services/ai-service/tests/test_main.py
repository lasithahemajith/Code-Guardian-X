"""Tests for ai-service."""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from unittest.mock import MagicMock

from code_analyzer import CodeAnalyzer
from kafka_consumer import process_message


def test_rule_based_sql_injection():
    ca = CodeAnalyzer()
    code = 'query = "SELECT * FROM users WHERE id = " + user_id'
    issues = ca._analyze_rule_based(code, "db.py")
    types = [i["type"] for i in issues]
    assert "security" in types


def test_rule_based_hardcoded_secret():
    ca = CodeAnalyzer()
    code = 'password = "super_secret_pass"'
    issues = ca._analyze_rule_based(code, "config.py")
    messages = [i["message"] for i in issues]
    assert any("credential" in m.lower() or "secret" in m.lower() for m in messages)


def test_rule_based_eval():
    ca = CodeAnalyzer()
    code = "result = eval(user_input)"
    issues = ca._analyze_rule_based(code, "handler.py")
    assert any("eval" in i["message"] for i in issues)


def test_rule_based_no_issues():
    ca = CodeAnalyzer()
    code = "def add(a, b):\n    return a + b\n"
    issues = ca._analyze_rule_based(code, "math.py")
    assert issues == []


def test_rule_based_infinite_loop():
    ca = CodeAnalyzer()
    code = "while True:\n    do_something()\n"
    issues = ca._analyze_rule_based(code, "loop.py")
    assert any("infinite" in i["message"].lower() for i in issues)


def test_analyze_dispatches_to_rule_based_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    ca = CodeAnalyzer()
    result = ca.analyze("x = 1", "simple.py")
    assert isinstance(result, list)


def test_process_message():
    mock_producer = MagicMock()
    msg = {
        "pr_id": 5,
        "files": [
            {"file": "auth.py", "code": 'query = "SELECT * FROM users WHERE id = " + uid'},
        ],
    }
    process_message(msg, mock_producer)
    mock_producer.send.assert_called_once()
    call = mock_producer.send.call_args
    assert call[0][0] == "ai.review.completed"


def test_health_endpoint():
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
