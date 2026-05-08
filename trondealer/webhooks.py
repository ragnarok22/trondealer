"""Webhook verification and parsing helpers."""

from __future__ import annotations

import hashlib
import hmac
import json

from pydantic import ValidationError

from .exceptions import TronDealerValidationError
from .models import WebhookEvent


def _normalize_signature(signature: str) -> str:
    value = signature.strip()
    if value.lower().startswith("sha256="):
        return value.split("=", 1)[1].lower()
    return value.lower()


def verify_webhook_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    """Verify an X-Signature-256 HMAC-SHA256 signature.

    TronDealer documentation currently shows both raw hexadecimal signatures and
    `sha256=<hex>` signatures. This helper accepts both formats and always uses
    constant-time comparison.
    """

    if not signature or not secret:
        return False

    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    received = _normalize_signature(signature)
    return hmac.compare_digest(received, expected)


def parse_webhook_event(raw_body: bytes) -> WebhookEvent:
    """Parse a raw webhook request body into a typed event model."""

    try:
        payload = json.loads(raw_body.decode("utf-8"))
        return WebhookEvent.model_validate(payload)
    except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as exc:
        raise TronDealerValidationError("Invalid webhook payload") from exc
