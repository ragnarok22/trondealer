# AGENTS.md

## Project Facts

- This is a publishable Python SDK package named `trondealer`, not an app; public code lives in `trondealer/`, tests in `tests/`, and usage samples in `examples/`.
- Package support is Python `>=3.10`; CI tests `3.10`, `3.11`, `3.12`, and `3.13`.
- Local `.python-version` is `3.12`; avoid Python `3.14` for verification because it previously broke the current Pydantic stack.

## Commands

- Prefer Make targets; they run through `uv run --extra dev` and do not rely on globally installed tools.
- `make test` runs pytest.
- `make test:coverage` runs pytest with coverage for `trondealer`.
- `make lint` runs `ruff check .`.
- `make format` runs `ruff format .`.
- `make format:check` runs `ruff format --check .`.
- If invoking tools directly, use `uv run --extra dev <tool>` or run `uv sync --extra dev` first.

## SDK-Specific Gotchas

- `register_client_public(...)` must default to `/clients/register-public`; do not silently switch to `/clients/register-open` unless live API testing proves the guide endpoint is wrong.
- Keep the TODO near `registration_endpoint`: verify `/clients/register-public` with TronDealer before stable v1.0.
- Webhook verification must use the raw request body and `hmac.compare_digest`; support both raw hex and `sha256=<hex>` signatures because docs disagree.
- Response models intentionally allow extra fields; do not tighten them unless the public API is versioned and verified.
- Balance parsing intentionally accepts both guide-style per-network balances and OpenAPI-style flat balances.

## Release Workflow

- Publishing is triggered only by tags matching `v*.*.*` via `.github/workflows/publish.yml`.
- Publish workflow uses PyPI trusted publishing (`id-token: write`) and environment `pypi`.
- CI uses pip, while Make/local workflow uses uv; keep both paths working.
