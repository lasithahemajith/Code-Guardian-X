"""Diff extractor for analysis-service."""
from __future__ import annotations

from typing import List, Dict


def extract_changed_files(diff_content: str) -> List[Dict[str, str]]:
    """Parse a unified git diff and return list of {file, code} dicts."""
    files: List[Dict[str, str]] = []
    current_file: str = ""
    current_lines: List[str] = []

    for line in diff_content.splitlines():
        if line.startswith("diff --git"):
            if current_file and current_lines:
                files.append({"file": current_file, "code": "\n".join(current_lines)})
            current_file = ""
            current_lines = []
        elif line.startswith("+++ b/"):
            current_file = line[6:]
        elif line.startswith("+") and not line.startswith("+++"):
            current_lines.append(line[1:])

    if current_file and current_lines:
        files.append({"file": current_file, "code": "\n".join(current_lines)})

    return files


def prepare_analysis_files(pr_event: dict, diff_content: str) -> dict:
    """Build a CodeAnalysisReady event dict from a PR event and diff content."""
    if diff_content:
        file_contents = extract_changed_files(diff_content)
    else:
        # Fallback: use filename list from pr_event with empty code
        file_contents = [{"file": f, "code": ""} for f in pr_event.get("files", [])]

    return {
        "pr_id": pr_event["pr_id"],
        "files": file_contents,
    }
