.PHONY: install sync lint lint-fix format format-check typecheck test test-v run \
        check verify deploy-dev deploy-prod remove-dev remove-prod info-dev info-prod \
        invoke logs clean full-clean

# Shared variables for the invoke/logs targets.
#   STAGE  dev | prod                  (default: dev)
#   TASK   api | nightly-cleanup | sync-things
SERVICE := serverless-fastapi-scheduler-template
STAGE ?= dev
TASK ?= api

# ==================== Setup ====================

install:
	@command -v uv >/dev/null 2>&1 || { echo "❌ uv is not installed. Install it with: curl -LsSf https://astral.sh/uv/install.sh | sh"; exit 1; }
	uv sync --group dev --group test
	npm install

sync:
	uv sync --group dev --group test

# ==================== Quality ====================
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

# Full local gate: auto-fix first, then verify everything.
check: lint-fix format lint format-check typecheck test
	@echo "✅ lint, format, typecheck and tests passed"

# Same checks without touching files — what CI should run.
verify: lint format-check typecheck test
	@echo "✅ lint, format, typecheck and tests passed"

# ==================== Local Dev ====================
run:
	uv run uvicorn src.app.main:app --reload

# ==================== Deploy ====================
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

# ==================== Invoke tasks (async) ====================
# Usage:
#   make invoke TASK=nightly-cleanup
#   make invoke TASK=sync-things STAGE=prod PAYLOAD='{"region":"eu-west-1"}'
PAYLOAD ?= {}
LAMBDA_PREFIX := $(SERVICE)-$(STAGE)

invoke:
ifeq ($(TASK),nightly-cleanup)
	aws lambda invoke --no-cli-pager --function-name $(LAMBDA_PREFIX)-nightlyCleanupUtc \
		--invocation-type Event --cli-binary-format raw-in-base64-out \
		--payload '$(PAYLOAD)' /dev/null
else ifeq ($(TASK),sync-things)
	aws lambda invoke --no-cli-pager --function-name $(LAMBDA_PREFIX)-syncThingsUtc \
		--invocation-type Event --cli-binary-format raw-in-base64-out \
		--payload '$(PAYLOAD)' /dev/null
else
	@echo "Unknown TASK: $(TASK). Options: nightly-cleanup, sync-things"; exit 1
endif

# ==================== Logs ====================
# Usage: make logs TASK=api STAGE=dev
logs:
ifeq ($(TASK),api)
	aws logs tail /aws/lambda/$(LAMBDA_PREFIX)-api --follow
else ifeq ($(TASK),nightly-cleanup)
	aws logs tail /aws/lambda/$(LAMBDA_PREFIX)-nightlyCleanupUtc --follow
else ifeq ($(TASK),sync-things)
	aws logs tail /aws/lambda/$(LAMBDA_PREFIX)-syncThingsUtc --follow
else
	@echo "Unknown TASK: $(TASK). Options: api, nightly-cleanup, sync-things"; exit 1
endif

# ==================== Cleanup ====================
# clean: caches only. full-clean: also removes .venv and .serverless.
clean:
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf **/__pycache__

full-clean: clean
	rm -rf .venv
	rm -rf .serverless
	npx sls requirements cleanCache
