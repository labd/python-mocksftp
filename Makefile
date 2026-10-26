.PHONY: install test retest coverage lint format


install:
	uv sync

test:
	uv run pytest

retest:
	uv run pytest -vvs --lf

coverage:
	uv run pytest --cov=mocksftp --cov-report=term-missing -p no:mocksftp

lint:
	uv run ruff format --check src tests
	uv run ruff check src tests

format:
	uv run ruff check --fix src tests
	uv run ruff format src tests
