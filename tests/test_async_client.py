from __future__ import annotations

import httpx
import pytest

from trondealer import AsyncTronDealerClient
from trondealer.exceptions import TronDealerAuthenticationError, TronDealerValidationError

BASE_URL = "https://www.trondealer.com/api/v2"


class CloseTrackingAsyncClient(httpx.AsyncClient):
    def __init__(self) -> None:
        super().__init__(
            transport=httpx.MockTransport(lambda _request: httpx.Response(200, json={}))
        )
        self.close_called = False

    async def aclose(self) -> None:
        self.close_called = True
        await super().aclose()


@pytest.mark.anyio
async def test_async_context_manager_closes_owned_client() -> None:
    client = AsyncTronDealerClient()

    async with client as entered:
        assert entered is client


@pytest.mark.anyio
async def test_async_close_does_not_close_injected_client() -> None:
    http_client = CloseTrackingAsyncClient()

    await AsyncTronDealerClient(http_client=http_client).aclose()

    assert not http_client.close_called
    await http_client.aclose()


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
async def test_async_list_wallet_transactions_sends_optional_filters(httpx_mock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/wallets/transactions",
        json={
            "success": True,
            "transactions": [{"tx_hash": "0xabc", "amount": "10", "status": "confirmed"}],
        },
    )

    async with AsyncTronDealerClient(api_key="td_secret") as client:
        response = await client.list_wallet_transactions(
            address="0xabc",
            status="confirmed",
            limit=20,
            offset=0,
        )

    request = httpx_mock.get_request()
    assert request is not None
    assert request.read() == b'{"address":"0xabc","status":"confirmed","limit":20,"offset":0}'
    assert response.transactions[0].tx_hash == "0xabc"


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


@pytest.mark.anyio
async def test_async_retries_network_errors_and_preserves_cause(monkeypatch) -> None:
    request = httpx.Request("POST", f"{BASE_URL}/wallets/balance")

    async def handler(_request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    sleeps = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr("trondealer.async_client.asyncio.sleep", fake_sleep)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
        client = AsyncTronDealerClient(api_key="td_secret", max_retries=1, http_client=http_client)
        with pytest.raises(Exception) as exc_info:
            await client.get_wallet_balance("0xabc")

    assert exc_info.value.__class__.__name__ == "TronDealerNetworkError"
    assert isinstance(exc_info.value.__cause__, httpx.ConnectError)
    assert sleeps == [0.5]
