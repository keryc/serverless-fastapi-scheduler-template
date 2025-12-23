# Migration Guide: v0.3.0 → v0.4.0

## Summary of Changes

This migration removes dependency management complexity and optimizes for AWS Lambda deployment size.

### Key Changes:
1. **Removed** `serverless-python-requirements` plugin (Serverless Framework v4 has built-in Python support)
2. **Removed** `serverless-offline` plugin (simplified to cloud-first deployment)
3. **Switched** from `pyproject.toml` to `requirements.txt` for dependency management
4. **Changed** `package.individually: true` → `false` to reduce duplication
5. **Added** stage-based configuration (dev/prod)

## Migration Steps

### 1. Clean Up Old Dependencies
```bash
# Remove old node_modules
rm -rf node_modules package-lock.json

# Remove old Python cache
rm -rf .venv .mypy_cache .pytest_cache .ruff_cache

# Remove Serverless artifacts
rm -rf .serverless
```

### 2. Reinstall Dependencies
```bash
# Create fresh virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements-dev.txt

# Install Node dependencies
npm install
```

### 3. Deploy to Dev Stage
```bash
# Deploy to development stage first to test
npm run deploy:dev
# or
make deploy-dev
```

### 4. Test the Deployment
```bash
# Get deployment information
npm run info:dev

# Test your API endpoint
curl https://YOUR_API_ENDPOINT/health

# View logs
npm run logs:api:dev
```

### 5. Deploy to Production (when ready)
```bash
npm run deploy:prod
# or
make deploy-prod
```

## What Changed in Configuration

### serverless.yml
- **Removed**: `plugins` section (no longer needed)
- **Removed**: `custom.pythonRequirements` section
- **Removed**: `custom.serverless-offline` section
- **Changed**: `package.individually: true` → `false`
- **Added**: `custom.stages` for stage-specific configuration
- **Added**: More exclusion patterns in `package.patterns`
- **Removed**: Function-level `package.patterns` (now using global)

### package.json
- **Removed**: `serverless-offline` dependency
- **Removed**: `serverless-python-requirements` dependency
- **Added**: NPM scripts for common operations

### Dependency Management
- **Before**: `pyproject.toml` with `[project.dependencies]`
- **After**: `requirements.txt` and `requirements-dev.txt`
- **Note**: `pyproject.toml` kept only for tool configurations (ruff, black, mypy, pytest)

## Stage Configuration

### Development (dev)
- Memory: 512MB
- Log Retention: 7 days
- Schedules: **Disabled** (won't trigger automatically)

### Production (prod)
- Memory: 1024MB
- Log Retention: 30 days
- Schedules: **Enabled** (will trigger on schedule)

## Benefits of This Migration

1. **Smaller Lambda Packages**: `individually: false` reduces duplication
2. **Faster Deployments**: Simpler packaging, no extra plugins
3. **More Reliable**: Direct `requirements.txt` support, no conversion issues
4. **Better Staging**: Clear separation between dev and prod environments
5. **Cleaner Dependencies**: Removed archived plugins

## Rollback Instructions

If you need to rollback to v0.3.0:

```bash
git checkout v0.3.0
rm -rf node_modules .venv
pip install -e ".[dev]"
npm install
```

## Troubleshooting

### Issue: "Module not found" errors
**Solution**: Make sure you've reinstalled Python dependencies:
```bash
pip install -r requirements-dev.txt
```

### Issue: Deployment package too large
**Solution**: The new configuration should fix this. If still too large:
1. Check `requirements.txt` for unnecessary dependencies
2. Ensure `.venv/` is excluded in `package.patterns`

### Issue: Schedules not working in dev
**Solution**: This is intentional. Schedules are disabled in dev stage. Use prod stage or manually invoke:
```bash
serverless invoke --function nightlyCleanupUtc --stage dev
```

## Need Help?

Open an issue at: https://github.com/your-org/serverless-fastapi-scheduler-template/issues
