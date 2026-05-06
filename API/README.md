# Genivra API

This folder contains the REST API for serving trial predictions. Start with `API/main.py` first.

**Status:** Production Ready  
**Version:** 1.0.0  
**Created:** February 24, 2026

---

## Overview

The Genivra API provides a FastAPI-based REST interface to the predictive trial scoring engine. It accepts structured trial data and returns interpretable risk assessments with actionable biomarker insights.

```
HTTP POST /predict
├── Input: Trial design, endpoints, biomarkers, enrollment
├── Process: Feature engineering → Logistic regression model
└── Output: Success probability, risk tier, top drivers, explanation
```

---

## Quick Start

### 1. Install Dependencies

```bash
# From project root
pip install -r requirements.txt
```

### 2. Run the API Server

```bash
# Development (with auto-reload)
uvicorn API.main:app --reload

# Access at: http://localhost:8000
# Docs at: http://localhost:8000/docs
# Local development now accepts a default demo API key if none is provided.
```

### 3. Send a Prediction Request

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -H "x-api-key: demo_tier2_key_67890" \
  -d '{
    "trial_design": {
      "trial_sample_size": 200,
      "trial_duration_weeks": 52
    },
    "endpoints": {
      "endpoint_type": "objective",
      "primary_endpoint_name": "CDR-SB"
    },
    "biomarkers": {
      "apoe_e4_carrier": 1,
      "ptau217_high": 1,
      "amyloid_pet_positive": 1
    },
    "enrollment": {
      "age_mean": 72.5,
      "baseline_mmse": 22.0,
      "cdr_baseline": 1.5
    }
  }'
```

You can also pass the API key as a bearer token:

```bash
-H "Authorization: Bearer demo_tier2_key_67890"
```

### 4. Check API Key Limits

```bash
curl -X GET http://localhost:8000/api-key/status \
  -H "x-api-key: demo_tier2_key_67890"
```

---

## File Structure

```
API/
├── main.py                    # FastAPI application & endpoints
├── models.py                  # Pydantic request/response schemas
├── __init__.py               # Package initialization
├── test_api.py               # Pytest test suite
├── example_usage.py          # Client example
├── API_DOCUMENTATION.md      # Full API documentation
└── README.md                 # This file
```

---

## API Endpoints

### Health Checks

- **GET** `/` - Basic health status
- **GET** `/health` - Detailed health status

### Predictions

- **POST** `/predict` - Predict trial success with risk assessment

### Documentation

- **GET** `/docs` - Interactive Swagger UI
- **GET** `/redoc` - ReDoc documentation

---

## Core Features

### ✅ Input Validation
- Required fields enforcement
- Type checking (Pydantic models)
- Range validation (ages, scores, etc.)
- Enum validation (endpoint types, enrichment strategies)

### ✅ Prediction Engine
- Connects to trained logistic regression model
- Feature engineering matching training pipeline
- Confidence assessment based on data completeness
- Risk tier classification

### ✅ Interpretable Output
- Success probability (0-1)
- Risk tier (LOW/MEDIUM/HIGH)
- Top 5 feature drivers with coefficients
- Plain-English biomarker explanation
- Confidence flag with missing field count

### ✅ Production Ready
- CORS enabled for browser testing
- Comprehensive logging
- Error handling with structured error responses
- Interactive API documentation

---

## Testing

### Run All Tests

```bash
pytest API/test_api.py -v
```

### Run Specific Test Class

```bash
pytest API/test_api.py::TestPredictions -v
```

### Run with Coverage

```bash
pytest API/test_api.py --cov=API --cov-report=html
```

### Test Categories

- **Health Checks** - Endpoint availability
- **Predictions** - Core prediction functionality
- **Input Validation** - Error handling for invalid inputs
- **Risk Tiers** - Threshold classification
- **Response Format** - Output structure validation
- **Content Type** - JSON handling

---

## Example Use Cases

### Example 1: High-Success Trial

```python
import requests

payload = {
    "trial_design": {
        "trial_sample_size": 200,
        "trial_duration_weeks": 52
    },
    "endpoints": {
        "endpoint_type": "objective",
        "primary_endpoint_name": "CDR-SB"
    },
    "biomarkers": {
        "apoe_e4_carrier": 1,
        "ptau217_high": 1,
        "amyloid_pet_positive": 1,
        "tau_pet_positive": 1
    },
    "enrollment": {
        "age_mean": 72.5,
        "baseline_mmse": 22.0,
        "cdr_baseline": 1.5
    },
    "biomarker_enrichment_strategy": "at_positive"
}

response = requests.post("http://localhost:8000/predict", json=payload)
result = response.json()

print(f"Success: {result['trial_success_probability']:.1%}")  # ~95%
print(f"Risk: {result['risk_tier']}")  # LOW
```

### Example 2: High-Risk Trial

```python
payload = {
    "trial_design": {
        "trial_sample_size": 50,
        "trial_duration_weeks": 12
    },
    "endpoints": {
        "endpoint_type": "subjective",
        "primary_endpoint_name": "MMSE"
    },
    "biomarkers": {
        "apoe_e4_carrier": 0,
        "ptau217_high": 0,
        "amyloid_pet_positive": 0
    },
    "enrollment": {
        "age_mean": 65.0,
        "baseline_mmse": 26.0,
        "cdr_baseline": 0.5
    },
    "biomarker_enrichment_strategy": "cognitive_only"
}

response = requests.post("http://localhost:8000/predict", json=payload)
result = response.json()

print(f"Success: {result['trial_success_probability']:.1%}")  # ~5-10%
print(f"Risk: {result['risk_tier']}")  # HIGH
```

---

## Deployment

### Local Development

```bash
uvicorn API.main:app --reload --host 0.0.0.0 --port 8000
```

### Production (Gunicorn)

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker API.main:app --bind 0.0.0.0:8000
```

### Docker

```bash
docker build -t genivra-api .
docker run -p 8000:8000 genivra-api
```

### Cloud Deployment

Example deployment to Render, Railway, or Heroku:

```bash
# Ensure requirements.txt is up to date
pip freeze > requirements.txt

# Deploy (platform-specific instructions)
# See API_DOCUMENTATION.md for Docker example
```

---

## Configuration

### CORS Settings (main.py)

**Development (allow all):**
```python
allow_origins=["*"]
```

**Production (specific domain):**
```python
allow_origins=["https://yourdomain.com"]
```

### Logging

Logs are printed to console in development. For production, configure in `main.py`:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api.log"),
        logging.StreamHandler()
    ]
)
```

---

## Monitoring

### Health Check Endpoint

Use for load balancer health checks:

```bash
curl http://localhost:8000/health
```

### Logs

Monitor real-time logs:

```bash
# In development
tail -f console output

# With gunicorn
tail -f gunicorn.log
```

---

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'Models'"

**Solution:** Run from project root:
```bash
cd /path/to/Genivra.ai
uvicorn API.main:app --reload
```

### Issue: "Address already in use"

**Solution:** Use different port:
```bash
uvicorn API.main:app --port 8001
```

### Issue: CORS errors from frontend

**Solution:** Verify CORS is enabled in `API/main.py`:
```python
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
```

### Issue: Prediction returns error

**Check:**
1. All required fields present (trial_design, endpoints, biomarkers, enrollment)
2. Data types are correct (integers, floats, strings as specified)
3. Value ranges valid (sample size > 0, age/scores in range)
4. ML model artifacts exist (`models/artifacts/logistic_model.pkl`)

---

## Integration Examples

### JavaScript/React

```javascript
const response = await fetch('http://localhost:8000/predict', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    trial_design: { trial_sample_size: 200, trial_duration_weeks: 52 },
    endpoints: { endpoint_type: 'objective', primary_endpoint_name: 'CDR-SB' },
    biomarkers: { apoe_e4_carrier: 1, ptau217_high: 1, amyloid_pet_positive: 1 },
    enrollment: { age_mean: 72.5, baseline_mmse: 22.0, cdr_baseline: 1.5 }
  })
});

const result = await response.json();
console.log(`Success: ${(result.trial_success_probability * 100).toFixed(1)}%`);
```

### Python (with type hints)

See `example_usage.py` for complete example.

---

## API Performance

- **Prediction latency:** ~50-100ms (model inference)
- **Throughput:** ~100-200 requests/second (single instance)
- **Model size:** ~2MB
- **Memory usage:** ~200MB at startup

For higher throughput, deploy multiple instances behind a load balancer.

---

## Documentation

- **API_DOCUMENTATION.md** - Complete API reference
- **example_usage.py** - Python client example
- **test_api.py** - Test suite with examples
- **/docs** - Interactive Swagger UI

---

## Support & Contribution

### Issues

Check `API_DOCUMENTATION.md` for common issues and error codes.

### Testing

Before deployment, ensure all tests pass:

```bash
pytest API/test_api.py -v
```

### Version Info

- **API Version:** 1.0.0
- **Model Version:** v1.0
- **Python:** ≥3.8
- **FastAPI:** 0.104.1+

---

## License

Part of the Genivra project.
