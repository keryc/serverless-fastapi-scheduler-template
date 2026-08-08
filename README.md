# serverless-fastapi-scheduler-template

FastAPI on **AWS Lambda** using **Serverless Framework v4**, with:
- **HTTP API** via API Gateway + **Mangum**
- **EventBridge Rule (UTC)** scheduling, declared in `events/*.yml`
- A **task registry**: one shared Lambda handler, tasks added as modules
- Built-in **retry with exponential backoff** on transient errors
- Optional **Bearer token auth** for protected endpoints
- **Stage-based deployment** (dev/prod) with optimized packaging
- Tests (pytest + httpx), typing, linting
- CI/CD with GitHub Actions
- Function-level DLQs (SQS) via `AWS::Lambda::EventInvokeConfig`

## Architecture

```
API Gateway (HTTP API) → Lambda (Mangum → FastAPI)

EventBridge Rule (UTC) ───► Lambda: nightlyCleanupUtc ─┐
                          └► Lambda: syncThingsUtc ────┴► task_handler
                                                          → TaskRegistry[TASK_ID]
                                                          → BaseTask.execute_safe()
```

Each function shares `src/handlers/task_handlers.task_handler`. The function's
`TASK_ID` environment variable selects the task from the registry, and each
schedule's `input:` payload arrives as `config.params`. Adding a task means
adding a module under `src/tasks/` and a file under `events/` — no new handler.

## Directory Structure
```
serverless-fastapi-scheduler-template/
├─ serverless.yml
├─ pyproject.toml             # Project configuration & dependencies
├─ uv.lock                    # Locked dependencies (auto-generated)
├─ Makefile                   # Development shortcuts
├─ README.md
├─ .env.example
├─ events/                    # EventBridge schedules, one file per task
├─ .python-version
├─ package.json               # Serverless Framework (pinned) + npm scripts
├─ package-lock.json
├─ requirements.txt           # Exported from uv.lock for the Lambda build
├─ src/
│  ├─ app/...
│  ├─ handlers/...            # task_handler (shared) + http_handler
│  └─ tasks/                  # base.py, registry.py + one module per task
├─ tests/...
└─ .github/workflows/...
```

## Requirements
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (modern Python package manager)
- Node.js 18+
- **Docker** — required to deploy: `serverless-python-requirements` builds the
  dependencies with `dockerizePip: true` so they match the Lambda runtime
- AWS credentials with permissions

## Quickstart
```bash
# Install dependencies
make install

# Configure the local environment
cp .env.example .env

# Run tests
make test

# Start local dev server  →  http://127.0.0.1:8000/docs
make run
```

## Endpoints

| Method | Path              | Auth   | Description                     |
|--------|-------------------|--------|---------------------------------|
| GET    | `/api/v1/health`  | public | Health check                    |
| GET    | `/api/v1/tasks`   | Bearer | List the registered tasks       |

```bash
curl localhost:8000/api/v1/health
curl -H "Authorization: Bearer $API_BEARER_TOKEN" localhost:8000/api/v1/tasks
```

Endpoints depending on `verify_token` return **401** on a missing or wrong
token, and **503** when `API_BEARER_TOKEN` is not configured at all.

## Deploying

### Development Stage
```bash
make deploy-dev
```

### Production Stage
```bash
make deploy-prod
```

### Stage-specific Configuration

| | Memory | API timeout | Task timeout | Log retention | Schedules |
|---|---|---|---|---|---|
| **dev**  | 512MB  | 29s | 300s | 7 days  | disabled |
| **prod** | 1024MB | 29s | 300s | 30 days | enabled  |

The API function stays at 29s because that is the API Gateway integration
limit; scheduled tasks get their own longer `taskTimeout`. All of it lives in
`custom.stages` in `serverless.yml`.

### Teardown
```bash
make remove-dev   # Remove dev stage
make remove-prod  # Remove prod stage
```

### View Deployment Info
```bash
make info-dev
make info-prod
```

### View Logs
```bash
make logs-api-dev
make logs-api-prod

# Or tail any function, including the scheduled tasks:
make logs TASK=api                      # STAGE defaults to dev
make logs TASK=sync-things STAGE=prod
```

### Invoke a Task Manually
```bash
make invoke TASK=nightly-cleanup
make invoke TASK=sync-things STAGE=prod PAYLOAD='{"region":"eu-west-1"}'
```

`PAYLOAD` is the same shape as a schedule's `input:`. These are async
(`--invocation-type Event`) invocations, so they return `202` and nothing else —
read the outcome with `make logs TASK=...`.

## Adding a Task

1. Create `src/tasks/my_task.py`:
   ```python
   from src.tasks.base import BaseTask, TaskConfig
   from src.tasks.registry import register_task

   @register_task("my-task")
   class MyTask(BaseTask):
       max_retries = 3  # optional

       async def run(self, config: TaskConfig):
           return f"done for {config.params.get('region')}"
   ```
2. Create `events/my-task.yml` with one or more `schedule` entries (each may
   carry a different `input:` payload).
3. Add the function to `serverless.yml`:
   ```yaml
   myTask:
     handler: src/handlers/task_handlers.task_handler
     timeout: ${self:custom.stages.${self:provider.stage}.taskTimeout}
     environment:
       TASK_ID: my-task
     events: ${file(./events/my-task.yml):events}
   ```
4. Add it to `TASK_MAP` in the `Makefile` so `make invoke`/`make logs` know it:
   ```make
   TASK_MAP := nightly-cleanup:nightlyCleanupUtc sync-things:syncThingsUtc my-task:myTask
   ```

Tasks are auto-discovered from `src/tasks/`, so there is no registration list to
update. `tests/integration/test_serverless_config.py` cross-checks all four
places and fails if they drift apart — a `TASK_ID` with no task, an unreferenced
`events/` file, or a stale `TASK_MAP`.

### Retries

`BaseTask.execute_safe()` retries only *transient* failures (HTTP 429/5xx,
timeouts, reset connections) with exponential backoff, then returns a
`TaskResult` instead of raising — so Lambda's own async retry and the DLQ stay
reserved for real crashes. Tune per call via `TaskConfig(max_retries=...,
base_delay_seconds=...)`, and keep the worst case below the function `timeout`.

## Configuration & Secrets
- `STAGE`, `API_BASE_PATH`, `ROOT_PATH`, `AWS_REGION`, `API_BEARER_TOKEN`
- Settings load from the environment and, locally, from a `.env` file (see `.env.example`)
- `API_BEARER_TOKEN` protects endpoints that depend on `verify_token`
  (`GET /api/v1/tasks` is the included example); when unset those endpoints return 503
- Schedules are managed per stage through `custom.stages.<stage>.schedulesEnabled`
  in `serverless.yml` (disabled in dev, enabled in prod), not through `.env`

### Secrets in production

`API_BEARER_TOKEN` is passed as a plain Lambda environment variable, readable by
anyone holding `lambda:GetFunctionConfiguration`. That is fine for dev; for prod
keep it in **SSM Parameter Store** (or Secrets Manager) and reference it from
`serverless.yml` instead:

```yaml
API_BEARER_TOKEN: ${ssm:/${self:service}/${self:provider.stage}/api-bearer-token}
```

Create it once with:

```bash
aws ssm put-parameter --name /<service>/prod/api-bearer-token \
  --type SecureString --value "$(openssl rand -hex 32)"
```

## Testing & Quality
```bash
# Everything at once: auto-fix, then lint, format check, mypy and tests
make check

# Same checks without modifying files (the same set CI runs)
make verify
```

Or one at a time:

```bash
make test          # pytest
make test-v        # pytest -v
make lint          # ruff check
make lint-fix      # ruff check --fix
make format        # black
make format-check  # black --check
make typecheck     # mypy src
```

All commands use `uv` under the hood. See `Makefile` for details.

## CI/CD
- **CI**: lint, format check, type check and tests on push/PR to `main`, against
  Python 3.11 and 3.12 — the same checks `make verify` runs locally
- **Deploy**: manual dispatch with `stage` and `region` inputs; set
  `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in repo secrets. It regenerates
  `requirements.txt` from `uv.lock` before deploying, same as the Makefile targets.

## Contributing
Issues and PRs are welcome. Run `make check` before submitting.

## License
MIT
