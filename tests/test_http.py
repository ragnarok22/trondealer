from __future__ import annotations

import httpx

from trondealer._http import api_error, build_url, error_message, request_id
from trondealer.exceptions import (
    TronDealerAPIError,
    TronDealerAuthenticationError,
    TronDealerNotFoundError,
    TronDealerRateLimitError,
)
from trondealer.types import TransactionStatus


def response(
    status_code: int, *, json=None, content: bytes | None = None, headers=None
) -> httpx.Response:
    return httpx.Response(
        status_code,
        json=json,
        content=content,
        headers=headers,
        request=httpx.Request("POST", "https://example.test"),
    )


def test_build_url_accepts_endpoint_without_leading_slash() -> None:
    assert build_url("https://example.test/api/", "wallets/assign") == (
        "https://example.test/api/wallets/assign"
    )


def test_request_id_accepts_request_id_header_alias() -> None:
    assert request_id(response(400, json={}, headers={"request-id": "req_alias"})) == "req_alias"


def test_error_message_falls_back_to_message_field_and_non_dict_body() -> None:
    assert error_message({"message": "bad request"}) == "bad request"
    assert error_message("plain error") == "plain error"
    assert error_message({}) is None


def test_api_error_maps_authentication_not_found_rate_limit_and_server_errors() -> None:
    assert isinstance(
        api_error(response(401, json={"error": "invalid key"})), TronDealerAuthenticationError
    )
    assert isinstance(
        api_error(response(403, json={"error": "inactive"})), TronDealerAuthenticationError
    )
    assert isinstance(api_error(response(404, json={"error": "missing"})), TronDealerNotFoundError)
    assert isinstance(
        api_error(response(429, json={"error": "slow down"})), TronDealerRateLimitError
    )
    assert isinstance(api_error(response(500, json={})), TronDealerAPIError)


def test_api_error_uses_text_body_when_error_response_is_not_json() -> None:
    error = api_error(response(500, content=b"server exploded"))

    assert isinstance(error, TronDealerAPIError)
    assert error.message == "server exploded"
    assert error.response_body == "server exploded"


def test_api_error_str_includes_status_code_and_request_id() -> None:
    error = TronDealerAPIError("boom", status_code=500, request_id="req_123")

    assert str(error) == "boom (status_code=500, request_id=req_123)"
    assert str(TronDealerAPIError("boom")) == "boom"


def test_string_enums_render_as_values() -> None:
    assert str(TransactionStatus.CONFIRMED) == "confirmed"
