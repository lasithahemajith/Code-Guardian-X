"""Static analysis runners: bandit, pylint, semgrep."""
from __future__ import annotations

import contextlib
import json
import logging
import os
import subprocess
import tempfile
from typing import Generator, List

logger = logging.getLogger(__name__)


@contextlib.contextmanager
def _temp_code_file(code: str, filename: str) -> Generator[str, None, None]:
    """Write code to a temporary file and clean up on exit."""
    suffix = os.path.splitext(filename)[1] or ".py"
    tmp = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8")
    try:
        tmp.write(code)
        tmp.flush()
        tmp.close()
        yield tmp.name
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


def run_bandit(code: str, filename: str) -> List[dict]:
    """Run bandit on the given code snippet."""
    issues: List[dict] = []
    with _temp_code_file(code, filename) as tmp_path:
        try:
            result = subprocess.run(
                ["bandit", "-f", "json", "-q", tmp_path],
                capture_output=True, text=True, timeout=30,
            )
            if result.stdout:
                data = json.loads(result.stdout)
                for r in data.get("results", []):
                    issues.append({
                        "tool": "bandit",
                        "severity": r.get("issue_severity", "medium").lower(),
                        "message": r.get("issue_text", ""),
                        "file": filename,
                        "line": r.get("line_number"),
                    })
        except FileNotFoundError:
            logger.warning("bandit not found, skipping")
        except subprocess.TimeoutExpired:
            logger.warning("bandit timed out")
        except json.JSONDecodeError as exc:
            logger.warning("bandit output parse error: %s", exc)
        except Exception as exc:
            logger.error("bandit error: %s", exc)
    return issues


def run_pylint(code: str, filename: str) -> List[dict]:
    """Run pylint on the given code snippet."""
    issues: List[dict] = []
    with _temp_code_file(code, filename) as tmp_path:
        try:
            result = subprocess.run(
                ["pylint", "--output-format=json", "--score=no", tmp_path],
                capture_output=True, text=True, timeout=30,
            )
            if result.stdout:
                data = json.loads(result.stdout)
                severity_map = {"E": "high", "W": "medium", "C": "low", "R": "info", "I": "info", "F": "high"}
                for msg in data:
                    sev = severity_map.get(msg.get("type", "I")[0].upper(), "info")
                    issues.append({
                        "tool": "pylint",
                        "severity": sev,
                        "message": f"[{msg.get('message-id', '')}] {msg.get('message', '')}",
                        "file": filename,
                        "line": msg.get("line"),
                    })
        except FileNotFoundError:
            logger.warning("pylint not found, skipping")
        except subprocess.TimeoutExpired:
            logger.warning("pylint timed out")
        except json.JSONDecodeError as exc:
            logger.warning("pylint output parse error: %s", exc)
        except Exception as exc:
            logger.error("pylint error: %s", exc)
    return issues


def run_semgrep(code: str, filename: str) -> List[dict]:
    """Run semgrep on the given code snippet."""
    issues: List[dict] = []
    with _temp_code_file(code, filename) as tmp_path:
        try:
            result = subprocess.run(
                ["semgrep", "--config=auto", "--json", "--quiet", tmp_path],
                capture_output=True, text=True, timeout=60,
            )
            if result.stdout:
                data = json.loads(result.stdout)
                for finding in data.get("results", []):
                    extra = finding.get("extra", {})
                    severity = extra.get("severity", "WARNING").lower()
                    if severity == "warning":
                        severity = "medium"
                    elif severity == "error":
                        severity = "high"
                    issues.append({
                        "tool": "semgrep",
                        "severity": severity,
                        "message": extra.get("message", ""),
                        "file": filename,
                        "line": finding.get("start", {}).get("line"),
                    })
        except FileNotFoundError:
            logger.warning("semgrep not found, skipping")
        except subprocess.TimeoutExpired:
            logger.warning("semgrep timed out")
        except json.JSONDecodeError as exc:
            logger.warning("semgrep output parse error: %s", exc)
        except Exception as exc:
            logger.error("semgrep error: %s", exc)
    return issues
