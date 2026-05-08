"""Shared HTTP helpers for sync and async clients."""

from __future__ import annotations

from typing import Any, TypeVar

import httpx
from pydantic import BaseModel, ValidationError

from .exceptions import (
    TronDealerAPIError,
    TronDealerAuthenticationError,
    TronDealerNotFoundError,
    TronDealerRateLimitError,
    TronDealerValidationError,
)

DEFAULT_BASE_URL = "https://www.trondealer.com/api/v2"
DEFAULT_REGISTRATION_ENDPOINT = "/clients/register-public"
TRANSIENT_STATUS_CODES = {429, 500, 502, 503, 504}

ModelT = TypeVar("ModelT", bound=BaseModel)


def build_url(base_url: str, endpoint: str) -> str:
    normalized = endpoint if endpoint.startswith("/") else f"/{endpoint}"
    return f"{base_url.rstrip('/')}{normalized}"


def build_headers(api_key: str | None, *, auth_required: bool) -> dict[str, str]:
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if auth_required and api_key:
        headers["x-api-key"] = api_key
    return headers


def parse_json_response(response: httpx.Response) -> dict[str, Any]:
    try:
        payload = response.json()
    except ValueError as exc:
        raise TronDealerAPIError(
            "TronDealer returned invalid JSON",
            status_code=response.status_code,
            response_body=response.text,
            request_id=request_id(response),
        ) from exc

    if not isinstance(payload, dict):
        raise TronDealerAPIError(
            "TronDealer returned an unexpected JSON payload",
            status_code=response.status_code,
            response_body=payload,
            request_id=request_id(response),
        )

    return payload


def validate_response_model(model: type[ModelT], payload: dict[str, Any]) -> ModelT:
    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise TronDealerAPIError(
            "TronDealer returned an unexpected JSON payload",
            response_body=payload,
        ) from exc


def api_error(response: httpx.Response) -> TronDealerAPIError:
    body: Any
    try:
        body = response.json()
    except ValueError:
        body = response.text

    message = error_message(body) or f"TronDealer API error: HTTP {response.status_code}"
    kwargs = {
        "status_code": response.status_code,
        "response_body": body,
        "request_id": request_id(response),
    }

    if response.status_code == 400:
        return TronDealerValidationError(message, **kwargs)
    if response.status_code in {401, 403}:
        return TronDealerAuthenticationError(message, **kwargs)
    if response.status_code == 404:
        return TronDealerNotFoundError(message, **kwargs)
    if response.status_code == 429:
        return TronDealerRateLimitError(message, **kwargs)
    return TronDealerAPIError(message, **kwargs)


def error_message(body: Any) -> str | None:
    if isinstance(body, dict):
        error = body.get("error") or body.get("message")
        return str(error) if error else None
    return str(body) if body else None


def request_id(response: httpx.Response) -> str | None:
    return response.headers.get("x-request-id") or response.headers.get("request-id")
