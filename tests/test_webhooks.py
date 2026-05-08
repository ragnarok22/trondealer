from __future__ import annotations

import hashlib
import hmac

import pytest

from trondealer import parse_webhook_event, verify_webhook_signature
from trondealer.exceptions import TronDealerValidationError
from trondealer.models import WebhookSweptData, WebhookTransactionData


def test_verify_webhook_signature_accepts_raw_hex() -> None:
    raw_body = b'{"event":"transaction.confirmed"}'
    secret = "webhook-secret"
    signature = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()

    assert verify_webhook_signature(raw_body, signature, secret)


def test_verify_webhook_signature_accepts_sha256_prefix() -> None:
    raw_body = b'{"event":"transaction.confirmed"}'
    secret = "webhook-secret"
    digest = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()

    assert verify_webhook_signature(raw_body, f"sha256={digest}", secret)


def test_verify_webhook_signature_accepts_uppercase_prefix_digest_and_whitespace() -> None:
    raw_body = b'{"event":"transaction.confirmed"}'
    secret = "webhook-secret"
    digest = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest().upper()

    assert verify_webhook_signature(raw_body, f"  SHA256={digest}  ", secret)


def test_verify_webhook_signature_rejects_invalid_signature() -> None:
    assert not verify_webhook_signature(b"{}", "bad", "secret")


def test_verify_webhook_signature_rejects_missing_signature_or_secret() -> None:
    assert not verify_webhook_signature(b"{}", "", "secret")
    assert not verify_webhook_signature(b"{}", "signature", "")


def test_verify_webhook_signature_accepts_signed_empty_body() -> None:
    secret = "webhook-secret"
    signature = hmac.new(secret.encode(), b"", hashlib.sha256).hexdigest()

    assert verify_webhook_signature(b"", signature, secret)


def test_parse_webhook_event_transaction() -> None:
    event = parse_webhook_event(
        b'{"event":"transaction.confirmed","timestamp":"2026-03-30T14:25:30.000Z",'
        b'"data":{"tx_hash":"0xabc","amount":"150.50","asset":"USDT","network":"bsc"}}'
    )

    assert event.event == "transaction.confirmed"
    assert isinstance(event.data, WebhookTransactionData)
    assert event.data.tx_hash == "0xabc"


def test_parse_webhook_event_swept() -> None:
    event = parse_webhook_event(
        b'{"event":"transaction.swept","data":{"sweep_tx_hash":"0xdef",'
        b'"source_tx_hashes":["0xabc"],"asset":"USDT","amount":"1.0","network":"bsc"}}'
    )

    assert isinstance(event.data, WebhookSweptData)
    assert event.data.source_tx_hashes == ["0xabc"]


def test_parse_webhook_event_rejects_invalid_json() -> None:
    with pytest.raises(TronDealerValidationError):
        parse_webhook_event(b"not json")


def test_parse_webhook_event_rejects_invalid_utf8() -> None:
    with pytest.raises(TronDealerValidationError):
        parse_webhook_event(b"\xff")


def test_parse_webhook_event_rejects_missing_data() -> None:
    with pytest.raises(TronDealerValidationError):
        parse_webhook_event(b'{"event":"transaction.confirmed"}')
