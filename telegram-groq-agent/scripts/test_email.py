#!/usr/bin/env python
"""Send a test appointment email to verify Gmail SMTP setup.

Requires in .env:
  GMAIL_SMTP_USER=your@gmail.com
  GMAIL_APP_PASSWORD=16-char-app-password
  STAFF_EMAIL=recipient@gmail.com

Usage:
  python scripts/test_email.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.bootstrap import create_email_notifier


async def main() -> None:
    notifier = create_email_notifier()
    if not notifier:
        print("ERROR: Email not configured. Set GMAIL_SMTP_USER, GMAIL_APP_PASSWORD, STAFF_EMAIL in .env")
        sys.exit(1)

    print(f"Sending test email to {notifier.staff_email} ...")
    ok = await notifier.notify_lead(
        business_name="Royal Aesthetic Clinic (TEST)",
        status="appointment_request",
        channel="test",
        profile={
            "name": "Test Patient",
            "phone": "0312-0000000",
            "concern": "HydraFacial consultation",
            "preferred_day": "Tuesday",
            "preferred_time": "2 PM",
        },
        staff_summary="This is a test email from test_email.py — your Gmail setup works.",
    )

    if ok:
        print("OK — check your inbox (and spam folder).")
    else:
        print("FAILED — check App Password and 2-Step Verification on your Google account.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
