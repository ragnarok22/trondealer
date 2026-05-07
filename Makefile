.PHONY: help test test\:coverage lint format format\:check

help:
	@printf "Available commands:\n"
	@printf "  make help             Show this help message\n"
	@printf "  make test             Run the test suite\n"
	@printf "  make test:coverage    Run tests with coverage\n"
	@printf "  make lint             Run ruff lint checks\n"
	@printf "  make format           Format code with ruff\n"
	@printf "  make format:check     Check code formatting\n"

test:
	python -m pytest

test\:coverage:
	python -m pytest --cov=trondealer --cov-report=term-missing

lint:
	python -m ruff check .

format:
	python -m ruff format .

format\:check:
	python -m ruff format --check .
