"""Exception types raised by the TronDealer SDK."""

from __future__ import annotations

from typing import Any


class TronDealerError(Exception):
    """Base class for all SDK errors."""


class TronDealerAPIError(TronDealerError):
    """Raised when TronDealer returns a non-successful HTTP response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_body: Any | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body
        self.request_id = request_id

    def __str__(self) -> str:
        details = []
        if self.status_code is not None:
            details.append(f"status_code={self.status_code}")
        if self.request_id:
            details.append(f"request_id={self.request_id}")
        return f"{self.message} ({', '.join(details)})" if details else self.message


class TronDealerAuthenticationError(TronDealerAPIError):
    """Raised for missing, invalid, or unauthorized API credentials."""


class TronDealerRateLimitError(TronDealerAPIError):
    """Raised when the API rate limits a request."""


class TronDealerValidationError(TronDealerAPIError):
    """Raised when the API rejects request parameters."""


class TronDealerNotFoundError(TronDealerAPIError):
    """Raised when a requested resource does not exist or is not accessible."""


class TronDealerNetworkError(TronDealerError):
    """Raised for network, connection, and timeout failures."""
