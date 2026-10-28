PYTHON ?= python3
VENV ?= .venv
RUN = $(VENV)/bin

.PHONY: dev lint format test check build demo

dev:
	$(PYTHON) -m venv $(VENV)
	$(RUN)/python -m pip install -e '.[dev]'

lint:
	$(RUN)/ruff check src tests scripts
	$(RUN)/ruff format --check src tests scripts

format:
	$(RUN)/ruff format src tests scripts

test:
	$(RUN)/python -m pytest --cov=truemsg --cov-report=term-missing --cov-report=json --cov-fail-under=70

check: lint test

build:
	$(RUN)/python -m build

demo:
	$(RUN)/python scripts/demo.py
