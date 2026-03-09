"""Result aggregation logic for review-aggregator."""
from __future__ import annotations

from typing import List

SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]


def _normalize_severity(sev: str) -> str:
    sev = sev.lower()
    if sev in SEVERITY_ORDER:
        return sev
    return "info"


def aggregate_results(ai_issues: List[dict], static_issues: List[dict]) -> dict:
    """Merge AI and static analysis results, deduplicate, and rank by severity."""
    seen: set = set()
    merged: List[dict] = []

    for issue in ai_issues:
        key = (issue.get("file"), issue.get("line"), issue.get("message", "")[:80])
        if key not in seen:
            seen.add(key)
            issue["source"] = "ai"
            issue["severity"] = _normalize_severity(issue.get("severity", "info"))
            merged.append(issue)

    for issue in static_issues:
        normalized = {
            "file": issue.get("file"),
            "line": issue.get("line"),
            "type": "static",
            "severity": _normalize_severity(issue.get("severity", "info")),
            "message": f"[{issue.get('tool', 'static')}] {issue.get('message', '')}",
            "suggestion": None,
            "source": issue.get("tool", "static"),
        }
        key = (normalized["file"], normalized["line"], normalized["message"][:80])
        if key not in seen:
            seen.add(key)
            merged.append(normalized)

    merged.sort(key=lambda x: SEVERITY_ORDER.index(_normalize_severity(x.get("severity", "info"))))

    summary: dict = {s: 0 for s in SEVERITY_ORDER}
    for issue in merged:
        severity = issue.get("severity", "info")
        summary[severity] = summary.get(severity, 0) + 1

    return {"summary": summary, "issues": merged}
