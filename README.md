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
├─ package.json
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
- AWS credentials with permissions

## Quickstart
```bash
# Install dependencies
make install

# Run tests
make test

# Start local dev server
make run
```


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
- **Dev**: 512MB memory, 7-day logs, schedules **disabled**
- **Prod**: 1024MB memory, 30-day logs, schedules **enabled**

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

Tasks are auto-discovered from `src/tasks/`, so no registration list to update.

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
- Store secrets in **SSM Parameter Store** or **AWS Secrets Manager** and reference in `serverless.yml`
- Schedules are automatically managed per stage (disabled in dev, enabled in prod)

## Testing & Quality
```bash
# Run tests
make test

# Lint code
make lint

# Auto-fix lint issues
make lint-fix

# Format code
make format

# Type check
make typecheck

# Run local dev server
make run
```

All commands use `uv` under the hood. See `Makefile` for details.

## CI/CD
- **CI**: lint, type-check, tests on push/PR to `main`
- **Deploy**: manual dispatch with `stage` and `region` inputs; set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in repo secrets

## Contributing
Issues and PRs are welcome. Run `make lint`, `make typecheck`, and `make test` before submitting.

## License
MIT
