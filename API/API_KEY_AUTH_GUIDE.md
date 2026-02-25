# API Key Authentication Guide

## Overview

The Genivra API now requires API key authentication for all prediction endpoints:
- `POST /predict` - Single trial predictions
- `POST /predict_batch` - Batch CSV predictions

API keys are tier-based with rate limiting and usage tracking.

---

## API Key Tiers

### Tier 1: Limited Access
- **Rate Limit:** 100 requests per month
- **Use Case:** Development, testing, small-scale trials
- **Demo Key:** `demo_tier1_key_12345`

### Tier 2: Unlimited Access
- **Rate Limit:** Unlimited requests
- **Use Case:** Production, enterprise customers
- **Demo Key:** `demo_tier2_key_67890`

---

## Authentication

### Adding API Key to Requests

All requests to `/predict` and `/predict_batch` must include the `x-api-key` header:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -H "x-api-key: demo_tier1_key_12345" \
  -d '{"trial_design": {...}, ...}'
```

### Using the Dashboard

1. Open `FrontEnd/dashboard.html`
2. Enter your API key in the "API Key:" field (top right)
3. Click "Save"
4. Dashboard will verify the key and show connection status

### Using Python

```python
import requests

api_key = "demo_tier1_key_12345"
headers = {
    "Content-Type": "application/json",
    "x-api-key": api_key,
}

response = requests.post(
    "http://localhost:8000/predict",
    headers=headers,
    json={"trial_design": {...}, ...}
)
```

### Using JavaScript/Fetch

```javascript
const apiKey = "demo_tier1_key_12345";

fetch("http://localhost:8000/predict", {
    method: "POST",
    headers: {
        "Content-Type": "application/json",
        "x-api-key": apiKey,
    },
    body: JSON.stringify({
        trial_design: {...},
        ...
    })
})
```

---

## Error Responses

### Missing API Key
```
Status: 401 Unauthorized

{
    "detail": "Missing x-api-key header"
}
```

### Invalid API Key
```
Status: 401 Unauthorized

{
    "detail": "Invalid or inactive API key"
}
```

### Rate Limit Exceeded
```
Status: 429 Too Many Requests

{
    "detail": "Rate limit exceeded: 100/100 requests used this month"
}
```

---

## Admin Endpoints

Manage API keys and view usage statistics.

### View Usage Statistics

Get usage info for a specific API key:

```bash
curl http://localhost:8000/admin/api-keys/usage/demo_tier1_key_12345
```

**Response:**
```json
{
    "api_key": "demo_tier1_key_12345",
    "name": "Demo Account - Tier 1",
    "tier": "tier_1",
    "current_month": "2026-02",
    "current_usage": 15,
    "limit": 100,
    "remaining": 85
}
```

### List All API Keys

Get list of all keys with current usage:

```bash
curl http://localhost:8000/admin/api-keys/list
```

**Response:**
```json
{
    "total_keys": 2,
    "keys": [
        {
            "api_key": "demo_tier1_key_...",
            "name": "Demo Account - Tier 1",
            "tier": "tier_1",
            "active": true,
            "created": "2026-02-01T00:00:00",
            "current_month_usage": 25
        },
        {
            "api_key": "demo_tier2_key_...",
            "name": "Demo Account - Tier 2",
            "tier": "tier_2",
            "active": true,
            "created": "2026-02-01T00:00:00",
            "current_month_usage": 1000
        }
    ],
    "timestamp": "2026-02-24T10:30:45.123456Z"
}
```

### Create New API Key

```bash
curl -X POST "http://localhost:8000/admin/api-keys/create?api_key=custom_key_xyz&tier=tier_2&name=Customer%20ABC&org=ABC%20Corp"
```

**Response:**
```json
{
    "message": "API key created successfully",
    "api_key": "custom_key_...",
    "tier": "tier_2",
    "name": "Customer ABC",
    "org": "ABC Corp"
}
```

### Deactivate API Key

```bash
curl -X POST http://localhost:8000/admin/api-keys/deactivate/demo_tier1_key_12345
```

**Response:**
```json
{
    "message": "API key deactivated successfully",
    "api_key": "demo_tier1_..."
}
```

---

## Usage Tracking

### How Usage is Counted

- **Single Predictions:** 1 request = 1 usage count
- **Batch Predictions:** 1 request = 1 count per successful prediction (failed rows don't count)

Example:
- Upload CSV with 10 trials
- 8 succeed, 2 fail
- Usage: +8 (only successful rows counted)

### Monthly Reset

Usage counters reset automatically at the start of each month (UTC).

Example Timeline:
- Feb 1-28: 100 requests used (Tier 1)
- Mar 1: Counter resets to 0/100

---

## Demo Keys

Two demo keys are pre-configured for testing:

| Key | Tier | Limit | Use Case |
|-----|------|-------|----------|
| `demo_tier1_key_12345` | Tier 1 | 100/month | Testing small workflows |
| `demo_tier2_key_67890` | Tier 2 | Unlimited | Testing production workflows |

### Testing Rate Limits

To test Tier 1 rate limiting:

```bash
# Use Tier 1 key to exhaust monthly limit
for i in {1..100}; do
  curl -X POST http://localhost:8000/predict \
    -H "x-api-key: demo_tier1_key_12345" \
    -H "Content-Type: application/json" \
    -d '{"trial_design": {...}, ...}'
done

# 101st request will get 429 Too Many Requests
```

---

## Implementation Details

### Architecture

The authentication system is modular and can be replaced with a database backend:

```python
# Current: In-memory implementation
from API.auth import APIKeyManager

# Usage:
is_valid, tier, name = APIKeyManager.validate_key(api_key)
allowed, message = APIKeyManager.check_rate_limit(api_key)
APIKeyManager.increment_usage(api_key)
```

### In-Memory Storage

- **API_KEYS:** Dictionary of {key_string: key_info}
- **USAGE_TRACKER:** Dictionary of {key_string: {month_year: count}}

### Thread Safety

All operations are protected by threading locks for concurrent requests.

---

## Production Migration

To use a database instead of in-memory storage:

1. Create `API/auth_db.py` with `APIKeyManagerDB` class
2. Implement database queries for:
   - `validate_key(api_key)` - Query api_keys table
   - `check_rate_limit(api_key)` - Query usage_log table
   - `increment_usage(api_key)` - Update usage_log
3. Update `API/main.py` imports:
   ```python
   from API.auth_db import APIKeyManagerDB
   key_manager = APIKeyManagerDB(get_db_connection())
   ```

### Database Schema (Example: PostgreSQL)

```sql
-- API Keys table
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    key_string VARCHAR(255) UNIQUE NOT NULL,
    tier VARCHAR(20) NOT NULL,
    name VARCHAR(255),
    org VARCHAR(255),
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255)
);

-- Usage log table
CREATE TABLE usage_log (
    id SERIAL PRIMARY KEY,
    key_id INTEGER REFERENCES api_keys(id),
    month_year VARCHAR(7),  -- Format: YYYY-MM
    request_count INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(key_id, month_year)
);

-- Create indexes
CREATE INDEX idx_api_keys_key ON api_keys(key_string);
CREATE INDEX idx_usage_log_key_month ON usage_log(key_id, month_year);
```

---

## FAQ

### Q: Can I use multiple API keys?
**A:** Yes. Each key is tracked independently with its own tier and usage count.

### Q: What happens if I exceed my rate limit?
**A:** The API returns 429 Too Many Requests. Try again next month or upgrade to Tier 2.

### Q: Can I have unlimited Tier 2 keys?
**A:** Yes, you can create as many Tier 2 keys as needed (one per application/customer).

### Q: How do I reset my monthly usage?
**A:** Usage resets automatically at the start of each UTC month. Contact support for emergency resets.

### Q: Can I use the same key across multiple applications?
**A:** Yes, but usage is combined. For separate tracking, create separate keys per app.

### Q: What's the cost difference between tiers?
**A:** Contact sales for pricing. Demo keys are free for testing.

---

## Security Notes

1. **Never** commit API keys to version control
2. **Store** keys in environment variables or secure vaults
3. **Rotate** keys regularly (every 90 days recommended)
4. **Monitor** usage patterns for anomalies
5. **Use HTTPS** in production (not HTTP)
6. **Deactivate** old/unused keys immediately

---

## Support

For API key issues, contact: support@genivra.ai

---

**API Version:** 1.0.0  
**Auth System Version:** 1.0.0  
**Last Updated:** February 24, 2026
