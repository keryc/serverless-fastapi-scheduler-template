# serverless-fastapi-scheduler-template

FastAPI on **AWS Lambda** using **Serverless Framework v4**, with:
- **HTTP API** via API Gateway + **Mangum**
- **EventBridge Rule (UTC)** scheduling
- **Stage-based deployment** (dev/prod) with optimized packaging
- Tests (pytest + httpx), typing, linting
- CI/CD with GitHub Actions
- Function-level DLQs (SQS) via `AWS::Lambda::EventInvokeConfig`

## Architecture

```
API Gateway (HTTP API) → Lambda (Mangum → FastAPI)

EventBridge Rule (UTC) ───► Lambda: nightlyCleanupUtc
                          └► Lambda: syncThingsUtc
```

## Directory Structure
```
serverless-fastapi-scheduler-template/
├─ serverless.yml
├─ pyproject.toml             # Project configuration & dependencies
├─ uv.lock                    # Locked dependencies (auto-generated)
├─ Makefile                   # Development shortcuts
├─ README.md
├─ .env.example
├─ .python-version
├─ package.json
├─ src/
│  ├─ app/...
│  ├─ handlers/...
│  └─ tasks/...
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
```

## Configuration & Secrets
- `STAGE`, `API_BASE_PATH`, `ROOT_PATH`
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
