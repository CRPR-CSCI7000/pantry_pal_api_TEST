"""
Email service — sends structured events to the pantrypal-email-worker.

This is the producer side of the event contract. The schema used here
must match what the email worker expects. This is the seam that will be
used for Data & Schema break tests.
"""
import json
import logging
from datetime import datetime, timezone

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# ─── Event schema version ────────────────────────────────────────────────────
# Bumping this version is one way to introduce a schema break test.
EVENT_SCHEMA_VERSION = '1.0.0'


def _build_envelope(event_type: str, payload: dict) -> dict:
    """
    Wrap a payload in a standard event envelope.

    Schema contract (v1.0.0):
      - schema_version: str
      - event_type: str        e.g. "pantry.item.added"
      - occurred_at: str       ISO-8601 UTC timestamp
      - payload: dict          event-specific data
    """
    return {
        'schema_version': EVENT_SCHEMA_VERSION,
        'event_type': event_type,
        'occurred_at': datetime.now(tz=timezone.utc).isoformat(),
        'payload': payload,
    }


def send_pantry_event(event_type: str, payload: dict) -> bool:
    """
    POST a pantry event to the email worker.
    Returns True on success, False on any error (fire-and-forget — never raises).

    Supported event types:
      - pantry.item.added
      - pantry.item.removed
      - pantry.item.expiring_soon   (future)
    """
    worker_url = getattr(settings, 'EMAIL_WORKER_URL', '')
    worker_key = getattr(settings, 'EMAIL_WORKER_API_KEY', '')

    if not worker_url:
        logger.debug('EMAIL_WORKER_URL not configured — skipping event %s', event_type)
        return False

    envelope = _build_envelope(event_type, payload)

    try:
        resp = requests.post(
            f'{worker_url}/events',
            json=envelope,
            headers={
                'Content-Type': 'application/json',
                'X-API-Key': worker_key,
            },
            timeout=3,
        )
        resp.raise_for_status()
        logger.info('Event %s delivered (status %s)', event_type, resp.status_code)
        return True
    except Exception as exc:
        logger.warning('Failed to deliver event %s: %s', event_type, exc)
        return False
