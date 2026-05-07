"""FastAPI webhook endpoint that verifies TronDealer HMAC signatures."""

from __future__ import annotations

import os

from fastapi import FastAPI, Header, HTTPException, Request

from trondealer import parse_webhook_event, verify_webhook_signature

app = FastAPI()


@app.post("/webhooks/trondealer")
async def trondealer_webhook(
    request: Request,
    x_signature_256: str | None = Header(default=None),
) -> dict[str, str]:
    raw_body = await request.body()
    secret = os.environ["TRONDEALER_WEBHOOK_SECRET"]

    if not x_signature_256 or not verify_webhook_signature(raw_body, x_signature_256, secret):
        raise HTTPException(status_code=401, detail="invalid signature")

    event = parse_webhook_event(raw_body)
    if event.event == "transaction.confirmed":
        # Store tx_hash + log_index or event-specific unique index before crediting.
        pass

    return {"status": "ok"}
