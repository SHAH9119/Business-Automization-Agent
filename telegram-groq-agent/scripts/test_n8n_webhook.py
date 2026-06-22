#!/usr/bin/env python
"""Send a sample lead payload to your n8n webhook URL to verify connectivity.

Usage:
  python scripts/test_n8n_webhook.py
  python scripts/test_n8n_webhook.py --url http://localhost:5678/webhook/clinic-lead
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

import httpx

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import N8N_WEBHOOK_URL


SAMPLE_PAYLOAD = {
    "event": "lead_saved",
    "channel": "whatsapp",
    "chat_id": "wa:923001234567",
    "business_name": "Royal Aesthetic Clinic",
    "tenant_id": "royce_aesthetics_phase7_rawalpindi",
    "status": "appointment_request",
    "profile": {
        "name": "Test Patient",
        "phone": "0312-0000000",
        "concern": "HydraFacial",
        "preferred_day": "Tuesday",
        "preferred_time": "2 PM",
        "language": "roman_urdu",
    },
    "staff_summary": "TEST — n8n connectivity check from test_n8n_webhook.py",
    "handoff_reason": None,
    "lead_file": "test-lead.json",
}


async def main() -> None:
    parser = argparse.ArgumentParser(description="Test n8n webhook connectivity")
    parser.add_argument("--url", default=N8N_WEBHOOK_URL, help="n8n webhook URL")
    args = parser.parse_args()

    if not args.url:
        print("ERROR: No webhook URL. Set N8N_WEBHOOK_URL in .env or pass --url")
        sys.exit(1)

    print(f"POST {args.url}")
    print(json.dumps(SAMPLE_PAYLOAD, indent=2))

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.post(args.url, json=SAMPLE_PAYLOAD)

    print(f"\nStatus: {response.status_code}")
    print(f"Body:   {response.text[:500]}")

    if response.is_success:
        print("\nOK — n8n received the test payload. Check your n8n workflow execution log.")
    else:
        print("\nFAILED — check that n8n is running and the workflow is ACTIVE.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
