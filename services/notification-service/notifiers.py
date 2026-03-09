"""Notification senders for GitHub, Slack, and email."""
from __future__ import annotations

import logging
import os
import smtplib
from email.mime.text import MIMEText

import aiohttp

logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "25"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
NOTIFY_EMAIL_TO = os.getenv("NOTIFY_EMAIL_TO", "")


def format_summary(review_data: dict) -> str:
    pr_id = review_data.get("pr_id", "?")
    summary = review_data.get("summary", {})
    issues = review_data.get("issues", [])

    lines = [f"## AI Code Review Summary — PR #{pr_id}\n"]
    if summary:
        lines.append(
            f"**Critical:** {summary.get('critical', 0)} | "
            f"**High:** {summary.get('high', 0)} | "
            f"**Medium:** {summary.get('medium', 0)} | "
            f"**Low:** {summary.get('low', 0)}\n"
        )
    for issue in issues[:10]:  # limit to top 10
        sev = issue.get("severity", "info").upper()
        file_info = f"`{issue.get('file', 'unknown')}`"
        if issue.get("line"):
            file_info += f" line {issue['line']}"
        lines.append(f"- **[{sev}]** {file_info}: {issue.get('message', '')}")
        if issue.get("suggestion"):
            lines.append(f"  > 💡 {issue['suggestion']}")
    return "\n".join(lines)


class GitHubNotifier:
    async def post_pr_comment(self, repo: str, pr_number: int, review_data: dict) -> bool:
        if not GITHUB_TOKEN:
            logger.info("GITHUB_TOKEN not set, skipping GitHub comment")
            return False
        body = format_summary(review_data)
        url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json",
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={"body": body}, headers=headers) as resp:
                    if resp.status in (200, 201):
                        logger.info("Posted GitHub comment on PR %s#%d", repo, pr_number)
                        return True
                    logger.warning("GitHub comment failed: %s", resp.status)
        except Exception as exc:
            logger.error("GitHub notifier error: %s", exc)
        return False


class SlackNotifier:
    async def send_message(self, review_data: dict) -> bool:
        if not SLACK_WEBHOOK_URL:
            logger.info("SLACK_WEBHOOK_URL not set, skipping Slack notification")
            return False
        text = format_summary(review_data)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(SLACK_WEBHOOK_URL, json={"text": text}) as resp:
                    if resp.status == 200:
                        logger.info("Sent Slack notification")
                        return True
                    logger.warning("Slack notification failed: %s", resp.status)
        except Exception as exc:
            logger.error("Slack notifier error: %s", exc)
        return False


class EmailNotifier:
    def send(self, review_data: dict) -> bool:
        if not NOTIFY_EMAIL_TO:
            logger.info("NOTIFY_EMAIL_TO not set, skipping email")
            return False
        subject = f"CodeGuardian: PR #{review_data.get('pr_id')} Review Complete"
        body = format_summary(review_data)
        msg = MIMEText(body, "plain")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER or "codeguardian@localhost"
        msg["To"] = NOTIFY_EMAIL_TO
        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
                if SMTP_USER and SMTP_PASSWORD:
                    smtp.login(SMTP_USER, SMTP_PASSWORD)
                smtp.sendmail(msg["From"], [NOTIFY_EMAIL_TO], msg.as_string())
            logger.info("Sent email notification to %s", NOTIFY_EMAIL_TO)
            return True
        except Exception as exc:
            logger.error("Email notifier error: %s", exc)
        return False
