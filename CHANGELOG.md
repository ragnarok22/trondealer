# Changelog

## 0.1.1

- Fixed successful API responses with unexpected shapes to raise `TronDealerAPIError` instead of leaking raw Pydantic validation errors.
- Added typed webhook transaction index fields for safer idempotency handling.
- Improved SDK tests around response validation, context-manager cleanup, webhook parsing, and async network errors.

## 0.1.0

- Initial Python SDK package.
- Added synchronous and asynchronous TronDealer clients.
- Added public registration, wallet assignment, wallet balance, and transaction listing methods.
- Added Pydantic v2 models and custom exception hierarchy.
- Added HMAC webhook verification and parsing helpers.
- Added examples, tests, and package metadata.
