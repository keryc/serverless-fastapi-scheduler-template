.PHONY: install lint format typecheck test run deploy remove offline

install:
	python -m pip install --upgrade pip
	pip install -e ".[dev]"
	npm ci

lint:
	ruff check .

format:
	black .

typecheck:
	mypy src

test:
	pytest -q

run:
	uvicorn src.app.main:app --reload
