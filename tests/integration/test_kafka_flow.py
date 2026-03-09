"""Integration tests for the Kafka event flow (all mocked)."""
from __future__ import annotations

import json
import sys
import os

# Repo root is 2 levels up from this file
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Add service paths
for svc in ["analysis-service", "ai-service", "review-aggregator", "notification-service"]:
    sys.path.insert(0, os.path.join(REPO_ROOT, "services", svc))

import pytest
from unittest.mock import MagicMock

from diff_extractor import prepare_analysis_files
from code_analyzer import CodeAnalyzer
from aggregator import aggregate_results


SAMPLE_DIFF = """\
diff --git a/auth.py b/auth.py
+++ b/auth.py
@@ -1,0 +1,5 @@
+import sqlite3
+def get_user(username):
+    conn = sqlite3.connect('users.db')
+    query = "SELECT * FROM users WHERE username = " + username
+    return conn.execute(query).fetchone()
"""


def test_full_pipeline_pr_to_analysis():
    """Test that a PR event flows through to code analysis ready event."""
    pr_event = {"pr_id": 1, "repo": "company/backend", "files": ["auth.py"], "author": "dev"}
    analysis = prepare_analysis_files(pr_event, SAMPLE_DIFF)
    assert analysis["pr_id"] == 1
    assert len(analysis["files"]) == 1
    assert analysis["files"][0]["file"] == "auth.py"


def test_full_pipeline_analysis_to_ai_review():
    """Test that code is analyzed and issues are produced."""
    ca = CodeAnalyzer()
    code = 'query = "SELECT * FROM users WHERE id = " + user_id\npassword = "secret123"'
    issues = ca.analyze(code, "auth.py")
    assert any(i["type"] == "security" for i in issues)


def test_full_pipeline_aggregation():
    """Test that AI and static results are merged correctly."""
    ai_issues = [{"file": "auth.py", "line": 4, "type": "security", "severity": "critical",
                  "message": "SQL injection"}]
    static_issues = [{"tool": "bandit", "severity": "high", "message": "Hardcoded secret",
                      "file": "auth.py", "line": 1}]
    result = aggregate_results(ai_issues, static_issues)
    assert result["summary"]["critical"] == 1
    assert result["summary"]["high"] == 1
    assert len(result["issues"]) == 2


def test_full_pipeline_ordering():
    """Test that issues are ordered by severity."""
    ai_issues = [
        {"file": "a.py", "line": 1, "type": "bug", "severity": "low", "message": "Minor"},
        {"file": "b.py", "line": 2, "type": "security", "severity": "critical", "message": "Critical"},
    ]
    result = aggregate_results(ai_issues, [])
    assert result["issues"][0]["severity"] == "critical"
    assert result["issues"][1]["severity"] == "low"
