# 🔐 GENIVRA BACKEND CONTRACT AUDIT
**Date:** June 2, 2026  
**Purpose:** Complete API specification for frontend integration  
**Status:** ✅ Verified against API code (main.py, models.py, predict_trial.py)

---

## 1. AVAILABLE ENDPOINTS

### ✅ GET `/`
- **Purpose:** Root health check
- **Auth:** Optional
- **Response:** `HealthResponse`
```json
{
  "status": "running",
  "version": "1.0.0",
  "timestamp": "2026-06-02T10:30:00Z"
}
```

### ✅ GET `/health`
- **Purpose:** Detailed health check
- **Auth:** Optional
- **Response:** `HealthResponse`
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-06-02T10:30:00Z"
}
```

### ⭐ POST `/predict`
- **Purpose:** Single trial success prediction
- **Auth:** Optional (development mode)
- **Request:** `PredictionRequest` (JSON)
- **Response:** `PredictionResponse` (JSON)
- **Status Code:** 200 OK, 400 Bad Request, 500 Server Error

### ✅ POST `/predict_batch`
- **Purpose:** Batch predictions from CSV file
- **Auth:** Required API key
- **Request:** Multipart form-data with CSV file
- **Response:** `BatchPredictionResponse` (JSON or CSV)
- **Query Params:** `return_csv` (boolean, optional)

### ✅ POST `/predict_batch_csv`
- **Purpose:** Alias for batch prediction with CSV download
- **Auth:** Required
- **Request:** Multipart form-data with CSV file
- **Response:** CSV file (downloadable)

### ✅ GET `/api-key/status`
- **Purpose:** Check current API key usage
- **Auth:** Required API key
- **Response:** JSON with usage statistics

---

## 2. THE `/predict` ENDPOINT - COMPLETE SPECIFICATION

### REQUEST SCHEMA: `PredictionRequest`

#### Top-Level Fields

```json
{
  "phase": "Phase II",
  "indication": "Alzheimer's Disease",
  "trial_design": { ... },
  "endpoints": { ... },
  "biomarkers": { ... },
  "enrollment": { ... },
  "biomarker_enrichment_strategy": "at_positive"
}
```

### 2.1 TRIAL DESIGN SECTION (`trial_design`)

| Field | Type | Required | Validation | Example | Notes |
|-------|------|----------|-----------|---------|-------|
| `trial_sample_size` | integer | ✅ YES | > 0 | `200` | Number of participants |
| `trial_duration_weeks` | integer | ✅ YES | > 0 | `52` | Duration in weeks |
| `phase` | string | ❌ NO | Any string | `"Phase II"` | Optional trial phase |
| `indication` | string | ❌ NO | Any string | `"Alzheimer's Disease"` | Disease being studied |
| `number_of_arms` | integer | ❌ NO | >= 1 | `2` | Number of treatment arms |
| `randomization_ratio` | string | ❌ NO | Any string | `"1:1"` | Randomization scheme |

**Required Nested Object:** `trial_design` itself is REQUIRED

---

### 2.2 ENDPOINTS SECTION (`endpoints`)

| Field | Type | Required | Validation | Example | Notes |
|-------|------|----------|-----------|---------|-------|
| `endpoint_type` | string | ✅ YES | 'objective' \| 'subjective' \| 'mixed' | `"objective"` | **Case-insensitive** |
| `primary_endpoint_name` | string | ✅ YES | Any string | `"CDR-SB"` | Specific endpoint measure |

**Valid endpoint_type values (backend enforces lowercase):**
- `objective` - objective/measurable endpoint
- `subjective` - subjective/clinician-rated endpoint
- `mixed` - combination of both

**Common primary_endpoint_name values:**
- `CDR-SB` - Clinical Dementia Rating Scale (preferred for AD)
- `ADAS-Cog` - Alzheimer's Disease Assessment Scale
- `MMSE` - Mini-Mental State Examination
- `ADCOMS` - AD Composite Score
- Other free-form strings accepted

---

### 2.3 BIOMARKERS SECTION (`biomarkers`)

**ALL FIELDS OPTIONAL** — Model handles missing values gracefully

#### Binary Biomarkers (0 or 1)

| Field | Type | Range | Meaning | Example |
|-------|------|-------|---------|---------|
| `apoe_e4_carrier` | int | 0 \| 1 | 1 = ≥1 ε4 allele | `1` |
| `apoe_e4_homozygous` | int | 0 \| 1 | 1 = e4/e4 genotype | `1` |
| `ptau217_high` | int | 0 \| 1 | 1 if > 14.5 pg/mL | `1` |
| `csf_abeta42_40_ratio_low` | int | 0 \| 1 | 1 if < 0.5 | `0` |
| `csf_ptau_elevated` | int | 0 \| 1 | 1 if > 79 pg/mL | `1` |
| `amyloid_pet_positive` | int | 0 \| 1 | 1 if SUVR > 1.2 | `1` |
| `tau_pet_positive` | int | 0 \| 1 | 1 if SUVR > 1.3 | `0` |
| `hippocampal_atrophy_binary` | int | 0 \| 1 | 1 if < 10th percentile | `1` |

#### Continuous Biomarkers (floats)

| Field | Type | Unit | Example | Notes |
|-------|------|------|---------|-------|
| `ptau217_continuous` | float | pg/mL | `18.5` | Raw plasma p-tau217 value |
| `csf_abeta42_40_ratio_continuous` | float | ratio | `0.45` | Raw CSF Aβ42/Aβ40 ratio |
| `hippocampal_atrophy_mri` | float | mm³ | `3200.0` | Hippocampal volume |

**Missing Biomarker Handling:**
- Omitted fields → filled with 0 (for binary) or mean value (for continuous)
- null values → treated as missing
- Empty strings → treated as missing

---

### 2.4 ENROLLMENT SECTION (`enrollment`)

| Field | Type | Required | Validation | Example | Notes |
|-------|------|----------|-----------|---------|-------|
| `age_mean` | float | ✅ YES | Any positive number | `72.5` | Mean age of cohort (years) |
| `baseline_mmse` | float | ❌ NO | 0-30 | `22.0` | Mini-Mental State Exam score |
| `baseline_moca` | float | ❌ NO | 0-30 | `25.0` | Montreal Cognitive Assessment |
| `cdr_baseline` | float | ❌ NO | 0-18 | `1.5` | Clinical Dementia Rating |

**Required Nested Object:** `enrollment` itself is REQUIRED (must have age_mean)

---

### 2.5 BIOMARKER ENRICHMENT STRATEGY (Top-Level)

| Field | Type | Required | Valid Values | Example |
|-------|------|----------|--------------|---------|
| `biomarker_enrichment_strategy` | string | ❌ NO | `"amyloid_positive"`, `"tau_positive"`, `"at_positive"`, `"cognitive_only"`, `"none"`, `"unknown"` | `"at_positive"` |

**Backend behavior:** If omitted or null, defaults to `"unknown"` during feature engineering.

---

### 2.6 EXAMPLE COMPLETE REQUEST

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
    "amyloid_pet_positive": 1,
    "tau_pet_positive": 0,
    "hippocampal_atrophy_binary": 1
  },
  "enrollment": {
    "age_mean": 72.5,
    "baseline_mmse": 22.0,
    "baseline_moca": 19.0,
    "cdr_baseline": 1.5
  },
  "biomarker_enrichment_strategy": "at_positive"
}
```

---

## 3. THE `/predict` RESPONSE - COMPLETE SPECIFICATION

### RESPONSE SCHEMA: `PredictionResponse`

```json
{
  "trial_success_probability": 0.72,
  "risk_tier": "LOW",
  "top_drivers": [
    {
      "feature_name": "trial_sample_size",
      "coefficient": 1.422,
      "direction": "positive",
      "impact_magnitude": 1.422
    },
    {
      "feature_name": "age_mean",
      "coefficient": -0.845,
      "direction": "negative",
      "impact_magnitude": 0.845
    }
  ],
  "biomarker_explanation": "This trial enrolls participants with amyloid PET positive and elevated plasma p-tau217 biomarker profile...",
  "confidence_flag": "HIGH",
  "missing_biomarker_count": 0,
  "model_version": "v1.0",
  "generated_timestamp": "2026-06-02T10:30:45.123456Z"
}
```

### RESPONSE FIELDS

| Field | Type | Range | Meaning |
|-------|------|-------|---------|
| `trial_success_probability` | float | 0.0-1.0 | Probability trial will succeed (0 = will fail, 1 = will succeed) |
| `risk_tier` | string | "LOW" \| "MEDIUM" \| "HIGH" | Risk categorization based on probability |
| `top_drivers` | array | 5 items | Top 5 most influential features in prediction |
| `biomarker_explanation` | string | Any | Natural language explanation of drivers |
| `confidence_flag` | string | "HIGH" \| "MEDIUM" \| "LOW" | Data completeness confidence |
| `missing_biomarker_count` | int | 0-11 | Count of missing required biomarkers |
| `model_version` | string | "v1.0" | ML model version identifier |
| `generated_timestamp` | string | ISO 8601 | UTC timestamp of prediction |

### RISK TIER MAPPING

| Tier | Probability Range | Interpretation |
|------|------------------|-----------------|
| **LOW** | ≥ 0.70 | High likelihood of success |
| **MEDIUM** | 0.40 - 0.69 | Moderate/uncertain outcome |
| **HIGH** | < 0.40 | High failure risk |

### CONFIDENCE FLAG ASSESSMENT

| Flag | Missing Count | Data Completeness |
|------|---|---|
| **HIGH** | 0 | All 11 required biomarkers present |
| **MEDIUM** | 1-2 | Missing 1-2 biomarkers |
| **LOW** | 3+ | Missing 3+ required biomarkers |

**Required Biomarkers (for confidence assessment):**
1. apoe_e4_carrier
2. ptau217_high
3. amyloid_pet_positive
4. age_mean
5. baseline_mmse
6. cdr_baseline
7. trial_sample_size
8. trial_duration_weeks
9. endpoint_type
10. primary_endpoint_name
11. biomarker_enrichment_strategy

---

## 4. FEATURE ENGINEERING PIPELINE

### What the Model Expects (Internal)

The `/predict` endpoint internally transforms the request JSON into **29 engineered features** after one-hot encoding:

#### Base Features (22)
```
Biomarkers (11):
- apoe_e4_carrier
- apoe_e4_homozygous
- ptau217_continuous
- ptau217_high
- csf_abeta42_40_ratio_continuous
- csf_abeta42_40_ratio_low
- csf_ptau_elevated
- amyloid_pet_positive
- tau_pet_positive
- hippocampal_atrophy_mri
- hippocampal_atrophy_binary

Enrollment (4):
- age_mean
- baseline_mmse
- baseline_moca
- cdr_baseline

Trial Design (6):
- trial_sample_size
- trial_duration_weeks
- number_of_arms
- endpoint_type (categorical → one-hot)
- primary_endpoint_name (categorical → one-hot)
- biomarker_enrichment_strategy (categorical → one-hot)
```

#### One-Hot Encoding

**endpoint_type** (2 features, drop_first=True):
- `endpoint_type_objective` (1 if objective, 0 otherwise)
- `endpoint_type_subjective` (1 if subjective, implicit 0 for mixed)

**primary_endpoint_name** (3 features):
- `primary_endpoint_name_ADCOMS`
- `primary_endpoint_name_CDR-SB`
- `primary_endpoint_name_MMSE`
- (Other values encoded as all zeros)

**biomarker_enrichment_strategy** (4 features):
- `biomarker_enrichment_strategy_at_positive`
- `biomarker_enrichment_strategy_cognitive_only`
- `biomarker_enrichment_strategy_none`
- `biomarker_enrichment_strategy_tau_positive`

**randomization_ratio** (2 features):
- `randomization_ratio_2:1`
- `randomization_ratio_open_label`

---

## 5. FIELD-BY-FIELD FRONTEND INTEGRATION SPECIFICATION

### Core Input Schema for Frontend

```javascript
{
  "phase": {
    "type": "string",
    "required": false,
    "example": "Phase II",
    "description": "Trial phase (optional)"
  },
  "indication": {
    "type": "string",
    "required": false,
    "example": "Alzheimer's Disease",
    "description": "Disease indication (optional)"
  },
  
  // TRIAL DESIGN (REQUIRED SECTION)
  "trial_design": {
    "trial_sample_size": {
      "type": "integer",
      "required": true,
      "min": 1,
      "example": 200,
      "description": "Number of trial participants"
    },
    "trial_duration_weeks": {
      "type": "integer",
      "required": true,
      "min": 1,
      "example": 52,
      "description": "Trial duration in weeks"
    },
    "number_of_arms": {
      "type": "integer",
      "required": false,
      "min": 1,
      "example": 2,
      "description": "Number of treatment arms"
    },
    "randomization_ratio": {
      "type": "string",
      "required": false,
      "example": "1:1",
      "description": "e.g., '1:1', '2:1', 'open_label'"
    }
  },
  
  // ENDPOINTS (REQUIRED SECTION)
  "endpoints": {
    "endpoint_type": {
      "type": "string",
      "required": true,
      "enum": ["objective", "subjective", "mixed"],
      "example": "objective",
      "description": "Type of endpoint (case-insensitive)"
    },
    "primary_endpoint_name": {
      "type": "string",
      "required": true,
      "example": "CDR-SB",
      "description": "Specific endpoint measure"
    }
  },
  
  // BIOMARKERS (OPTIONAL, ALL FIELDS)
  "biomarkers": {
    "apoe_e4_carrier": {
      "type": "integer",
      "required": false,
      "enum": [0, 1],
      "example": 1
    },
    "apoe_e4_homozygous": {
      "type": "integer",
      "required": false,
      "enum": [0, 1]
    },
    "ptau217_high": {
      "type": "integer",
      "required": false,
      "enum": [0, 1],
      "example": 1
    },
    "ptau217_continuous": {
      "type": "number",
      "required": false,
      "unit": "pg/mL",
      "example": 18.5
    },
    "csf_abeta42_40_ratio_low": {
      "type": "integer",
      "required": false,
      "enum": [0, 1]
    },
    "csf_abeta42_40_ratio_continuous": {
      "type": "number",
      "required": false,
      "example": 0.45
    },
    "csf_ptau_elevated": {
      "type": "integer",
      "required": false,
      "enum": [0, 1]
    },
    "amyloid_pet_positive": {
      "type": "integer",
      "required": false,
      "enum": [0, 1],
      "example": 1
    },
    "tau_pet_positive": {
      "type": "integer",
      "required": false,
      "enum": [0, 1]
    },
    "hippocampal_atrophy_mri": {
      "type": "number",
      "required": false,
      "unit": "mm³",
      "example": 3200.0
    },
    "hippocampal_atrophy_binary": {
      "type": "integer",
      "required": false,
      "enum": [0, 1]
    }
  },
  
  // ENROLLMENT (REQUIRED SECTION)
  "enrollment": {
    "age_mean": {
      "type": "number",
      "required": true,
      "example": 72.5,
      "description": "Mean age in years"
    },
    "baseline_mmse": {
      "type": "number",
      "required": false,
      "min": 0,
      "max": 30,
      "example": 22.0
    },
    "baseline_moca": {
      "type": "number",
      "required": false,
      "min": 0,
      "max": 30
    },
    "cdr_baseline": {
      "type": "number",
      "required": false,
      "min": 0,
      "max": 18,
      "example": 1.5
    }
  },
  
  // ENRICHMENT STRATEGY (TOP-LEVEL, OPTIONAL)
  "biomarker_enrichment_strategy": {
    "type": "string",
    "required": false,
    "enum": ["amyloid_positive", "tau_positive", "at_positive", "cognitive_only", "none"],
    "example": "at_positive"
  }
}
```

---

## 6. REQUIRED FIELDS SUMMARY

### Absolutely Required for Prediction
```
✅ trial_design.trial_sample_size (int > 0)
✅ trial_design.trial_duration_weeks (int > 0)
✅ endpoints.endpoint_type (str: objective|subjective|mixed)
✅ endpoints.primary_endpoint_name (str)
✅ enrollment.age_mean (float)
```

### Optional Fields That Improve Confidence
```
⭐ apoe_e4_carrier (0/1)
⭐ ptau217_high (0/1)
⭐ amyloid_pet_positive (0/1)
⭐ baseline_mmse (0-30)
⭐ cdr_baseline (0-18)
⭐ biomarker_enrichment_strategy (str)
```

### Everything Else
```
❌ All other biomarkers optional
❌ trial_design.number_of_arms optional
❌ trial_design.randomization_ratio optional
❌ enrollment.baseline_moca optional
❌ phase optional
❌ indication optional
```

---

## 7. ERROR HANDLING SPECIFICATION

### HTTP Status Codes

| Code | Scenario | Example Error Message |
|------|----------|---------------------|
| **200** | Success | Returns PredictionResponse |
| **400** | Missing required fields | "Missing required fields: trial_design, endpoints, biomarkers, enrollment" |
| **400** | Invalid JSON | "Invalid endpoint_type must be one of {'objective', 'subjective', 'mixed'}" |
| **401** | Invalid/missing API key | "Invalid or inactive API key" (only in production) |
| **429** | Rate limit exceeded | "Monthly request limit exceeded" |
| **500** | Model error | "Model prediction failed: ..." |
| **500** | Internal error | "An unexpected error occurred during prediction" |

### Example Error Response (400)

```json
{
  "error": "validation error",
  "message": "Missing required field: trial_sample_size",
  "status_code": 400,
  "timestamp": "2026-06-02T10:30:45Z"
}
```

---

## 8. MISMATCHES & ISSUES IDENTIFIED

### ✅ NO CRITICAL MISMATCHES FOUND

Backend contract is clean and well-defined. However, note:

| Issue | Details | Frontend Impact |
|-------|---------|-----------------|
| No JSON Schema exposed | API doesn't provide JSON Schema endpoint | Frontend must manually build form from this spec |
| Optional API key | Works in dev mode (ENV=dev) but required in production | Frontend won't get 401 errors in local dev |
| CSV batch endpoint requires API key | Single /predict is optional, but /predict_batch requires key | Batch uploads need auth header |
| One-hot encoding hidden | Frontend sends categorical strings, backend handles encoding | Frontend doesn't need to worry about this |
| Feature defaults | Missing features default to 0 | Safe to omit optional fields |

---

## 9. MODEL LOADING & VERIFICATION

### Backend Initialization (on startup)

```python
# Located: Models/predict_trial.py
ARTIFACT_DIR = "models/artifacts"
MODEL_PATH = os.path.join(ARTIFACT_DIR, "logistic_model.pkl")
SCALER_PATH = os.path.join(ARTIFACT_DIR, "feature_scaler.pkl")
```

### Model Artifacts Required

```
models/artifacts/
├── logistic_model.pkl      (trained sklearn LogisticRegression)
└── feature_scaler.pkl      (fitted StandardScaler)
```

### If Missing

```
FileNotFoundError: Model not found at models/artifacts/logistic_model.pkl
```

**Frontend Impact:** API will crash on startup. Check logs if 500 errors occur on first prediction.

---

## 10. FRONTEND REQUIREMENTS FOR SUCCESSFUL PREDICTION REQUESTS

### Minimum Viable Request (MVP)

```json
{
  "trial_design": {
    "trial_sample_size": 200,
    "trial_duration_weeks": 52
  },
  "endpoints": {
    "endpoint_type": "objective",
    "primary_endpoint_name": "CDR-SB"
  },
  "biomarkers": {},
  "enrollment": {
    "age_mean": 72.5
  }
}
```

**Result:** Returns prediction with LOW confidence (missing 10 biomarkers)

### Typical Request (Good Confidence)

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
    "ptau217_high": 1,
    "amyloid_pet_positive": 1,
    "hippocampal_atrophy_binary": 1
  },
  "enrollment": {
    "age_mean": 72.5,
    "baseline_mmse": 22.0,
    "cdr_baseline": 1.5
  },
  "biomarker_enrichment_strategy": "at_positive"
}
```

**Result:** Returns prediction with HIGH confidence

---

## 11. INTEGRATION CHECKLIST: Frontend Requirements for Successful Prediction Requests

### ✅ REQUIRED FORM FIELDS

**Trial Design Section:**
- [ ] `trial_sample_size` (text input, type="number", min=1)
- [ ] `trial_duration_weeks` (text input, type="number", min=1)
- [ ] `number_of_arms` (text input, type="number", optional)
- [ ] `randomization_ratio` (text input, optional)
- [ ] `phase` (text input, optional)
- [ ] `indication` (text input, optional)

**Endpoints Section:**
- [ ] `endpoint_type` (select/dropdown: objective, subjective, mixed) **REQUIRED**
- [ ] `primary_endpoint_name` (text input or select) **REQUIRED**

**Biomarkers Section (All Optional):**
- [ ] `apoe_e4_carrier` (checkbox or toggle: 0/1)
- [ ] `apoe_e4_homozygous` (checkbox or toggle: 0/1)
- [ ] `ptau217_high` (checkbox or toggle: 0/1)
- [ ] `ptau217_continuous` (text input, type="number")
- [ ] `csf_abeta42_40_ratio_low` (checkbox or toggle: 0/1)
- [ ] `csf_abeta42_40_ratio_continuous` (text input, type="number")
- [ ] `csf_ptau_elevated` (checkbox or toggle: 0/1)
- [ ] `amyloid_pet_positive` (checkbox or toggle: 0/1)
- [ ] `tau_pet_positive` (checkbox or toggle: 0/1)
- [ ] `hippocampal_atrophy_mri` (text input, type="number")
- [ ] `hippocampal_atrophy_binary` (checkbox or toggle: 0/1)

**Enrollment Section:**
- [ ] `age_mean` (text input, type="number") **REQUIRED**
- [ ] `baseline_mmse` (text input, type="number", min=0, max=30)
- [ ] `baseline_moca` (text input, type="number", min=0, max=30)
- [ ] `cdr_baseline` (text input, type="number", min=0, max=18)

**Enrichment Strategy:**
- [ ] `biomarker_enrichment_strategy` (select: amyloid_positive, tau_positive, at_positive, cognitive_only, none)

### ✅ REQUIRED JAVASCRIPT FUNCTIONS

- [ ] `validateFormData()` - Check required fields before submit
- [ ] `buildRequestJSON()` - Construct JSON matching PredictionRequest schema
- [ ] `sendPredictionRequest()` - POST to http://127.0.0.1:8000/predict
- [ ] `handlePredictionResponse()` - Parse PredictionResponse and display results
- [ ] `handlePredictionError()` - Handle errors with user-friendly messages
- [ ] `renderResults()` - Display probability, risk tier, drivers, confidence

### ✅ REQUIRED ERROR HANDLING

- [ ] Check if API is reachable before submit (health check)
- [ ] Display validation errors for required fields
- [ ] Display server errors (400, 500) with messages
- [ ] Show loading indicator while awaiting response
- [ ] Handle network timeouts (30-second max)
- [ ] Display "API Unavailable" message if server unreachable

### ✅ REQUIRED RESPONSE RENDERING

- [ ] **trial_success_probability:** Display as percentage (0-100%)
- [ ] **risk_tier:** Color-code (GREEN=LOW, YELLOW=MEDIUM, RED=HIGH)
- [ ] **top_drivers:** Show top 5 features with names and impact direction
- [ ] **biomarker_explanation:** Display as readable text block
- [ ] **confidence_flag:** Show confidence level (HIGH/MEDIUM/LOW)
- [ ] **missing_biomarker_count:** Display count of missing data points

### ✅ REQUIRED API COMPATIBILITY

- [ ] Support CORS requests (API has CORS enabled, no auth needed)
- [ ] Send JSON with `Content-Type: application/json`
- [ ] Accept 200 status code as success
- [ ] Handle 400/500 status codes as errors
- [ ] No authentication required for /predict endpoint (dev mode)
- [ ] Optional: Store API key in localStorage for future use

### ✅ REQUIRED TEST CASES

- [ ] Submit with minimum required fields only → Should return LOW confidence
- [ ] Submit with all fields populated → Should return HIGH confidence
- [ ] Omit trial_sample_size → Should show error
- [ ] Omit endpoints.endpoint_type → Should show error
- [ ] Omit enrollment.age_mean → Should show error
- [ ] Invalid endpoint_type value → Should show validation error
- [ ] Network timeout (mock with delay) → Should show timeout message
- [ ] Server returns 500 → Should display error message

---

**Audit Completed:** June 2, 2026  
**API Version:** 1.0.0  
**Model Version:** v1.0  
**Status:** Ready for Frontend Integration ✅
