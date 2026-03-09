"""AI code analyzer for ai-service."""
from __future__ import annotations

import logging
import os
import re
from typing import List

logger = logging.getLogger(__name__)


class CodeAnalyzer:
    """Analyze code for security, performance, and maintainability issues."""

    def analyze(self, code: str, filename: str) -> List[dict]:
        api_key = os.getenv("OPENAI_API_KEY", "")
        if api_key:
            return self._analyze_openai(code, filename, api_key)
        return self._analyze_rule_based(code, filename)

    def _analyze_openai(self, code: str, filename: str, api_key: str) -> List[dict]:
        try:
            import openai
            client = openai.OpenAI(api_key=api_key)
            prompt = (
                f"You are a senior code reviewer. Analyze this file '{filename}' for security, "
                "performance, and maintainability issues. "
                "Return a JSON array of issues with fields: "
                "file, line (int or null), type (security/performance/bug/maintainability), "
                "severity (critical/high/medium/low/info), message, suggestion.\n\n"
                f"```\n{code}\n```\n\n"
                "Respond ONLY with the JSON array."
            )
            model_name = os.getenv("OPENAI_MODEL", "gpt-4")
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000,
            )
            import json
            content = response.choices[0].message.content or "[]"
            return json.loads(content)
        except Exception as exc:
            logger.warning("OpenAI analysis failed, falling back to rule-based: %s", exc)
            return self._analyze_rule_based(code, filename)

    def _analyze_rule_based(self, code: str, filename: str) -> List[dict]:
        issues: List[dict] = []

        # SQL injection: string concatenation in query
        if re.search(r"(SELECT|INSERT|UPDATE|DELETE).*\+\s*\w", code, re.IGNORECASE):
            issues.append({
                "file": filename, "line": None,
                "type": "security", "severity": "critical",
                "message": "Potential SQL injection via string concatenation",
                "suggestion": "Use parameterized queries or an ORM",
            })

        # Hardcoded secrets
        if re.search(r'(password|secret|api_key|token)\s*=\s*["\'][^"\']{4,}["\']', code, re.IGNORECASE):
            issues.append({
                "file": filename, "line": None,
                "type": "security", "severity": "high",
                "message": "Hardcoded credential or secret detected",
                "suggestion": "Use environment variables or a secrets manager",
            })

        # eval() usage
        if re.search(r"\beval\s*\(", code):
            issues.append({
                "file": filename, "line": None,
                "type": "security", "severity": "high",
                "message": "Use of eval() is dangerous",
                "suggestion": "Avoid eval(); use ast.literal_eval for safe parsing",
            })

        # Infinite loop without break
        if re.search(r"while\s+True\s*:", code) and "break" not in code:
            issues.append({
                "file": filename, "line": None,
                "type": "performance", "severity": "medium",
                "message": "Potential infinite loop: while True without break",
                "suggestion": "Add a break condition or use a bounded loop",
            })

        # Missing error handling
        if "open(" in code and "try" not in code:
            issues.append({
                "file": filename, "line": None,
                "type": "maintainability", "severity": "low",
                "message": "File open without try/except",
                "suggestion": "Wrap file operations in try/except or use context manager",
            })

        return issues


analyzer = CodeAnalyzer()
