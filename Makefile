.PHONY: install sync lint lint-fix format format-check typecheck test test-v run \
        check verify deploy-dev deploy-prod remove-dev remove-prod info-dev info-prod \
        invoke invoke-nightly-dev invoke-sync-dev logs logs-api-dev logs-api-prod clean

# Shared variables for the invoke/logs targets.
#   STAGE  dev | prod                     (default: dev)
#   TASK   api or any id in TASK_MAP      (default: api)
#
# SERVICE is read from serverless.yml so renaming the service in one place is
# enough. TASK_MAP is the single place mapping a task id to its function name;
# add one entry per task and both `invoke` and `logs` pick it up.
SERVICE := $(shell sed -n 's/^service:[[:space:]]*//p' serverless.yml | head -1)
TASK_MAP := nightly-cleanup:nightlyCleanupUtc sync-things:syncThingsUtc

STAGE ?= dev
TASK ?= api
PAYLOAD ?= {}

LAMBDA_PREFIX = $(SERVICE)-$(STAGE)
TASK_IDS = $(foreach e,$(TASK_MAP),$(firstword $(subst :, ,$(e))))
# Function name for $(TASK); empty when TASK is not in TASK_MAP.
TASK_FUNCTION = $(strip $(foreach e,$(TASK_MAP),\
    $(if $(filter $(TASK),$(firstword $(subst :, ,$(e)))),$(lastword $(subst :, ,$(e))))))

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
# Async invocation: returns 202, read the outcome with `make logs TASK=...`.
invoke:
	@test -n "$(SERVICE)" || { echo "❌ Could not read 'service:' from serverless.yml"; exit 1; }
	@test -n "$(TASK_FUNCTION)" || { echo "❌ Unknown TASK '$(TASK)'. Options: $(TASK_IDS)"; exit 1; }
	aws lambda invoke --no-cli-pager --function-name $(LAMBDA_PREFIX)-$(TASK_FUNCTION) \
		--invocation-type Event --cli-binary-format raw-in-base64-out \
		--payload '$(PAYLOAD)' /dev/null

invoke-nightly-dev:
	npx sls invoke -f nightlyCleanupUtc --stage dev

invoke-sync-dev:
	npx sls invoke -f syncThingsUtc --stage dev

# ==================== Logs ====================
# Usage: make logs TASK=api STAGE=dev
# TASK=api tails the HTTP function; any id in TASK_MAP tails that task.
logs:
	@test -n "$(SERVICE)" || { echo "❌ Could not read 'service:' from serverless.yml"; exit 1; }
	@test "$(TASK)" = "api" -o -n "$(TASK_FUNCTION)" || \
		{ echo "❌ Unknown TASK '$(TASK)'. Options: api $(TASK_IDS)"; exit 1; }
	aws logs tail /aws/lambda/$(LAMBDA_PREFIX)-$(if $(filter api,$(TASK)),api,$(TASK_FUNCTION)) --follow

logs-api-dev:
	npm run logs:api:dev

logs-api-prod:
	npm run logs:api:prod

# ==================== Cleanup ====================
clean:
	rm -rf .venv
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf **/__pycache__
	rm -rf .serverless
	sls requirements cleanCache
