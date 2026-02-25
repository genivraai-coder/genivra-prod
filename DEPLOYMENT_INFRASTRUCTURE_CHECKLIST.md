# ☁️ Deployment Infrastructure Checklist

**Purpose**: Comprehensive checklist for deploying Genivra API to production  
**Updated**: February 24, 2026  
**Version**: 1.0  

---

## 📋 Pre-Deployment (48 hours before)

### Code Quality
- [ ] All tests passing: `pytest -v`
- [ ] No lint errors: `flake8 API/ Models/`
- [ ] Type checking passes: `mypy API/ Models/`
- [ ] Code reviewed and approved
- [ ] Git history clean (no uncommitted changes)

### Dependencies & Requirements
- [ ] `requirements.txt` up to date
- [ ] All dependencies pinned to specific versions
- [ ] No security vulnerabilities: `pip-audit`
- [ ] Python version specified (3.10+)
- [ ] New dependencies documented in DEPLOYMENT.md

### Configuration
- [ ] `.env.example` includes all variables
- [ ] `.env.example` has sensible defaults
- [ ] No secrets in `.env.example`
- [ ] `.gitignore` includes `.env`
- [ ] Configuration module (`API/config.py`) tested

### Files Prepared
- [ ] ✅ `requirements.txt` - Dependencies
- [ ] ✅ `Procfile` - Deployment entry point
- [ ] ✅ `.env.example` - Configuration template
- [ ] ✅ `Dockerfile` - Container image
- [ ] ✅ `docker-compose.yml` - Local development
- [ ] ✅ `runtime.txt` - Python version
- [ ] ✅ `DEPLOYMENT.md` - Full deployment guide
- [ ] ✅ `API/config.py` - Environment configuration

---

## 🚀 Deployment Execution

### Step 1: Final Validation (Before deployment)

**Local Testing**:
```bash
# Run full test suite
pytest -v --cov=API --cov=Models

# Test app startup
python -m uvicorn API.main:app --reload

# Test key endpoints
curl -X GET http://localhost:8000/health \
  -H "x-api-key: demo_tier1_key_12345"

# Test prediction
curl -X POST http://localhost:8000/predict \
  -H "x-api-key: demo_tier1_key_12345" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

- [ ] All tests pass
- [ ] No lint errors
- [ ] App starts without errors
- [ ] Health endpoint works
- [ ] Prediction endpoint works
- [ ] API authentication works

### Step 2: Prepare Deployment Platform

**Heroku**:
```bash
heroku login
heroku create genivra-api
heroku config:set ENVIRONMENT=production
heroku config:set TIER_1_MONTHLY_LIMIT=100
heroku config:set API_KEYS_OVERRIDE="prodkey:tier2:Company"
git push heroku main
```

- [ ] Platform account created
- [ ] Environment variables configured
- [ ] Deployment credentials stored securely
- [ ] Team has access to dashboard

**Docker/Other**:
```bash
docker build -t genivra-api:latest .
docker push myregistry.azurecr.io/genivra-api:latest
# Deploy to Kubernetes/Swarm/other orchestration
```

- [ ] Docker image builds successfully
- [ ] Image uploaded to registry
- [ ] Orchestration platform configured

### Step 3: Configure Environment

- [ ] `ENVIRONMENT=production`
- [ ] `PORT` properly set (8000 or as required)
- [ ] `LOG_LEVEL=INFO` (not DEBUG in production)
- [ ] `REQUIRE_HTTPS=true` (for production)
- [ ] `CORS_ALLOWED_ORIGINS` restricted to actual domains
- [ ] `API_KEYS_OVERRIDE` set with production keys (not demo keys)
- [ ] `TIER_1_MONTHLY_LIMIT` set appropriately
- [ ] Model paths correct and accessible
- [ ] Database URL configured (if applicable)

### Step 4: Deploy Application

- [ ] Code pushed to production branch
- [ ] Deployment triggered
- [ ] Container/dyno started
- [ ] Startup scripts completed
- [ ] Logs show successful startup
- [ ] No critical errors in logs

### Step 5: Verify Deployment (Post-deployment)

**Smoke Tests**:
```bash
# Health check
curl -X GET https://api.yourdomain.com/health

# API docs load
curl https://api.yourdomain.com/docs | grep -q swagger

# API key required
curl -X POST https://api.yourdomain.com/predict \
  -H "Content-Type: application/json" \
  -d '{}' | grep -q "Missing x-api-key"

# Valid prediction
curl -X POST https://api.yourdomain.com/predict \
  -H "x-api-key: YOUR_PRODUCTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

- [ ] `/health` returns 200
- [ ] `/docs` loads successfully
- [ ] `/redoc` loads successfully
- [ ] API key validation works (401 without key)
- [ ] Prediction works with valid key
- [ ] Batch prediction works
- [ ] CORS headers present
- [ ] Response times acceptable (<1 second)

---

## 📊 Post-Deployment Monitoring (First 24 hours)

### Immediate (First 2 hours)
- [ ] Monitor error rates (should be <0.1%)
- [ ] Monitor response times (should be <1s avg)
- [ ] Check logs for errors/warnings
- [ ] Verify API availability (should be 100%)
- [ ] Monitor CPU usage (should be <50%)
- [ ] Monitor memory usage (should be <60%)
- [ ] Check disk space (should be >10% free)

### First 24 hours
- [ ] Monitor API key usage/rate limiting
- [ ] Check database queries (if applicable)
- [ ] Monitor for unusual error patterns
- [ ] Check for security-related errors
- [ ] Verify customer feedback/support tickets
- [ ] Monitor data pipeline (if applicable)

### Ongoing (After 24 hours)
- [ ] Set up automatic alerts for errors
- [ ] Set up automatic alerts for latency
- [ ] Set up automatic alerts for availability
- [ ] Set up daily log review process
- [ ] Set up weekly metrics review
- [ ] Schedule post-deployment review

---

## 🔐 Security Validation

- [ ] No hardcoded credentials in code
- [ ] `.env` file not in git
- [ ] API keys rotated from demo keys
- [ ] HTTPS/TLS enabled
- [ ] CORS origins restricted
- [ ] Database credentials strong
- [ ] Database backups encrypted
- [ ] Logs don't contain sensitive data
- [ ] API rate limiting enforced
- [ ] API authentication enforced

---

## 🔄 Rollback Plan

If critical issues found:

**Immediate Actions**:
- [ ] Identify issue (check logs/alerts)
- [ ] Notify team via Slack/PagerDuty
- [ ] Create incident ticket
- [ ] Start rollback process
- [ ] Communicate status to customers

**Rollback Execution**:

Heroku:
```bash
heroku releases -a genivra-api
heroku releases:rollback v49 -a genivra-api
heroku logs --tail -a genivra-api
```

Docker:
```bash
docker service update --image registry/genivra-api:v1.0 genivra-api
# or
kubectl set image deployment/genivra-api
```

**Post-Rollback**:
- [ ] Verify application working
- [ ] Communicate rollback to team
- [ ] Document what went wrong
- [ ] Fix issues in development
- [ ] Schedule retry deployment
- [ ] Conduct post-mortem review

---

## 📈 Deployment Success Criteria

Application is considered successfully deployed when:

1. **API Availability**: 99.9%+ (measured over 1 hour)
2. **Response Time**: <1 second average
3. **Error Rate**: <0.1% 
4. **Authentication**: All requests require valid API key
5. **Rate Limiting**: Tier 1 keys limited to 100/month
6. **Logging**: No ERROR level logs (WARNING ok)
7. **Monitoring**: All alerts functional
8. **Documentation**: Deployment guide accessible
9. **Backups**: Database backed up successfully
10. **Team Trained**: On-call team knows how to monitor & respond

---

## 📞 Support Information

### On-Call Contacts
| Role | Name | Contact |
|------|------|---------|
| Lead Engineer | — | — |
| DevOps | — | — |
| Manager | — | — |

### Escalation Levels
- **Level 1** (Agent): API errors, response time issues
- **Level 2** (Engineer): Database issues, deployment issues
- **Level 3** (CTO): Architectural issues, major outages

### Communication Channels
- **Critical**: Page via PagerDuty
- **Urgent**: Slack #genivra-incidents
- **Normal**: GitHub Issues
- **Updates**: Status page / Customer email

---

## ✅ Sign-Off

- **Deployed by**: ________________
- **Date/Time**: ________________
- **Deployment Duration**: ________________
- **Issues Encountered**: ☐ Yes ☐ No
- **Rollback Required**: ☐ Yes ☐ No

**Final Status**: ☐ Successful ☐ Partial ☐ Rolled Back

**Notes**:
_____________________________________________________________________________
_____________________________________________________________________________

**Approved by**: ________________ Date: ________________

---

*See DEPLOYMENT.md for detailed platform-specific instructions*
