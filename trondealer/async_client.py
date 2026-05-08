"""Asynchronous TronDealer API client."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from ._http import (
    DEFAULT_BASE_URL,
    DEFAULT_REGISTRATION_ENDPOINT,
    TRANSIENT_STATUS_CODES,
    api_error,
    build_headers,
    build_url,
    parse_json_response,
)
from .exceptions import (
    TronDealerAuthenticationError,
    TronDealerNetworkError,
)
from .models import (
    AssignedWallet,
    AssignedWalletResponse,
    ClientRegistrationRequest,
    ClientRegistrationResponse,
    TransactionListResponse,
    WalletBalance,
)
from .types import PayoutMethod, TransactionStatus


class AsyncTronDealerClient:
    """Async client for the documented TronDealer V2 API."""

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float | httpx.Timeout = 10.0,
        max_retries: int = 2,
        registration_endpoint: str = DEFAULT_REGISTRATION_ENDPOINT,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max(0, max_retries)
        # TODO: Verify /clients/register-public directly with the live API or
        # TronDealer maintainers before publishing a stable v1.0 release. The
        # integration guide documents this path, while embedded OpenAPI docs may
        # list /clients/register-open for the same public operation.
        self.registration_endpoint = registration_endpoint
        self._client = http_client or httpx.AsyncClient(
            timeout=timeout,
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )
        self._owns_client = http_client is None

    async def __aenter__(self) -> AsyncTronDealerClient:
        return self

    async def __aexit__(self, *_exc_info: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def register_client_public(
        self,
        *,
        name: str,
        webhook_url: str | None = None,
        webhook_secret: str | None = None,
        min_confirmations: int | None = None,
        sweep_wallet: str | None = None,
        payout_method: PayoutMethod | str | None = None,
        turnstile_token: str | None = None,
    ) -> ClientRegistrationResponse:
        request = ClientRegistrationRequest(
            name=name,
            webhook_url=webhook_url,
            webhook_secret=webhook_secret,
            min_confirmations=min_confirmations,
            sweep_wallet=sweep_wallet,
            payout_method=payout_method,
            turnstile_token=turnstile_token,
        )
        data = await self._request(
            "POST",
            self.registration_endpoint,
            json=request.model_dump(mode="json", exclude_none=True),
            auth_required=False,
            retry=False,
        )
        return ClientRegistrationResponse.model_validate(data)

    async def assign_wallet(self, label: str) -> AssignedWallet:
        data = await self._request(
            "POST",
            "/wallets/assign",
            json={"label": label},
            auth_required=True,
            retry=True,
        )
        return AssignedWalletResponse.model_validate(data).wallet

    async def get_wallet_balance(self, address: str) -> WalletBalance:
        data = await self._request(
            "POST",
            "/wallets/balance",
            json={"address": address},
            auth_required=True,
            retry=True,
        )
        return WalletBalance.model_validate(data)

    async def list_wallet_transactions(
        self,
        *,
        address: str,
        status: TransactionStatus | str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> TransactionListResponse:
        payload: dict[str, Any] = {"address": address}
        if status is not None:
            payload["status"] = str(status)
        if limit is not None:
            payload["limit"] = limit
        if offset is not None:
            payload["offset"] = offset

        data = await self._request(
            "POST",
            "/wallets/transactions",
            json=payload,
            auth_required=True,
            retry=True,
        )
        return TransactionListResponse.model_validate(data)

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        json: dict[str, Any] | None = None,
        auth_required: bool,
        retry: bool,
    ) -> dict[str, Any]:
        if auth_required and not self.api_key:
            raise TronDealerAuthenticationError("An api_key is required for this endpoint")

        headers = build_headers(self.api_key, auth_required=auth_required)

        attempts = self.max_retries + 1 if retry else 1
        last_network_error: Exception | None = None

        for attempt in range(attempts):
            try:
                response = await self._client.request(
                    method,
                    build_url(self.base_url, endpoint),
                    json=json,
                    headers=headers,
                )
            except (httpx.ConnectError, httpx.TimeoutException, httpx.NetworkError) as exc:
                last_network_error = exc
                if attempt < attempts - 1:
                    await self._sleep_before_retry(attempt)
                    continue
                raise TronDealerNetworkError("Network error while calling TronDealer") from exc

            if response.status_code in TRANSIENT_STATUS_CODES and attempt < attempts - 1:
                await self._sleep_before_retry(attempt)
                continue

            if response.is_error:
                raise api_error(response)

            return parse_json_response(response)

        raise TronDealerNetworkError(
            "Network error while calling TronDealer"
        ) from last_network_error

    async def _sleep_before_retry(self, attempt: int) -> None:
        await asyncio.sleep(min(0.5 * (2**attempt), 5.0))
