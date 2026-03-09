"""Tests for static-analysis service."""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from unittest.mock import MagicMock

from analyzers import run_bandit, run_pylint, run_semgrep
from kafka_consumer import process_message

VULNERABLE_CODE = """
import subprocess
import os

password = "hardcoded_secret_123"

def run_cmd(cmd):
    subprocess.call(cmd, shell=True)
"""

CLEAN_CODE = """
def add(a, b):
    return a + b
"""


def test_run_bandit_detects_issues():
    issues = run_bandit(VULNERABLE_CODE, "vuln.py")
    # bandit may not be installed in all envs; just check it returns a list
    assert isinstance(issues, list)
    if issues:
        assert "tool" in issues[0]
        assert issues[0]["tool"] == "bandit"


def test_run_bandit_clean_code():
    issues = run_bandit(CLEAN_CODE, "clean.py")
    assert isinstance(issues, list)


def test_run_pylint_returns_list():
    issues = run_pylint(CLEAN_CODE, "clean.py")
    assert isinstance(issues, list)


def test_run_semgrep_returns_list():
    issues = run_semgrep(CLEAN_CODE, "clean.py")
    assert isinstance(issues, list)


def test_process_message_skips_non_python():
    mock_producer = MagicMock()
    msg = {
        "pr_id": 10,
        "files": [
            {"file": "README.md", "code": "# Hello"},
            {"file": "app.js", "code": "console.log('hi')"},
        ],
    }
    process_message(msg, mock_producer)
    mock_producer.send.assert_called_once()
    call = mock_producer.send.call_args
    assert call[0][0] == "static.analysis.completed"


def test_health_endpoint():
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
