# 🚀 Deployment Guide - Genivra CNS Risk Engine API

**Status:** Production-Ready | **Version:** 1.0.0 | **Last Updated:** February 24, 2026

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Local Development](#local-development)
3. [Environment Configuration](#environment-configuration)
4. [Deployment Platforms](#deployment-platforms)
5. [API Key Management](#api-key-management)
6. [CORS Configuration](#cors-configuration)
7. [Monitoring & Logs](#monitoring--logs)
8. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Installation (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/AMatelis/Genivra.ai.git
cd Genivra.ai

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run API locally
uvicorn API.main:app --reload

# Open browser: http://localhost:8000/docs
```

### First Request (1 minute)

```bash
# Using demo API key (Tier 1 - 100/month limit)
curl -X POST http://localhost:8000/predict \
  -H "x-api-key: demo_tier1_key_12345" \
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
```

---

## 💻 Local Development

### Setup Development Environment

```bash
# Create and activate venv
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies with development tools
pip install -r requirements.txt

# Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install

# Create .env file from example
cp .env.example .env
```

### Run Development Server

```bash
# With auto-reload (watches file changes)
uvicorn API.main:app --host 127.0.0.1 --port 8000 --reload

# Server ready at:
# - API: http://127.0.0.1:8000
# - Docs: http://127.0.0.1:8000/docs
# - ReDoc: http://127.0.0.1:8000/redoc
```

### Run Tests

```bash
# Run all tests
pytest

# Run with output and coverage
pytest -v --cov=API --cov=Models

# Run specific test file
pytest test_api_auth.py -v

# Example output:
# ✓ PASS: Health check accessible without auth key
# ✓ PASS: Missing API key returns 401 Unauthorized
# ✓ PASS: Tier 1 key accepted (100/month limit)
# 8/8 tests PASSED ✓
```

### Web Dashboard (Local)

```bash
# Dashboard is in FrontEnd/index.html
# Open in browser: file:///path/to/Genivra.ai/FrontEnd/index.html

# Enter demo API key:
# demo_tier1_key_12345 (Tier 1: 100/month)
# demo_tier2_key_67890 (Tier 2: unlimited)

# Click Save, then make predictions
```

---

## ⚙️ Environment Configuration

### Using .env File

```bash
# Copy example to .env
cp .env.example .env

# Edit .env with your values
nano .env  # or your favorite editor

# File is automatically loaded by FastAPI/Pydantic
# Changes require server restart
```

### .env Format & Options

```env
# Environment
ENVIRONMENT=development
PORT=8000
HOST=127.0.0.1
LOG_LEVEL=INFO

# API Keys (override defaults if needed)
API_KEYS_OVERRIDE=prod_key1:tier_2:Client A,prod_key2:tier_1:Client B
TIER_1_MONTHLY_LIMIT=100
TIER_2_MONTHLY_LIMIT=0

# CORS (for web dashboard)
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
CORS_ALLOW_CREDENTIALS=true

# Models
MODEL_ARTIFACT_DIR=Models/artifacts
FEATURE_SCALER_PATH=Models/artifacts/feature_scaler.pkl
LOGISTIC_MODEL_PATH=Models/artifacts/logistic_model.pkl

# Security
REQUIRE_HTTPS=false
ENABLE_API_DOCS=true

# Deployment
DEPLOYMENT_PLATFORM=local
APP_NAME=Genivra CNS Risk Engine API
APP_VERSION=1.0.0
```

### Environment Variables (Alternative to .env)

```bash
# Set via shell environment
export ENVIRONMENT=production
export TIER_1_MONTHLY_LIMIT=500
export API_KEYS_OVERRIDE="prod_key1:tier_2:Company A"

# Then run server
uvicorn API.main:app --host 0.0.0.0 --port 8000
```

### Configuration Loading Priority

1. **Environment variables** (highest priority)
2. **.env file** (if exists and not overridden)
3. **Default values** in code (lowest priority)

---

## ☁️ Deployment Platforms

### Heroku Deployment (Recommended for quick start)

#### Step 1: Prepare Application

```bash
# Ensure Procfile exists (already included)
cat Procfile
# Expected output: web: uvicorn API.main:app --host=0.0.0.0 --port=${PORT:-8000}

# Ensure requirements.txt is up to date
pip freeze > requirements.txt
```

#### Step 2: Create Heroku App

```bash
# Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli

# Login to Heroku
heroku login

# Create new app
heroku create genivra-api
# or use existing app:
heroku apps:info  # list apps

# Set app name (for convenience)
HEROKU_APP=genivra-api
```

#### Step 3: Configure Environment

```bash
# Set production environment variables
heroku config:set ENVIRONMENT=production -a $HEROKU_APP
heroku config:set LOG_LEVEL=INFO -a $HEROKU_APP
heroku config:set REQUIRE_HTTPS=true -a $HEROKU_APP

# Set rate limits
heroku config:set TIER_1_MONTHLY_LIMIT=100 -a $HEROKU_APP
heroku config:set TIER_2_MONTHLY_LIMIT=0 -a $HEROKU_APP

# Set your production API keys (see API Key Management section)
heroku config:set API_KEYS_OVERRIDE="prod_key_001:tier_2:Pharma Corp,prod_key_002:tier_1:Lab A" -a $HEROKU_APP

# Allow CORS for dashboard
heroku config:set CORS_ALLOWED_ORIGINS="https://mycompany.com,https://dashboard.mycompany.com" -a $HEROKU_APP

# Verify configuration
heroku config -a $HEROKU_APP
```

#### Step 4: Deploy

```bash
# Deploy to Heroku
git push heroku main  # or master

# View logs
heroku logs --tail -a $HEROKU_APP

# Open app in browser
heroku open -a $HEROKU_APP

# Test API
curl -X GET https://<app-name>.herokuapp.com/health \
  -H "x-api-key: demo_tier1_key_12345"
```

#### Step 5: Monitor

```bash
# View logs
heroku logs -a $HEROKU_APP

# Monitor resources
heroku ps -a $HEROKU_APP

# Restart app (if needed)
heroku restart -a $HEROKU_APP

# Scale dynos (increase capacity)
heroku ps:scale web=2 -a $HEROKU_APP
```

---

### Railway Deployment (Modern alternative)

#### Step 1: Connect GitHub

```bash
# Push code to GitHub
git remote add origin https://github.com/yourusername/genivra-api.git
git push origin main
```

#### Step 2: Connect Railway

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub"
4. Choose your repository
5. Authorize Railway

#### Step 3: Configure

```bash
# Set environment variables in Railway dashboard:
# Variables → Add Variable

ENVIRONMENT=production
PORT=${PORT}  # Railway provides this
LOG_LEVEL=INFO
TIER_1_MONTHLY_LIMIT=100
API_KEYS_OVERRIDE="prod_key_001:tier_2:Pharma Corp"
CORS_ALLOWED_ORIGINS="https://yourdomain.com"
REQUIRE_HTTPS=true
```

#### Step 4: Deploy

- Railway auto-deploys on git push
- View logs in Dashboard
- Get public URL: https://<project-name>.railway.app

---

### Render Deployment (Another modern option)

```bash
# 1. Go to https://render.com
# 2. New → Web Service
# 3. Connect GitHub repository
# 4. Configuration:
#    - Name: genivra-api
#    - Environment: Python 3
#    - Build: pip install -r requirements.txt
#    - Start: uvicorn API.main:app --host 0.0.0.0 --port $PORT
# 5. Set Environment Variables (same as above)
# 6. Deploy
```

---

### Docker Deployment (Recommended for production)

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Set environment
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Run
CMD ["uvicorn", "API.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Deploy to Docker registry:

```bash
# Build image
docker build -t genivra-api:latest .

# Run locally
docker run -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e TIER_1_MONTHLY_LIMIT=100 \
  genivra-api:latest

# Push to Docker Hub
docker tag genivra-api:latest youruser/genivra-api:latest
docker push youruser/genivra-api:latest

# Deploy to cloud (AWS ECR, GCP GCR, Azure ACR, etc.)
```

---

### AWS Deployment (Elastic Beanstalk)

```bash
# 1. Install EB CLI
pip install awsebcli

# 2. Initialize EB
eb init -p python-3.10 genivra-api --region us-east-1

# 3. Create environment
eb create genivra-production

# 4. Set environment variables
eb setenv ENVIRONMENT=production TIER_1_MONTHLY_LIMIT=100

# 5. Deploy
eb deploy

# 6. View logs
eb logs

# 7. Open app
eb open
```

---

### GCP Deployment (Cloud Run)

```bash
# 1. Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/genivra-api

# 2. Deploy
gcloud run deploy genivra-api \
  --image gcr.io/PROJECT_ID/genivra-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars "ENVIRONMENT=production,TIER_1_MONTHLY_LIMIT=100"

# 3. Get URL
gcloud run services describe genivra-api --region us-central1 --format='value(status.url)'
```

---

### Azure Deployment (App Service)

```bash
# 1. Create resource group
az group create --name genivra-rg --location eastus

# 2. Create App Service plan
az appservice plan create \
  --name genivra-plan \
  --resource-group genivra-rg \
  --sku B1 \
  --is-linux

# 3. Create web app
az webapp create \
  --resource-group genivra-rg \
  --plan genivra-plan \
  --name genivra-api \
  --runtime "PYTHON|3.10"

# 4. Configure deployment from git
az webapp deployment source config-zip \
  --resource-group genivra-rg \
  --name genivra-api \
  --src

# 5. Set application settings
az webapp config appsettings set \
  -g genivra-rg \
  -n genivra-api \
  --settings ENVIRONMENT=production TIER_1_MONTHLY_LIMIT=100
```

---

## 🔐 API Key Management

### Demo Keys (Pre-configured)

Database file is at `API/auth.py`, in the `API_KEYS` dictionary:

```python
API_KEYS = {
    "demo_tier1_key_12345": {
        "tier": KeyTier.TIER_1,
        "name": "Demo Account - Tier 1",
        "org": "Genivra Demo",
        "active": True
    },
    "demo_tier2_key_67890": {
        "tier": KeyTier.TIER_2,
        "name": "Demo Account - Tier 2 (Unlimited)",
        "org": "Genivra Premium",
        "active": True
    },
}
```

### Create Production Keys

#### Option 1: Environment Variable

```bash
# Set in .env or deployment platform
API_KEYS_OVERRIDE="prod_key_001:tier_2:Pharma Corp,prod_key_002:tier_1:Lab A,prod_key_003:tier_1:Lab B"
```

#### Option 2: Admin API Endpoint

```bash
# Create new API key (requires authentication)
curl -X POST http://localhost:8000/admin/api-keys/create \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "prod_key_001",
    "tier": "tier_2",
    "name": "Pharma Corporation",
    "org": "Acme Pharma"
  }'

# Expected response:
# {
#   "message": "API key created successfully",
#   "api_key": "prod_key_001",
#   "tier": "tier_2"
# }
```

#### Option 3: Future Database Integration

See documentation in `API/auth.py` for PostgreSQL migration template:

```python
# Future: Replace in-memory dict with database table
# CREATE TABLE api_keys (
#   id SERIAL PRIMARY KEY,
#   api_key VARCHAR(50) UNIQUE NOT NULL,
#   tier VARCHAR(10) NOT NULL,
#   name VARCHAR(100) NOT NULL,
#   org VARCHAR(100),
#   created TIMESTAMP DEFAULT NOW(),
#   active BOOLEAN DEFAULT TRUE,
#   last_used TIMESTAMP
# );
```

### Check API Key Usage

```bash
# View usage for specific key
curl -X GET http://localhost:8000/admin/api-keys/usage/demo_tier1_key_12345 \
  -H "x-api-key: demo_tier1_key_12345"

# Response example:
# {
#   "api_key": "demo_tier1_key_12345",
#   "tier": "tier_1",
#   "monthly_limit": 100,
#   "usage_stats": {
#     "2026-02": 25
#   },
#   "current_month_used": 25,
#   "current_month_remaining": 75
# }
```

### List All API Keys

```bash
# Admin endpoint to list all keys
curl -X GET http://localhost:8000/admin/api-keys/list \
  -H "x-api-key: demo_tier2_key_67890"

# Response:
# [
#   {
#     "api_key": "demo_tier1_key_12345",
#     "tier": "tier_1",
#     "name": "Demo Account - Tier 1",
#     "org": "Genivra Demo",
#     "active": true,
#     "created": "2026-02-01"
#   },
#   ...
# ]
```

### Deactivate API Key

```bash
# Disable a key (soft delete)
curl -X POST http://localhost:8000/admin/api-keys/deactivate/old_key_12345 \
  -H "x-api-key: admin_key_here"

# Response:
# {"message": "API key deactivated"}

# Deactivated keys return 401: "Invalid or inactive API key"
```

---

## 🌐 CORS Configuration

### Enable Dashboard Access

CORS is **already configured** in `API/main.py` but can be customized:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # Change for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Production CORS Setup

```bash
# Set in .env
CORS_ALLOWED_ORIGINS=https://dashboard.mycompany.com,https://app.mycompany.com,https://api.mycompany.com

# Or set in deployment platform
heroku config:set CORS_ALLOWED_ORIGINS="https://dashboard.mycompany.com,https://app.mycompany.com"
```

### Troubleshoot CORS Issues

**Error:** `Access to XMLHttpRequest has been blocked by CORS policy`

**Solution:**

```bash
# 1. Check allowed origins
curl -i -X OPTIONS http://localhost:8000/predict \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type"

# 2. If failing, update CORS_ALLOWED_ORIGINS environment variable
# 3. Restart API server
```

---

## 📊 Monitoring & Logs

### View Logs

**Local Development:**
```bash
# Logs printed to console
# Shows: timestamp, logger name, level, message
```

**Heroku:**
```bash
heroku logs --tail -a genivra-api
```

**Render:**
```
Dashboard → Logs section
```

**Docker:**
```bash
docker logs -f container_id
```

### Application Metrics

**Endpoints generate metrics automatically:**
- Requests per endpoint
- Average response time
- Error rates
- API key usage tracking

**View current metrics:**
```python
# In code (API/auth.py)
from API.auth import APIKeyManager

usage = APIKeyManager.get_usage_stats("demo_tier1_key_12345")
print(usage)
# {'2026-02': 25}
```

### Enable Prediction Logging

```bash
# Set in .env
LOG_PREDICTIONS=true
PREDICTIONS_LOG_FILE=logs/predictions.log
```

Creates `logs/predictions.log`:
```
2026-02-24T10:30:15 - API_KEY: demo_tier1_key_12345 - RESULT: {"probability": 0.72, "tier": "MEDIUM", ...}
2026-02-24T10:30:30 - API_KEY: demo_tier1_key_12345 - RESULT: {"probability": 0.45, "tier": "HIGH", ...}
```

---

## 🐛 Troubleshooting

### Issue: API key returns 401 Unauthorized

**Solution:**

```bash
# 1. Verify key is included in header
curl -v -X POST http://localhost:8000/predict \
  -H "x-api-key: demo_tier1_key_12345" \
  -H "Content-Type: application/json" \
  -d '{...}'

# 2. Check if key is valid
curl -X GET http://localhost:8000/admin/api-keys/list \
  -H "x-api-key: demo_tier2_key_67890"

# 3. Ensure key is not deactivated
# Check output of list endpoint above

# 4. If using environment override, verify format:
# API_KEYS_OVERRIDE="key:tier_2:Name,key2:tier_1:Name2"
```

### Issue: 429 Too Many Requests

**Solution:**

```bash
# Check usage for key
curl -X GET http://localhost:8000/admin/api-keys/usage/demo_tier1_key_12345 \
  -H "x-api-key: demo_tier1_key_12345"

# Output shows monthly limit and remaining:
# "monthly_limit": 100
# "current_month_remaining": 0

# Options:
# 1. Wait until next month (auto-resets on 1st)
# 2. Use Tier 2 key (unlimited)
# 3. Increase TIER_1_MONTHLY_LIMIT in .env
# 4. Create new API key for different tier
```

### Issue: CORS errors in dashboard

**Solution:**

```bash
# 1. Verify API is running
curl -X GET http://localhost:8000/health

# 2. Check CORS allowed origins
# In .env: CORS_ALLOWED_ORIGINS=http://localhost:3000,...

# 3. Verify browser origin matches
# Example: If dashboard is at http://localhost:8000, 
# CORS_ALLOWED_ORIGINS must include http://localhost:8000

# 4. Restart API server
```

### Issue: Model files not found

**Solution:**

```bash
# Verify paths in .env
MODEL_ARTIFACT_DIR=Models/artifacts
FEATURE_SCALER_PATH=Models/artifacts/feature_scaler.pkl
LOGISTIC_MODEL_PATH=Models/artifacts/logistic_model.pkl

# Check files exist
ls -la Models/artifacts/
# Should show: feature_scaler.pkl, logistic_model.pkl

# If missing, rebuild models
python Scripts/run_train.py
```

### Issue: Slow API response

**Solution:**

```bash
# 1. Check server resources (CPU, memory)
#    Local: watch top / Task Manager
#    Heroku: heroku ps -a genivra-api
#    Docker: docker stats

# 2. Check model size
ls -lh Models/artifacts/*.pkl

# 3. Check for concurrent requests
# If high volume, scale horizontally:
heroku ps:scale web=2 -a genivra-api

# 4. Check logs for errors
heroku logs --tail -a genivra-api | grep ERROR
```

### Issue: Database connection errors (future)

**Solution:**

```bash
# When migrating from in-memory to database:
# 1. Set DATABASE_URL in .env
DATABASE_URL=postgresql://user:password@localhost/genivra

# 2. Run migrations
python -m alembic upgrade head

# 3. Verify connection
python -c "from API.config import settings; print(settings.database_url)"

# 4. Check database is running
psql -c "SELECT 1"  # PostgreSQL
```

---

## 📚 Additional Resources

- **API Documentation:** `/docs` (Swagger UI)
- **Alternative Docs:** `/redoc` (ReDoc)
- **API Schema:** `/openapi.json` (OpenAPI 3.0)
- **GitHub Repository:** https://github.com/AMatelis/Genivra.ai
- **Issues & Support:** GitHub Issues section

---

## ✅ Pre-Deployment Checklist

Before deploying to production:

- [ ] Create production API keys (not demo keys)
- [ ] Set `ENVIRONMENT=production` in deployment config
- [ ] Set `REQUIRE_HTTPS=true` for secure communication
- [ ] Configure `CORS_ALLOWED_ORIGINS` for your domain
- [ ] Set rate limits appropriate for your business (`TIER_1_MONTHLY_LIMIT`)
- [ ] Test all API endpoints with production keys
- [ ] Set up monitoring/alerts for API errors
- [ ] Configure automatic backups for database (if using)
- [ ] Enable logging (set `LOG_LEVEL=INFO` or `WARNING`)
- [ ] Test failover/disaster recovery plan
- [ ] Document your deployment setup
- [ ] Enable HTTPS/SSL certificates
- [ ] Set up API rate limiting/DDoS protection (at CDN/proxy level)

---

## 🎯 Summary

Your Genivra API is ready for production deployment! 

**Quick path to production:**
1. Choose platform (Heroku suggested for quick start)
2. Click "Deploy to Heroku" (one-click if set up)
3. Configure environment variables
4. Create production API keys
5. Done! 🚀

**Questions?** Check logs or run tests locally first.

---

**Last Updated:** February 24, 2026  
**API Version:** 1.0.0  
**Status:** ✅ Production Ready  
