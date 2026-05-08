# TronDealer Python SDK

[![CI](https://github.com/ragnarok22/trondealer/actions/workflows/ci.yml/badge.svg)](https://github.com/ragnarok22/trondealer/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/trondealer.svg)](https://pypi.org/project/trondealer/)
[![Python Versions](https://img.shields.io/pypi/pyversions/trondealer.svg)](https://pypi.org/project/trondealer/)
[![License](https://img.shields.io/pypi/l/trondealer.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-46aef7.svg)](https://docs.astral.sh/ruff/)

Typed Python SDK for the TronDealer API, built for backend integrations that assign deposit wallets, reconcile balances and transactions, and verify HMAC-signed webhooks.

The SDK follows the official integration guide as the primary source for the payment flow.

## Installation

```bash
pip install trondealer
```

For local development:

```bash
pip install -e ".[dev]"
```

This repository also supports `uv`, which is useful when your system Python is externally managed:

```bash
uv sync --extra dev
```

## Configuration

Store your API key in an environment variable or secret manager:

```bash
export TRONDEALER_API_KEY="td_..."
```

```python
import os

from trondealer import TronDealerClient

client = TronDealerClient(api_key=os.environ["TRONDEALER_API_KEY"])
```

Default configuration:

```python
client = TronDealerClient(
    api_key=os.environ["TRONDEALER_API_KEY"],
    base_url="https://www.trondealer.com/api/v2",
    timeout=10.0,
    max_retries=2,
)
```

## Public Registration

Public registration does not use normal API-key authentication. It posts to `/clients/register-public`, the canonical endpoint documented by the integration guide.

```python
from trondealer import TronDealerClient

client = TronDealerClient()
registration = client.register_client_public(
    name="My Shop",
    webhook_url="https://example.com/webhooks/trondealer",
    webhook_secret="a-long-random-secret",
    min_confirmations=15,
    sweep_wallet="0xABC...123",
    payout_method="wallet",
    turnstile_token="...",
)

api_key = registration.client.api_key
```

Advanced users can override the registration path if TronDealer changes the canonical endpoint:

```python
client = TronDealerClient(registration_endpoint="/clients/register-public")
```

## Assign A Wallet

Use one `label` per order or customer. TronDealer documents `label` as the user-side idempotency key.

```python
import os

from trondealer import TronDealerClient

client = TronDealerClient(api_key=os.environ["TRONDEALER_API_KEY"])

wallet = client.assign_wallet(label="order-A-1024")
print(wallet.address)
```

## Check A Balance

```python
balance = client.get_wallet_balance(address="0xABC...123")
print(balance.balances)
```

The integration guide shows balances grouped by network. The embedded OpenAPI schema currently shows a flatter balance map. The SDK accepts both shapes.

## List Transactions

```python
transactions = client.list_wallet_transactions(
    address="0xABC...123",
    status="confirmed",
    limit=20,
    offset=0,
)

for tx in transactions.transactions:
    print(tx.tx_hash, tx.amount, tx.status)
```

Supported transaction statuses:

- `detected`
- `confirmed`
- `notified`
- `swept`

## Verify Webhooks

TronDealer sends HMAC-SHA256 signatures in the `X-Signature-256` header when a webhook secret is configured. Always verify the signature against the raw request body before parsing JSON.

```python
from trondealer import parse_webhook_event, verify_webhook_signature

if verify_webhook_signature(raw_body, signature, webhook_secret):
    event = parse_webhook_event(raw_body)
```

The SDK accepts both documented signature formats: raw hex and `sha256=<hex>`.

### FastAPI

```python
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
    return {"status": "ok"}
```

### Flask

```python
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
    return "ok", 200
```

## Recommended Payment Flow

1. Create one wallet per order or customer using `label`.
2. Show the returned address to the user.
3. Wait for the `confirmed` or `notified` webhook.
4. Store `tx_hash + log_index` as a unique key to prevent double crediting.
5. Do not mark an order as paid when the transaction is only in `detected` status.

## Security Warnings

- Never expose the `x-api-key` in frontend or mobile apps.
- Store `api_key` and `webhook_secret` in environment variables or a secret manager.
- Always verify the webhook HMAC signature.
- Persist the raw body and signature for audit/debugging purposes.
- Do not print API keys, webhook secrets, or full signed webhook payloads in logs.

## Documentation Discrepancies

The official integration guide documents public registration as:

```text
POST /api/v2/clients/register-public
Auth: none, with Turnstile token
```

The API docs/OpenAPI surface may list the same public operation as:

```text
POST /api/v2/clients/register-open
```

This SDK uses `/clients/register-public` as canonical because the integration guide documents the complete registration flow, request body, auth behavior, and cURL example for that endpoint. The SDK does not silently switch to `/clients/register-open`. If needed, pass `registration_endpoint="/clients/register-open"` explicitly.

TODO before stable v1.0: verify `/clients/register-public` directly against the live API or with TronDealer maintainers.

Other known discrepancies:

- The guide shows per-network balance responses; embedded OpenAPI shows a flatter balance object.
- The guide shows raw hex webhook signatures; embedded OpenAPI describes `sha256=<hex>`.
- The guide says EVM wallet assignment returns an existing wallet for the same `label`; embedded OpenAPI only documents `201` for EVM assignment.

## Development

The Makefile runs tools through `uv run --extra dev`, so commands use the project development environment instead of depending on packages installed in your global Python.

```bash
make help
make test
make test:coverage
make lint
make format
make format:check
```

Equivalent direct commands after installing development dependencies:

```bash
pip install -e ".[dev]"
ruff check .
ruff format --check .
pytest
```

If your Python installation is externally managed and `pip install -e ".[dev]"` is blocked, use:

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run ruff format --check .
```
