"""GitHub webhook handler."""
from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Optional

logger = logging.getLogger(__name__)

HANDLED_ACTIONS = {"opened", "synchronize", "reopened"}


def verify_signature(payload_body: bytes, secret: str, signature_header: str) -> bool:
    """Verify GitHub HMAC-SHA256 webhook signature."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = "sha256=" + hmac.new(
        secret.encode("utf-8"), payload_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def extract_pr_event(payload: dict) -> Optional[dict]:
    """Extract PREvent dict from a GitHub webhook payload."""
    action = payload.get("action", "")
    if action not in HANDLED_ACTIONS:
        return None
    pr = payload.get("pull_request", {})
    repo = payload.get("repository", {})
    return {
        "repo": repo.get("full_name", ""),
        "pr_id": pr.get("number", 0),
        "author": pr.get("user", {}).get("login", ""),
        "files": [],
        "diff_url": pr.get("diff_url", ""),
        "provider": "github",
    }
