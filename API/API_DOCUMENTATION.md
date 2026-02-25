# Genivra API Documentation

**Version:** 1.0.0  
**Created:** February 24, 2026  
**Status:** Production Ready

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the API Server

```bash
# From the project root directory
uvicorn API.main:app --reload
```

The API will be available at `http://localhost:8000`

### 3. Access the Interactive Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## Endpoints

### Health Check

#### GET `/`

Returns basic health status.

**Response:**
```json
{
  "status": "running",
  "version": "1.0.0",
  "timestamp": "2026-02-24T15:30:00Z"
}
```

---

#### GET `/health`

Returns detailed health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-02-24T15:30:00Z"
}
```

---

### Predictions

#### POST `/predict`

**Purpose:** Predict CNS trial success probability and risk tier.

**Request Body:**

```json
{
  "phase": "Phase II",
  "indication": "Alzheimer's Disease",
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
  "biomarkers": {
    "apoe_e4_carrier": 1,
    "apoe_e4_homozygous": 0,
    "ptau217_high": 1,
    "ptau217_continuous": 18.5,
    "csf_abeta42_40_ratio_low": 1,
    "csf_ptau_elevated": 0,
    "amyloid_pet_positive": 1,
    "tau_pet_positive": 1,
    "hippocampal_atrophy_mri": 3800.0,
    "hippocampal_atrophy_binary": 1
  },
  "enrollment": {
    "age_mean": 72.5,
    "baseline_mmse": 22.0,
    "baseline_moca": 21.0,
    "cdr_baseline": 1.5
  },
  "biomarker_enrichment_strategy": "at_positive"
}
```

**Response:**

```json
{
  "trial_success_probability": 0.958,
  "risk_tier": "LOW",
  "top_drivers": [
    {
      "feature_name": "amyloid_pet_positive",
      "coefficient": 2.845,
      "direction": "positive",
      "impact_magnitude": 2.845
    },
    {
      "feature_name": "ptau217_high",
      "coefficient": 1.932,
      "direction": "positive",
      "impact_magnitude": 1.932
    },
    {
      "feature_name": "trial_duration_weeks",
      "coefficient": 0.687,
      "direction": "positive",
      "impact_magnitude": 0.687
    }
  ],
  "biomarker_explanation": "Strong amyloid and phosphorylated tau signals; APOE ε4 carrier status increases risk profile. Hippocampal atrophy indicates neurodegeneration. Well-enriched cohort for anti-amyloid intervention.",
  "confidence_flag": "HIGH",
  "missing_biomarker_count": 0,
  "model_version": "v1.0",
  "generated_timestamp": "2026-02-24T15:30:45Z"
}
```

---

## Input Schema

### Trial Design

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `trial_sample_size` | integer | ✓ | Planned enrollment (must be > 0) |
| `trial_duration_weeks` | integer | ✓ | Duration in weeks (must be > 0) |
| `number_of_arms` | integer | | Number of parallel arms (≥1) |
| `randomization_ratio` | string | | e.g., "1:1", "2:1", "open_label" |
| `phase` | string | | "Phase II", "Phase III", etc. |
| `indication` | string | | Disease indication |

### Endpoints

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `endpoint_type` | string | ✓ | "objective", "subjective", or "mixed" |
| `primary_endpoint_name` | string | ✓ | e.g., "CDR-SB", "ADAS-Cog", "MMSE", "amyloid_pet_suvr" |

### Biomarkers

All biomarker fields are **optional**. Missing values are handled gracefully.

#### Genetic
- `apoe_e4_carrier` (0/1/null): ≥1 ε4 allele present?
- `apoe_e4_homozygous` (0/1/null): e4/e4 genotype?

#### Blood (Plasma)
- `ptau217_high` (0/1/null): > 14.5 pg/mL?
- `ptau217_continuous` (float/null): Raw value in pg/mL

#### Cerebrospinal Fluid (CSF)
- `csf_abeta42_40_ratio_low` (0/1/null): < 0.5?
- `csf_abeta42_40_ratio_continuous` (float/null): Raw ratio
- `csf_ptau_elevated` (0/1/null): > 79 pg/mL?

#### Imaging
- `amyloid_pet_positive` (0/1/null): SUVR > 1.2?
- `tau_pet_positive` (0/1/null): SUVR > 1.3?
- `hippocampal_atrophy_mri` (float/null): Volume in mm³
- `hippocampal_atrophy_binary` (0/1/null): < 10th percentile?

### Enrollment

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `age_mean` | float | ✓ | Mean baseline age (years) |
| `baseline_mmse` | float | | MMSE score (0-30) |
| `baseline_moca` | float | | MoCA score (0-30) |
| `cdr_baseline` | float | | CDR sum-of-boxes (0-18) |

### Enrichment Strategy

| Field | Type | Description |
|-------|------|-------------|
| `biomarker_enrichment_strategy` | string | "amyloid_positive", "tau_positive", "at_positive", "cognitive_only", "none", "unknown" |

---

## Output Schema

| Field | Type | Description |
|-------|------|-------------|
| `trial_success_probability` | float (0-1) | Predicted success probability |
| `risk_tier` | string | "LOW" (≥70%), "MEDIUM" (40-69%), "HIGH" (<40%) |
| `top_drivers` | array | Top 5 features influencing prediction |
| `biomarker_explanation` | string | Plain-English summary of drivers |
| `confidence_flag` | string | "HIGH", "MEDIUM", "LOW" based on data completeness |
| `missing_biomarker_count` | integer | Count of required fields missing |
| `model_version` | string | "v1.0" |
| `generated_timestamp` | string | ISO 8601 UTC timestamp |

### Feature Driver

Each driver in `top_drivers`:

| Field | Type | Description |
|-------|------|-------------|
| `feature_name` | string | Name of biomarker/feature |
| `coefficient` | float | Model coefficient (positive/negative) |
| `direction` | string | "positive" or "negative" |
| `impact_magnitude` | float | Absolute value of coefficient |

---

## Error Handling

### 400 Bad Request

Missing or invalid required fields.

```json
{
  "error": "ValidationError",
  "message": "Missing required fields: trial_design, endpoints, biomarkers, enrollment",
  "status_code": 400,
  "timestamp": "2026-02-24T15:30:45Z"
}
```

### 500 Internal Server Error

Prediction failed or unexpected error.

```json
{
  "error": "InternalServerError",
  "message": "Model prediction failed: ...",
  "status_code": 500,
  "timestamp": "2026-02-24T15:30:45Z"
}
```

---

## Examples

### Example 1: High-Success Lecanemab-like Trial

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "phase": "Phase II",
    "indication": "Alzheimer'\''s Disease",
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
  }'
```

Expected: ~95%+ success probability, LOW risk

### Example 2: High-Risk Trial

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
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
  }'
```

Expected: ~5-10% success probability, HIGH risk

---

## Python Client Example

```python
import requests

url = "http://localhost:8000/predict"

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
        "amyloid_pet_positive": 1
    },
    "enrollment": {
        "age_mean": 72.5,
        "baseline_mmse": 22.0,
        "cdr_baseline": 1.5
    }
}

response = requests.post(url, json=payload)
result = response.json()

print(f"Success Probability: {result['trial_success_probability']:.1%}")
print(f"Risk Tier: {result['risk_tier']}")
print(f"Confidence: {result['confidence_flag']}")
```

---

## Deployment

### Development

```bash
uvicorn API.main:app --reload --host 0.0.0.0 --port 8000
```

### Production (with Gunicorn)

```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker API.main:app --bind 0.0.0.0:8000
```

### Docker (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "API.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## CORS Configuration

The API allows cross-origin requests from all domains. For production, modify this in `API/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],  # Specify allowed domains
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

---

## Model Information

- **Version:** v1.0
- **Algorithm:** Logistic Regression
- **Training Data:** Synthetic CNS Phase II trials
- **Features:** 29 (11 required biomarkers + trial design + endpoints)
- **Accuracy:** 98.33%
- **Confidence Assessment:** Data completeness-based

---

## Support

For issues or questions:
1. Check the interactive docs: http://localhost:8000/docs
2. Review PREDICT_TRIAL_GUIDE.md for ML model details
3. Check error logs for detailed error messages
