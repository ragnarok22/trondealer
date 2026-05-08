from __future__ import annotations

import httpx
import pytest

from trondealer import TronDealerClient
from trondealer.exceptions import (
    TronDealerAPIError,
    TronDealerAuthenticationError,
    TronDealerNetworkError,
    TronDealerRateLimitError,
    TronDealerValidationError,
)

BASE_URL = "https://www.trondealer.com/api/v2"


def test_register_client_public_uses_canonical_endpoint_without_api_key(httpx_mock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/clients/register-public",
        status_code=201,
        json={
            "success": True,
            "client": {
                "id": "client-id",
                "name": "My Shop",
                "api_key": "td_abc123",
                "payout_method": "wallet",
            },
        },
    )

    client = TronDealerClient(api_key="td_should_not_be_sent")
    response = client.register_client_public(
        name="My Shop",
        webhook_url="https://example.com/webhooks/trondealer",
        webhook_secret="secret",
        min_confirmations=15,
        sweep_wallet="0xABC",
        payout_method="wallet",
        turnstile_token="turnstile-token",
    )

    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers.get("x-api-key") is None
    assert request.url.path == "/api/v2/clients/register-public"
    assert response.client.api_key == "td_abc123"


def test_registration_endpoint_can_be_overridden(httpx_mock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/clients/register-open",
        status_code=201,
        json={"success": True, "client": {"name": "My Shop"}},
    )

    client = TronDealerClient(registration_endpoint="/clients/register-open")
    client.register_client_public(name="My Shop")

    request = httpx_mock.get_request()
    assert request is not None
    assert request.url.path == "/api/v2/clients/register-open"


def test_assign_wallet_sends_api_key_and_label(httpx_mock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/wallets/assign",
        status_code=201,
        json={
            "success": True,
            "wallet": {
                "id": "wallet-id",
                "address": "0xabc",
                "label": "order-123",
                "status": "active",
            },
        },
    )

    wallet = TronDealerClient(api_key="td_secret").assign_wallet("order-123")

    request = httpx_mock.get_request()
    assert request is not None
    assert request.headers["x-api-key"] == "td_secret"
    assert request.read() == b'{"label":"order-123"}'
    assert wallet.address == "0xabc"


def test_authenticated_endpoint_requires_api_key() -> None:
    with pytest.raises(TronDealerAuthenticationError):
        TronDealerClient().assign_wallet("order-123")


def test_get_wallet_balance_parses_response(httpx_mock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/wallets/balance",
        json={
            "success": True,
            "balances": {"bsc": {"native": "0.0", "usdt": "1.0", "usdc": "0.0"}},
        },
    )

    balance = TronDealerClient(api_key="td_secret").get_wallet_balance("0xabc")

    assert balance.balances.root["bsc"].usdt == "1.0"


def test_list_wallet_transactions_sends_filters(httpx_mock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/wallets/transactions",
        json={
            "success": True,
            "total": 1,
            "limit": 20,
            "offset": 0,
            "transactions": [{"tx_hash": "0xabc", "amount": "10", "status": "confirmed"}],
        },
    )

    response = TronDealerClient(api_key="td_secret").list_wallet_transactions(
        address="0xabc",
        status="confirmed",
        limit=20,
        offset=0,
    )

    request = httpx_mock.get_request()
    assert request is not None
    assert request.read() == b'{"address":"0xabc","status":"confirmed","limit":20,"offset":0}'
    assert response.transactions[0].tx_hash == "0xabc"


def test_maps_validation_error(httpx_mock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/wallets/balance",
        status_code=400,
        json={"error": "address is required"},
        headers={"x-request-id": "req_123"},
    )

    with pytest.raises(TronDealerValidationError) as exc_info:
        TronDealerClient(api_key="td_secret").get_wallet_balance("")

    assert exc_info.value.status_code == 400
    assert exc_info.value.request_id == "req_123"
    assert exc_info.value.response_body == {"error": "address is required"}


def test_maps_rate_limit_error(httpx_mock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/clients/register-public",
        status_code=429,
        json={"error": "Rate limit exceeded"},
    )

    with pytest.raises(TronDealerRateLimitError):
        TronDealerClient().register_client_public(name="My Shop")


def test_invalid_json_response_raises_api_error(httpx_mock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/wallets/balance",
        status_code=200,
        content=b"not-json",
        headers={"x-request-id": "req_json"},
    )

    with pytest.raises(TronDealerAPIError) as exc_info:
        TronDealerClient(api_key="td_secret").get_wallet_balance("0xabc")

    assert exc_info.value.status_code == 200
    assert exc_info.value.response_body == "not-json"
    assert exc_info.value.request_id == "req_json"


def test_non_object_json_response_raises_api_error(httpx_mock) -> None:
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/wallets/balance",
        status_code=200,
        json=[],
    )

    with pytest.raises(TronDealerAPIError) as exc_info:
        TronDealerClient(api_key="td_secret").get_wallet_balance("0xabc")

    assert exc_info.value.response_body == []


def test_retries_transient_http_errors(httpx_mock, monkeypatch) -> None:
    sleeps = []
    httpx_mock.add_response(method="POST", url=f"{BASE_URL}/wallets/balance", status_code=503)
    httpx_mock.add_response(
        method="POST",
        url=f"{BASE_URL}/wallets/balance",
        json={"success": True, "balances": {}},
    )
    monkeypatch.setattr("trondealer.client.time.sleep", sleeps.append)

    balance = TronDealerClient(api_key="td_secret").get_wallet_balance("0xabc")

    assert balance.success is True
    assert len(httpx_mock.get_requests()) == 2
    assert sleeps == [0.5]


def test_retries_network_errors_and_preserves_cause(monkeypatch) -> None:
    request = httpx.Request("POST", f"{BASE_URL}/wallets/balance")
    transport = httpx.MockTransport(
        lambda _request: (_ for _ in ()).throw(httpx.ConnectError("boom", request=request))
    )
    client = httpx.Client(transport=transport)
    sleeps = []
    monkeypatch.setattr("trondealer.client.time.sleep", sleeps.append)

    with pytest.raises(TronDealerNetworkError) as exc_info:
        TronDealerClient(api_key="td_secret", max_retries=1, http_client=client).get_wallet_balance(
            "0xabc"
        )

    assert isinstance(exc_info.value.__cause__, httpx.ConnectError)
    assert sleeps == [0.5]
