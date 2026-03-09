"""GitLab webhook handler."""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)

HANDLED_STATES = {"opened", "update", "reopen"}


def verify_token(request_token: str, secret: str) -> bool:
    """Verify GitLab X-Gitlab-Token header."""
    return request_token == secret


def extract_pr_event(payload: dict) -> Optional[dict]:
    """Extract PREvent dict from a GitLab merge_request webhook payload."""
    attrs = payload.get("object_attributes", {})
    state = attrs.get("state", "")
    action = attrs.get("action", "")
    if action not in HANDLED_STATES and state != "opened":
        return None
    project = payload.get("project", {})
    return {
        "repo": project.get("path_with_namespace", ""),
        "pr_id": attrs.get("iid", 0),
        "author": payload.get("user", {}).get("username", ""),
        "files": [],
        "diff_url": attrs.get("url", ""),
        "provider": "gitlab",
    }
