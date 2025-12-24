.PHONY: install sync lint format typecheck test run deploy-dev deploy-prod remove-dev remove-prod info-dev info-prod invoke-research logs-research

install:
	@command -v uv >/dev/null 2>&1 || { echo "❌ uv is not installed. Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }
	uv sync
	npm install

sync:
	uv sync

lint:
	uv run ruff check .

lint-fix:
	uv run ruff check . --fix

format:
	uv run black .

format-check:
	uv run black --check .

typecheck:
	uv run mypy src

test:
	uv run pytest

test-v:
	uv run pytest -v

run:
	uv run uvicorn src.app.main:app --reload

deploy-dev:
	uv export --no-dev --no-emit-project --frozen > requirements.txt
	npm run deploy:dev

deploy-prod:
	uv export --no-dev --no-emit-project --frozen > requirements.txt
	npm run deploy:prod

remove-dev:
	npm run remove:dev

remove-prod:
	npm run remove:prod

info-dev:
	npm run info:dev

info-prod:
	npm run info:prod

logs-api-dev:
	npm run logs:api:dev

logs-api-prod:
	npm run logs:api:prod

clean:
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf **/__pycache__
	rm -rf .serverless
	sls requirements cleanCache

full-clean:
	rm -rf .venv
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf **/__pycache__
	rm -rf .serverless
	sls requirements cleanCache
