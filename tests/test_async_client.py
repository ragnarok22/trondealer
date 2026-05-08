from __future__ import annotations

import httpx
import pytest

from trondealer import AsyncTronDealerClient
from trondealer.exceptions import TronDealerAuthenticationError, TronDealerValidationError

BASE_URL = "https://www.trondealer.com/api/v2"


@pytest.mark.anyio
async def test_async_register_client_public_uses_canonical_endpoint_without_api_key(
    httpx_mock,
) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/clients/register-public",
        status_code=201,
        json={"success": True, "client": {"name": "My Shop", "api_key": "td_abc123"}},
    )

    async with AsyncTronDealerClient(api_key="td_should_not_be_sent") as client:
        response = await client.register_client_public(name="My Shop")

    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers.get("x-api-key") is None
    assert response.client.api_key == "td_abc123"


@pytest.mark.anyio
async def test_async_assign_wallet_sends_api_key_and_label(httpx_mock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/wallets/assign",
        status_code=201,
        json={"success": True, "wallet": {"address": "0xabc", "label": "order-123"}},
    )

    async with AsyncTronDealerClient(api_key="td_secret") as client:
        wallet = await client.assign_wallet("order-123")

    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["x-api-key"] == "td_secret"
    assert request.read() == b'{"label":"order-123"}'
    assert wallet.address == "0xabc"


@pytest.mark.anyio
async def test_async_authenticated_endpoint_requires_api_key() -> None:
    async with AsyncTronDealerClient() as client:
        with pytest.raises(TronDealerAuthenticationError):
            await client.assign_wallet("order-123")


@pytest.mark.anyio
async def test_async_maps_validation_error(httpx_mock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/wallets/balance",
        status_code=400,
        json={"error": "address is required"},
    )

    async with AsyncTronDealerClient(api_key="td_secret") as client:
        with pytest.raises(TronDealerValidationError):
            await client.get_wallet_balance("")


@pytest.mark.anyio
async def test_async_retries_transient_http_errors(monkeypatch) -> None:
    responses = iter(
        [
            httpx.Response(503, request=httpx.Request("POST", f"{BASE_URL}/wallets/balance")),
            httpx.Response(
                200,
                json={"success": True, "balances": {}},
                request=httpx.Request("POST", f"{BASE_URL}/wallets/balance"),
            ),
        ]
    )
    requests = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return next(responses)

    sleeps = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr("trondealer.async_client.asyncio.sleep", fake_sleep)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = AsyncTronDealerClient(api_key="td_secret", http_client=http_client)
        balance = await client.get_wallet_balance("0xabc")

    assert balance.success is True
    assert len(requests) == 2
    assert sleeps == [0.5]
