"""Flask webhook endpoint that verifies TronDealer HMAC signatures."""

from __future__ import annotations

import os

from flask import Flask, abort, request

from trondealer import parse_webhook_event, verify_webhook_signature

app = Flask(__name__)


@app.post("/webhooks/trondealer")
def trondealer_webhook() -> tuple[str, int]:
    raw_body = request.get_data(cache=False)
    signature = request.headers.get("X-Signature-256")
    secret = os.environ["TRONDEALER_WEBHOOK_SECRET"]

    if not signature or not verify_webhook_signature(raw_body, signature, secret):
        abort(401)

    event = parse_webhook_event(raw_body)
    if event.event == "transaction.confirmed":
        # Store tx_hash + log_index or event-specific unique index before crediting.
        pass

    return "ok", 200
