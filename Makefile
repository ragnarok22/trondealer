.PHONY: help test test\:coverage lint format format\:check

UV ?= uv
UV_RUN = $(UV) run --extra dev

help:
	@printf "Available commands:\n"
	@printf "  make help             Show this help message\n"
	@printf "  make test             Run the test suite\n"
	@printf "  make test:coverage    Run tests with coverage\n"
	@printf "  make lint             Run ruff lint checks\n"
	@printf "  make format           Format code with ruff\n"
	@printf "  make format:check     Check code formatting\n"

test:
	$(UV_RUN) pytest

test\:coverage:
	$(UV_RUN) pytest --cov=trondealer --cov-report=term-missing

lint:
	$(UV_RUN) ruff check .

format:
	$(UV_RUN) ruff format .

format\:check:
	$(UV_RUN) ruff format --check .
