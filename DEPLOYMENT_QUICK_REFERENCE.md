# 🚀 Quick Deployment Reference

**Purpose**: Quick command reference for common deployment operations  
**Date**: February 24, 2026

---

## Local Development

```bash
# Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env

# Run API
uvicorn API.main:app --reload

# Run tests
pytest -v
pytest test_api_auth.py

# View API docs
# Open: http://localhost:8000/docs
```

---

## Heroku Deployment

```bash
# First time setup
heroku login
heroku create genivra-api
git push heroku main

# Configure environment
heroku config:set ENVIRONMENT=production -a genivra-api
heroku config:set TIER_1_MONTHLY_LIMIT=100 -a genivra-api
heroku config:set API_KEYS_OVERRIDE="key:tier:name" -a genivra-api

# View logs
heroku logs --tail -a genivra-api

# Rollback
heroku releases -a genivra-api
heroku releases:rollback v50 -a genivra-api

# Scale
heroku ps:scale web=2 -a genivra-api
```

---

## Docker

```bash
# Build
docker build -t genivra-api:latest .

# Run locally
docker run -p 8000:8000 \
  -e ENVIRONMENT=production \
  genivra-api:latest

# Push to registry
docker tag genivra-api:latest myregistry/genivra-api:latest
docker push myregistry/genivra-api:latest

# Compose (with database)
docker-compose up -d
docker-compose logs -f api
docker-compose down
```

---

## Testing Deployment

```bash
# Health check
curl -X GET https://api.yourdomain.com/health

# Test API key auth
curl -X POST https://api.yourdomain.com/predict \
  -H "x-api-key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "age_mean": 75,
    "baseline_mmse": 20,
    "apoe_e4_carrier": true,
    "ptau217_high": true,
    "trial_sample_size": 500,
    "trial_duration_weeks": 52,
    "endpoint_type": "objective",
    "primary_endpoint_name": "CDR-SB"
  }'

# Test missing API key
curl -X POST https://api.yourdomain.com/predict \
  -H "Content-Type: application/json" \
  -d '{...}'
# Expected: 401 error
```

---

## Database (PostgreSQL)

```bash
# Start local database
docker-compose up -d db

# Connect to database
psql -U genivra -d genivra -h localhost

# Common queries
SELECT COUNT(*) FROM api_keys;
SELECT * FROM usage_logs WHERE created_at > NOW() - INTERVAL '1 day';

# Backup
pg_dump -U genivra genivra > backup.sql

# Restore
psql -U genivra genivra < backup.sql
```

---

## Monitoring & Logs

```bash
# Heroku logs
heroku logs --tail -a genivra-api

# Docker logs
docker logs -f container_name

# Local logs (if file configured)
tail -f logs/predictions.log

# Check metrics
curl -X GET https://api.yourdomain.com/admin/api-keys/usage/KEY_NAME \
  -H "x-api-key: YOUR_KEY"
```

---

## Environment Variables

```bash
# Essential for production
ENVIRONMENT=production
PORT=8000
LOG_LEVEL=INFO
REQUIRE_HTTPS=true

# API configuration
TIER_1_MONTHLY_LIMIT=100
API_KEYS_OVERRIDE="key:tier:name"
CORS_ALLOWED_ORIGINS="https://yourdomain.com"

# Set on Heroku
heroku config:set VAR_NAME=value -a genivra-api

# Set on Docker
docker run -e VAR_NAME=value genivra-api:latest

# Set on deployment platform UI
# Usually under "Settings" or "Configuration"
```

---

## Common Issues

### 401 Unauthorized
```bash
# Ensure x-api-key header is present
curl -X GET https://api.yourdomain.com/health \
  -H "x-api-key: YOUR_KEY"

# Check key exists
curl -X GET https://api.yourdomain.com/admin/api-keys/list \
  -H "x-api-key: ADMIN_KEY"
```

### 429 Too Many Requests
```bash
# Check usage
curl -X GET https://api.yourdomain.com/admin/api-keys/usage/KEY_NAME \
  -H "x-api-key: YOUR_KEY"

# Use Tier 2 key (unlimited) or wait until next month
```

### API Not Starting
```bash
# Check logs for error message
heroku logs -a genivra-api

# Verify environment variables
heroku config -a genivra-api

# Test locally first
python -m uvicorn API.main:app
```

### CORS Errors
```bash
# Check allowed origins
echo $CORS_ALLOWED_ORIGINS

# Test CORS headers
curl -i -X OPTIONS https://api.yourdomain.com/predict \
  -H "Origin: https://yourdomain.com" \
  -H "Access-Control-Request-Method: POST"

# Update if needed
heroku config:set CORS_ALLOWED_ORIGINS="https://yourdomain.com,..." -a genivra-api
```

---

## Performance Tuning

```bash
# Scale horizontally (more instances)
heroku ps:scale web=3 -a genivra-api

# Scale vertically (larger dyno)
heroku dyno:resize standard-1x -a genivra-api

# Monitor performance
watch -n 5 "heroku ps -a genivra-api"
watch -n 5 "docker stats"
```

---

## Version Management

```bash
# Create release tag
git tag v1.0.0
git push origin v1.0.0

# Deploy specific version
git push heroku v1.0.0:main
docker tag genivra-api:v1.0.0
docker push myregistry/genivra-api:v1.0.0

# Check deployed version
curl https://api.yourdomain.com/docs | grep -i version
```

---

## Useful Commands

```bash
# List all environment variables
heroku config -a genivra-api

# Restart application
heroku restart -a genivra-api

# Open app in browser
heroku open -a genivra-api

# View app info
heroku apps:info genivra-api

# Connect to remote shell
heroku run bash -a genivra-api
```

---

## Links & Resources

- Full guide: See [DEPLOYMENT.md](DEPLOYMENT.md)
- Infrastructure checklist: See [DEPLOYMENT_INFRASTRUCTURE_CHECKLIST.md](DEPLOYMENT_INFRASTRUCTURE_CHECKLIST.md)
- API documentation: `/docs` endpoint
- GitHub: https://github.com/AMatelis/Genivra.ai

---

## Quick Deployment Steps

**5-Minute Deployment to Heroku**:

```bash
# 1. Build and test locally
pytest -v
python -m uvicorn API.main:app &

# 2. Create Heroku app
heroku create genivra-api

# 3. Set environment
heroku config:set ENVIRONMENT=production API_KEYS_OVERRIDE="key:tier:name"

# 4. Deploy
git push heroku main

# 5. Verify
curl https://genivra-api.herokuapp.com/health \
  -H "x-api-key: your_key"
```

---

*Last Updated: February 24, 2026*
