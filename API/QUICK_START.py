"""
Quick start guide and troubleshooting for Genivra API.

This file demonstrates the fastest path from zero to running predictions.
"""

# ============================================================================
# ABSOLUTE QUICKEST START (5 minutes)
# ============================================================================

"""
Step 1: Install FastAPI and dependencies (30 seconds)
----------------------------------------------------
From your project root directory:

    pip install fastapi uvicorn


Step 2: Run the API (10 seconds)
-------------------------------
From your project root directory:

    uvicorn API.main:app --reload

You should see:
    INFO:     Uvicorn running on http://127.0.0.1:8000
    INFO:     Application startup complete


Step 3: Test it works (20 seconds)
----------------------------------
In another terminal, run:

    python API/example_usage.py

Or manually test with curl:

    curl -X POST "http://localhost:8000/predict" \
      -H "Content-Type: application/json" \
      -d '{
        "trial_design": {"trial_sample_size": 200, "trial_duration_weeks": 52},
        "endpoints": {"endpoint_type": "objective", "primary_endpoint_name": "CDR-SB"},
        "biomarkers": {"apoe_e4_carrier": 1, "ptau217_high": 1, "amyloid_pet_positive": 1},
        "enrollment": {"age_mean": 72.5, "baseline_mmse": 22.0, "cdr_baseline": 1.5}
      }'

Expected response:
    {
      "trial_success_probability": 0.958,
      "risk_tier": "LOW",
      "confidence_flag": "HIGH",
      ...
    }


Step 4: View Auto-Generated Docs (10 seconds)
--------------------------------------------
Open your browser to:
    http://localhost:8000/docs

You can test API endpoints directly from here!
"""


# ============================================================================
# PROPER SETUP WITH REQUIREMENTS (2 minutes)
# ============================================================================

"""
Step 1: Install all required packages
-------------------------------------
From project root:

    pip install -r requirements.txt

This installs:
  - fastapi (API framework)
  - uvicorn (ASGI server)
  - pydantic (validation)
  - scikit-learn (ML model)
  - numpy, pandas (data handling)
  - pytest (testing)


Step 2: Run the server
---------------------
    uvicorn API.main:app --reload --host 0.0.0.0 --port 8000

Options:
  --reload      Auto-restart on code changes (development)
  --host        Listen on this IP (0.0.0.0 = all interfaces)
  --port        Use this port (default 8000)
  --log-level   Set log level (info, debug, error)


Step 3: Run test suite
---------------------
    pytest API/test_api.py -v

This validates:
  - All endpoints work
  - Input validation works
  - Error handling works
  - Output format is correct


Step 4: Try the example client
------------------------------
    python API/example_usage.py

This tests:
  - High-success scenario (Lecanemab-like)
  - High-risk scenario
  - Error handling
"""


# ============================================================================
# MINIMAL EXAMPLE in Python
# ============================================================================

MINIMAL_PYTHON_EXAMPLE = """
import requests
import json

# Define your trial
trial = {
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

# Call the API
response = requests.post("http://localhost:8000/predict", json=trial)
result = response.json()

# Print results
print(f"Success Probability: {result['trial_success_probability']:.1%}")
print(f"Risk Tier: {result['risk_tier']}")
print(f"Confidence: {result['confidence_flag']}")
"""


# ============================================================================
# COMMON PROBLEMS & SOLUTIONS
# ============================================================================

TROUBLESHOOTING = """
PROBLEM 1: ModuleNotFoundError: No module named 'Models'
--------
ERROR:
    ModuleNotFoundError: No module named 'Models'

SOLUTION:
    You must run uvicorn from the PROJECT ROOT (Genivra.ai directory):
    
    cd /path/to/Genivra.ai
    uvicorn API.main:app --reload
    
    NOT from the API directory.


PROBLEM 2: Connection refused / Address already in use
--------
ERROR:
    Error: Address already in use
    Connection refused

SOLUTION 1 (Change port):
    uvicorn API.main:app --port 8001

SOLUTION 2 (Kill existing process):
    # On Mac/Linux:
    lsof -i :8000
    kill -9 <PID>
    
    # On Windows:
    netstat -ano | findstr :8000
    taskkill /PID <PID> /F


PROBLEM 3: ModuleNotFoundError: No module named 'fastapi'
--------
ERROR:
    ModuleNotFoundError: No module named 'fastapi'

SOLUTION:
    Install requirements:
    
    pip install -r requirements.txt
    
    Or install manually:
    
    pip install fastapi uvicorn pydantic scikit-learn numpy pandas


PROBLEM 4: Prediction returns error or empty result
--------
ERROR:
    "error": "Model prediction failed"
    HTTP 500

SOLUTION:
    Check that model artifacts exist:
    
    ls models/artifacts/
    
    You should see:
    - logistic_model.pkl
    - feature_scaler.pkl
    
    If missing, you need to run:
    
    python Scripts/run_train.py


PROBLEM 5: CORS errors from frontend
--------
ERROR:
    Access to XMLHttpRequest blocked by CORS policy
    No 'Access-Control-Allow-Origin' header

SOLUTION:
    CORS is already enabled in API/main.py for development.
    
    If issue persists, check your frontend is using correct URL:
    - http://localhost:8000 (not http://localhost:3000, etc.)
    - POST /predict (not /api/predict)


PROBLEM 6: API works but predictions seem wrong
--------
ERROR:
    Success probability always high/low regardless of input

SOLUTION:
    1. Check that inputs are correct type
       - age_mean: number
       - trial_sample_size: integer
       - biomarkers: 0, 1, or null
    
    2. Check confidence level
       - If "LOW", model has missing required biomarkers
       - Add more biomarkers for better predictions
    
    3. Run test suite
       pytest API/test_api.py -v


PROBLEM 7: Tests fail or hang
--------
ERROR:
    test_valid_prediction FAILED
    test_minimal_request hangs
    
SOLUTION:
    Make sure API is NOT running in another terminal.
    TestClient creates its own test server.
    
    Kill any running uvicorn instances:
    
    pkill -f uvicorn
    
    Then run tests:
    
    pytest API/test_api.py -v
"""


# ============================================================================
# FILE REFERENCE
# ============================================================================

FILE_REFERENCE = """
NEW FILES CREATED FOR THE API
=============================

API/
├── main.py
│   └── FastAPI application with endpoints
│       - GET / (health check)
│       - GET /health (status)
│       - POST /predict (main prediction endpoint)
│       - Includes CORS, logging, error handling
│
├── models.py
│   └── Pydantic models for validation
│       - PredictionRequest (input schema)
│       - PredictionResponse (output schema)
│       - BiomarkerInput, TrialDesignInput, EndpointInput, etc.
│
├── __init__.py
│   └── Package initialization
│
├── test_api.py
│   └── Pytest test suite (40+ tests)
│       - Health check tests
│       - Prediction tests
│       - Input validation tests
│       - Error handling tests
│
├── example_usage.py
│   └── Python client demonstrating API usage
│       - Tests health endpoint
│       - Runs 2 example predictions
│       - Shows how to parse responses
│
├── API_DOCUMENTATION.md
│   └── Complete API documentation
│       - Endpoint reference
│       - Input/output schemas
│       - Examples and error codes
│       - Deployment instructions
│
├── README.md
│   └── API package overview
│       - Quick start
│       - Testing instructions
│       - Integration examples
│
└── QUICK_START.py (THIS FILE)
    └── Quick reference and troubleshooting


UPDATED FILES
=============

requirements.txt
└── New file with all dependencies
    - fastapi, uvicorn (API)
    - pydantic (validation)
    - scikit-learn, numpy, pandas (ML)
    - pytest (testing)
    - gunicorn (production)
"""


# ============================================================================
# WORKFLOW: FROM ZERO TO PRODUCTION
# ============================================================================

WORKFLOW = """
DEVELOPMENT (5-10 minutes)
==========================

1. Install: pip install -r requirements.txt
2. Run: uvicorn API.main:app --reload
3. Test: python API/example_usage.py
4. Check docs: http://localhost:8000/docs


TESTING (2 minutes)
===================

1. Run test suite: pytest API/test_api.py -v
2. Check coverage: pytest API/test_api.py --cov=API
3. All should pass


INTEGRATION (varies)
====================

JavaScript/React:
    fetch('http://localhost:8000/predict', {
        method: 'POST',
        body: JSON.stringify(trial)
    })

Python:
    requests.post('http://localhost:8000/predict', json=trial)

cURL:
    curl -X POST http://localhost:8000/predict -d @trial.json

Other languages:
    Any HTTP client can call the API (REST standard)


PRODUCTION (30 minutes)
=======================

1. Install gunicorn: pip install gunicorn
2. Run: gunicorn -w 4 -k uvicorn.workers.UvicornWorker API.main:app
3. Set up load balancer (optional)
4. Monitor health: curl http://localhost:8000/health
5. Enable CORS for specific domains (remove allow_origins=["*"])
6. Set up logging to file and monitoring


SCALING (varies)
================

Single container: Run single API instance above
Multiple containers: Deploy 2-4 instances behind load balancer
Kubernetes: Package as Docker image, deploy to K8s
Serverless: Deploy to AWS Lambda, Google Cloud Functions, etc.
"""


# ============================================================================
# KEY CONCEPTS
# ============================================================================

CONCEPTS = """
REQUEST STRUCTURE
=================

{
  "trial_design": {           ← Trial enrollment & duration
    "trial_sample_size": 200,
    "trial_duration_weeks": 52,
    ...
  },
  "endpoints": {              ← How success is measured
    "endpoint_type": "objective",
    "primary_endpoint_name": "CDR-SB"
  },
  "biomarkers": {             ← Patient biology markers (optional)
    "apoe_e4_carrier": 1,
    "ptau217_high": 1,
    ...
  },
  "enrollment": {             ← Patient baseline characteristics
    "age_mean": 72.5,
    "baseline_mmse": 22.0,
    ...
  },
  "biomarker_enrichment_strategy": "at_positive"  ← Patient selection
}


RESPONSE STRUCTURE
==================

{
  "trial_success_probability": 0.958,    ← SUCCESS METRIC (0-1)
  "risk_tier": "LOW",                    ← RISK CATEGORY
  "top_drivers": [                       ← WHAT MATTERS
    {
      "feature_name": "amyloid_pet_positive",
      "coefficient": 2.845,
      "direction": "positive",
      "impact_magnitude": 2.845
    },
    ...
  ],
  "biomarker_explanation": "...",       ← EXPLAINABILITY
  "confidence_flag": "HIGH",             ← DATA QUALITY
  "missing_biomarker_count": 0
}


KEY OUTPUTS
===========

1. trial_success_probability
   - 0.0 = will fail
   - 1.0 = will succeed
   - 0.5 = coin flip

2. risk_tier
   - LOW (≥70% success)
   - MEDIUM (40-69% success)
   - HIGH (<40% success)

3. top_drivers
   - Top 5 factors influencing outcome
   - Ranked by impact magnitude
   - Positive = helps success
   - Negative = hurts success

4. biomarker_explanation
   - Plain English summary
   - Why this trial will succeed/fail
   - Which biomarkers matter most

5. confidence_flag
   - HIGH = all required biomarkers present
   - MEDIUM = 1-2 missing
   - LOW = >2 missing
"""


# ============================================================================
# NEXT STEPS
# ============================================================================

NEXT_STEPS = """
IMMEDIATE (Do now)
==================
[ ] 1. Run: pip install -r requirements.txt
[ ] 2. Run: uvicorn API.main:app --reload
[ ] 3. Visit: http://localhost:8000/docs
[ ] 4. Run: python API/example_usage.py


SHORT TERM (Next 2-4 weeks)
===========================
[ ] Build web dashboard (HTML form → /predict endpoint)
[ ] Add database to store predictions
[ ] Add authentication/API keys for Tier 2+ customers
[ ] Set up payment processing (Stripe)
[ ] Create customer onboarding flow


MEDIUM TERM (Weeks 4-12)
========================
[ ] Deploy to production (Render, Railway, AWS)
[ ] Add real trial data (ClinicalTrials.gov integration)
[ ] Validate predictions on real trial outcomes
[ ] Build customer dashboard
[ ] Create customer success playbook


LONG TERM (Months 3-6)
======================
[ ] Expand to other phases (Phase III)
[ ] Add more indications (ALS, Parkinson's, etc.)
[ ] Build proprietary dataset
[ ] Achieve $300K+ ARR
[ ] Prepare for acquisition
"""


# ============================================================================
# PRINT ALL GUIDES
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("GENIVRA API QUICK START GUIDE")
    print("=" * 80)
    
    print("\n" + "◆" * 40)
    print("5-MINUTE QUICKSTART")
    print("◆" * 40)
    print(globals()["MINIMAL_PYTHON_EXAMPLE"])
    
    print("\n" + "◆" * 40)
    print("FILE REFERENCE")
    print("◆" * 40)
    print(FILE_REFERENCE)
    
    print("\n" + "◆" * 40)
    print("TROUBLESHOOTING")
    print("◆" * 40)
    print(TROUBLESHOOTING)
    
    print("\n" + "◆" * 40)
    print("KEY CONCEPTS")
    print("◆" * 40)
    print(CONCEPTS)
    
    print("\n" + "◆" * 40)
    print("NEXT STEPS")
    print("◆" * 40)
    print(NEXT_STEPS)
    
    print("\n" + "=" * 80)
    print("Ready? Run: uvicorn API.main:app --reload")
    print("Then visit: http://localhost:8000/docs")
    print("=" * 80 + "\n")
