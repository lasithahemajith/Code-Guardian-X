"""Tests for repo-service."""
from __future__ import annotations

import hashlib
import hmac
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from unittest.mock import patch

from github_handler import verify_signature, extract_pr_event
from gitlab_handler import verify_token as gl_verify, extract_pr_event as gl_extract


def test_verify_signature_valid():
    body = b'{"action":"opened"}'
    secret = "mysecret"
    sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_signature(body, secret, sig) is True


def test_verify_signature_invalid():
    body = b'{"action":"opened"}'
    assert verify_signature(body, "mysecret", "sha256=invalidsig") is False


def test_verify_signature_missing():
    assert verify_signature(b"body", "secret", "") is False


def test_extract_pr_event_github_opened():
    payload = {
        "action": "opened",
        "pull_request": {
            "number": 42,
            "user": {"login": "alice"},
            "diff_url": "https://github.com/company/repo/pull/42.diff",
        },
        "repository": {"full_name": "company/repo"},
    }
    event = extract_pr_event(payload)
    assert event is not None
    assert event["pr_id"] == 42
    assert event["author"] == "alice"
    assert event["provider"] == "github"


def test_extract_pr_event_github_closed():
    payload = {"action": "closed", "pull_request": {}, "repository": {}}
    assert extract_pr_event(payload) is None


def test_gitlab_verify_token_valid():
    assert gl_verify("my-token", "my-token") is True


def test_gitlab_verify_token_invalid():
    assert gl_verify("wrong", "my-token") is False


def test_extract_pr_event_gitlab():
    payload = {
        "object_kind": "merge_request",
        "user": {"username": "bob"},
        "project": {"path_with_namespace": "company/repo"},
        "object_attributes": {
            "iid": 7,
            "state": "opened",
            "action": "open",
            "url": "https://gitlab.com/company/repo/merge_requests/7",
        },
    }
    event = gl_extract(payload)
    assert event is not None
    assert event["pr_id"] == 7
    assert event["provider"] == "gitlab"


def test_github_webhook_valid():
    from main import app
    client = TestClient(app)
    payload = {
        "action": "opened",
        "pull_request": {
            "number": 1,
            "user": {"login": "dev"},
            "diff_url": "https://example.com/diff",
        },
        "repository": {"full_name": "company/repo"},
    }
    body = json.dumps(payload).encode()
    with patch("main._send_to_kafka"):
        resp = client.post(
            "/webhooks/github",
            content=body,
            headers={"x-github-event": "pull_request", "content-type": "application/json"},
        )
    assert resp.status_code == 200


def test_github_webhook_bad_signature():
    from main import app
    client = TestClient(app)
    payload = b'{"action":"opened"}'
    resp = client.post(
        "/webhooks/github",
        content=payload,
        headers={
            "x-github-event": "pull_request",
            "x-hub-signature-256": "sha256=badsignature",
            "content-type": "application/json",
        },
    )
    assert resp.status_code == 400
