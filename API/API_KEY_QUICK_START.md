# API Key Authentication - Quick Start

## 1. Demo Keys (Pre-configured)

Two demo keys are ready to use immediately:

```
Tier 1 (Limited): demo_tier1_key_12345
Tier 2 (Unlimited): demo_tier2_key_67890
```

---

## 2. Using the Dashboard

### Open Dashboard
```bash
# Windows
start FrontEnd/dashboard.html

# macOS/Linux
open FrontEnd/dashboard.html
```

### Enter API Key
1. Click "API Key:" field in top right
2. Paste demo key or your own key
3. Click "Save"
4. Status will show "✓ Connected"

---

## 3. Using cURL

### Single Prediction
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -H "x-api-key: demo_tier1_key_12345" \
  -d '{
    "phase": "Phase 3",
    "indication": "Alzheimers disease",
    "trial_design": {
      "trial_sample_size": 200,
      "trial_duration_weeks": 52,
      "number_of_arms": 2,
      "randomization_ratio": "1:1"
    },
    "endpoints": {
      "endpoint_type": "objective",
      "primary_endpoint_name": "CDR-SB"
    },
    "biomarkers": {},
    "enrollment": {
      "age_mean": 72.5
    }
  }'
```

### Batch Predictions
```bash
curl -X POST http://localhost:8000/predict_batch \
  -H "x-api-key: demo_tier1_key_12345" \
  -F "file=@trials.csv"
```

---

## 4. Using Python

```python
import requests
import json

# Set API key
API_KEY = "demo_tier1_key_12345"
HEADERS = {"x-api-key": API_KEY}

# Single prediction
response = requests.post(
    "http://localhost:8000/predict",
    headers=HEADERS,
    json={
        "phase": "Phase 3",
        "indication": "Alzheimers disease",
        "trial_design": {
            "trial_sample_size": 200,
            "trial_duration_weeks": 52,
            "number_of_arms": 2,
            "randomization_ratio": "1:1"
        },
        "endpoints": {
            "endpoint_type": "objective",
            "primary_endpoint_name": "CDR-SB"
        },
        "biomarkers": {},
        "enrollment": {"age_mean": 72.5}
    }
)
print(response.json())

# Batch prediction
with open("trials.csv", "rb") as f:
    files = {"file": f}
    response = requests.post(
        "http://localhost:8000/predict_batch",
        headers=HEADERS,
        files=files
    )
print(response.json())
```

---

## 5. Check Usage

### View Your Monthly Usage
```bash
curl http://localhost:8000/admin/api-keys/usage/demo_tier1_key_12345
```

Response:
```json
{
    "api_key": "demo_tier1_key_12345",
    "tier": "tier_1",
    "current_month": "2026-02",
    "current_usage": 15,
    "limit": 100,
    "remaining": 85
}
```

---

## 6. Error Handling

### Missing Header
```
Status: 401 Unauthorized
Detail: "Missing x-api-key header"
```

### Invalid Key
```
Status: 401 Unauthorized
Detail: "Invalid or inactive API key"
```

### Rate Limit Exceeded (Tier 1)
```
Status: 429 Too Many Requests
Detail: "Rate limit exceeded: 100/100 requests used this month"
```

---

## 7. Create Custom API Key

### Admin Command
```bash
curl -X POST "http://localhost:8000/admin/api-keys/create?api_key=my_custom_key_xyz&tier=tier_2&name=My%20App&org=My%20Corp"
```

### Then Use
```bash
curl -X POST http://localhost:8000/predict \
  -H "x-api-key: my_custom_key_xyz" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

---

## 8. Tier Comparison

| Feature | Tier 1 | Tier 2 |
|---------|--------|--------|
| Monthly Limit | 100 | Unlimited |
| Use Case | Testing | Production |
| Cost | $0 (demo) | $X/month |
| Rate Limit Error | 429 | Never |

---

## 9. Production Checklist

- [ ] Create production API key (Tier 2)
- [ ] Remove demo keys from code
- [ ] Use HTTPS (not HTTP) in production
- [ ] Store key in environment variable: `GENIVRA_API_KEY`
- [ ] Monitor usage monthly
- [ ] Set up alerts for 80% limit (Tier 1)
- [ ] Document key rotation policy

---

## 10. Troubleshooting

### "Missing x-api-key header"
**Fix:** Add `-H "x-api-key: YOUR_KEY"` to request

### "Invalid API key"
**Fix:** Check key is correct, hasn't been deactivated

### "Rate limit exceeded"
**Fix:** Wait until next month or upgrade to Tier 2

### Dashboard shows "✗ Auth Failed"
**Fix:** Verify API key is correct in the API Key field

---

**Quick Links:**
- Full Guide: [API_KEY_AUTH_GUIDE.md](API_KEY_AUTH_GUIDE.md)
- Dashboard: [dashboard.html](../FrontEnd/dashboard.html)
- Auth Module: [auth.py](auth.py)

---

**Version:** 1.0.0  
**Date:** February 24, 2026
