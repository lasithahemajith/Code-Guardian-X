"""Tests for analysis-service."""
from __future__ import annotations

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from unittest.mock import MagicMock

from diff_extractor import extract_changed_files, prepare_analysis_files
from kafka_consumer import process_message


SAMPLE_DIFF = """\
diff --git a/auth.py b/auth.py
--- a/auth.py
+++ b/auth.py
@@ -1,3 +1,4 @@
+import os
+def login(user):
+    return user
"""


def test_extract_changed_files_basic():
    files = extract_changed_files(SAMPLE_DIFF)
    assert len(files) == 1
    assert files[0]["file"] == "auth.py"
    assert "import os" in files[0]["code"]


def test_extract_changed_files_multiple():
    diff = (
        "diff --git a/a.py b/a.py\n+++ b/a.py\n+line_a\n"
        "diff --git a/b.py b/b.py\n+++ b/b.py\n+line_b\n"
    )
    files = extract_changed_files(diff)
    assert len(files) == 2
    assert files[0]["file"] == "a.py"
    assert files[1]["file"] == "b.py"


def test_extract_changed_files_empty():
    assert extract_changed_files("") == []


def test_prepare_analysis_files_with_diff():
    pr_event = {"pr_id": 1, "files": ["auth.py"]}
    result = prepare_analysis_files(pr_event, SAMPLE_DIFF)
    assert result["pr_id"] == 1
    assert len(result["files"]) == 1


def test_prepare_analysis_files_fallback():
    pr_event = {"pr_id": 2, "files": ["service.py", "utils.py"]}
    result = prepare_analysis_files(pr_event, "")
    assert len(result["files"]) == 2
    assert result["files"][0]["file"] == "service.py"


def test_process_message():
    mock_producer = MagicMock()
    pr_event = {"pr_id": 99, "files": ["main.py"], "repo": "company/repo"}
    process_message(pr_event, mock_producer)
    mock_producer.send.assert_called_once()
    call_kwargs = mock_producer.send.call_args
    assert call_kwargs[0][0] == "code.analysis.ready"


def test_health_endpoint():
    from fastapi.testclient import TestClient
    from main import app
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
