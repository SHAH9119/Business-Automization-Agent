"""Tests for Gmail SMTP email notifier."""

import unittest
from unittest.mock import MagicMock, patch

from app.email_notifier import EmailNotifier


class EmailNotifierTest(unittest.TestCase):
    def test_disabled_when_credentials_missing(self):
        notifier = EmailNotifier(smtp_user="", smtp_app_password="", staff_email="")
        self.assertFalse(notifier.enabled)

    def test_build_message_subject(self):
        notifier = EmailNotifier(
            smtp_user="sender@gmail.com",
            smtp_app_password="app-pass",
            staff_email="staff@gmail.com",
        )
        message = notifier._build_message(
            business_name="Royce Aesthetics",
            status="appointment_request",
            channel="whatsapp",
            profile={
                "name": "Fatima",
                "phone": "0312-1111111",
                "concern": "HydraFacial",
                "preferred_day": "Tuesday",
                "preferred_time": "2 PM",
            },
            staff_summary="Test summary",
        )
        self.assertIn("Fatima", message["Subject"])
        self.assertEqual(message["To"], "staff@gmail.com")

    def test_notify_lead_sends_via_smtp(self):
        notifier = EmailNotifier(
            smtp_user="sender@gmail.com",
            smtp_app_password="app-pass",
            staff_email="staff@gmail.com",
        )

        with patch.object(notifier, "_send_sync") as mock_send:
            import asyncio

            result = asyncio.run(
                notifier.notify_lead(
                    business_name="Test Clinic",
                    status="appointment_request",
                    channel="telegram",
                    profile={"name": "Ali", "phone": "0300-0000000"},
                )
            )

        self.assertTrue(result)
        mock_send.assert_called_once()
