"""Send appointment/handoff alerts via Gmail SMTP (free, no n8n required).

Uses a Google App Password — not your normal Gmail password.
Setup: Google Account → Security → 2-Step Verification → App passwords.

Gmail API is also free, but SMTP + App Password is simpler for one inbox.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

logger = logging.getLogger(__name__)

GMAIL_SMTP_HOST = "smtp.gmail.com"
GMAIL_SMTP_PORT = 587


class EmailNotifier:
    """Send lead alerts to a staff inbox when appointments are saved."""

    def __init__(
        self,
        *,
        smtp_user: str,
        smtp_app_password: str,
        staff_email: str,
        from_name: str = "Clinic Agent",
    ):
        self.smtp_user = smtp_user.strip()
        self.smtp_app_password = smtp_app_password.strip()
        self.staff_email = staff_email.strip()
        self.from_name = from_name.strip() or "Clinic Agent"

    @property
    def enabled(self) -> bool:
        return bool(self.smtp_user and self.smtp_app_password and self.staff_email)

    def _build_message(
        self,
        *,
        business_name: str,
        status: str,
        channel: str,
        profile: dict[str, Any],
        staff_summary: str | None,
    ) -> MIMEMultipart:
        name = profile.get("name") or "Unknown"
        subject_status = "Appointment Request" if status == "appointment_request" else "Staff Handoff"
        subject = f"[{business_name}] {subject_status} — {name}"

        body_lines = [
            f"New {subject_status.lower()} via {channel}",
            f"Business: {business_name}",
            "",
            f"Name:           {profile.get('name') or '-'}",
            f"Phone:          {profile.get('phone') or '-'}",
            f"Concern:        {profile.get('concern') or '-'}",
            f"Preferred day:  {profile.get('preferred_day') or '-'}",
            f"Preferred time: {profile.get('preferred_time') or '-'}",
            "",
        ]
        if staff_summary:
            body_lines.extend(["--- Staff summary ---", staff_summary, ""])

        body_lines.append("— Sent automatically by your clinic AI agent")

        message = MIMEMultipart()
        message["From"] = f"{self.from_name} <{self.smtp_user}>"
        message["To"] = self.staff_email
        message["Subject"] = subject
        message.attach(MIMEText("\n".join(body_lines), "plain", "utf-8"))
        return message

    def _send_sync(self, message: MIMEMultipart) -> None:
        with smtplib.SMTP(GMAIL_SMTP_HOST, GMAIL_SMTP_PORT, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.smtp_user, self.smtp_app_password)
            server.send_message(message)

    async def notify_lead(
        self,
        *,
        business_name: str,
        status: str,
        channel: str,
        profile: dict[str, Any],
        staff_summary: str | None = None,
    ) -> bool:
        if not self.enabled:
            return False

        message = self._build_message(
            business_name=business_name,
            status=status,
            channel=channel,
            profile=profile,
            staff_summary=staff_summary,
        )

        try:
            await asyncio.to_thread(self._send_sync, message)
            logger.info("Email sent to %s (%s)", self.staff_email, status)
            return True
        except Exception as exc:
            logger.warning("Email delivery failed: %s", exc)
            return False
