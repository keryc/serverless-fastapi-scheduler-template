# serverless-fastapi-scheduler-template

FastAPI on **AWS Lambda** using **Serverless Framework v4**, with:
- **HTTP API** via API Gateway + **Mangum**
- **EventBridge Rule (UTC)** scheduling
- **Offline emulation** with `serverless-offline`
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
├─ pyproject.toml
├─ README.md
├─ .env.example
├─ Makefile
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
- Node.js 18+
- AWS credentials with permissions

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]" & npm install
```

## Offline Emulation (serverless-offline)
Run API + scheduled functions locally with **serverless-offline**.

### Start
```bash
sls offline start
```

### Pause automatic schedules
Schedules use:
```yaml
enabled: ${env:ENABLE_SCHEDULES, 'true'}
```
Disable them locally:
```bash
ENABLE_SCHEDULES=false sls offline start
```

### Manual triggers
```bash
sls invoke local -f nightlyCleanupUtc
sls invoke local -f syncThingsUtc
```

## Deploying
```bash
npm run sls -- deploy --stage dev
# teardown
npm run sls -- remove --stage dev
```

## Configuration & Secrets
- `STAGE`, `API_BASE_PATH`, `ROOT_PATH`, `ENABLE_SCHEDULES`
- Store secrets in **SSM Parameter Store** or **AWS Secrets Manager** and reference in `serverless.yml`.

## Testing & Quality
```bash
pytest
ruff check .
black --check .
mypy src
```

## CI/CD
- **CI**: lint, type-check, tests on push/PR to `main`
- **Deploy**: manual dispatch with `stage` and `region` inputs; set `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in repo secrets

## Contributing
Issues and PRs are welcome. Run `make lint`, `make typecheck`, `make test` before submitting.

## License
MIT
