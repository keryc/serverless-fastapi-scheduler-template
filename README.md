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
├─ requirements.txt           # Production dependencies
├─ requirements-dev.txt       # Development dependencies
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
# Create virtual environment
python3 -m venv .venv && source .venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt
npm install
```

## Deploying

### Development Stage
```bash
npm run deploy:dev
# or
serverless deploy --stage dev
```

### Production Stage
```bash
npm run deploy:prod
# or
serverless deploy --stage prod
```

### Stage-specific Configuration
- **Dev**: 512MB memory, 7-day logs, schedules **disabled**
- **Prod**: 1024MB memory, 30-day logs, schedules **enabled**

### Teardown
```bash
npm run remove:dev   # Remove dev stage
npm run remove:prod  # Remove prod stage
```

### View Deployment Info
```bash
npm run info:dev
npm run info:prod
```

### View Logs
```bash
npm run logs:api:dev
npm run logs:api:prod
```

## Configuration & Secrets
- `STAGE`, `API_BASE_PATH`, `ROOT_PATH`
- Store secrets in **SSM Parameter Store** or **AWS Secrets Manager** and reference in `serverless.yml`
- Schedules are automatically managed per stage (disabled in dev, enabled in prod)

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
