# 🔍 GENIVRA PROJECT - COMPLETE DEEP DIVE ANALYSIS
**Current Date:** May 28, 2026  
**Current Branch:** andrew_dev2  
**Project Status:** In Development (Frontend ↔ Backend Integration Phase)

---

## 📊 EXECUTIVE SUMMARY

**Genivra** is an AI-powered clinical trial success prediction engine for neurological indications (primarily Alzheimer's Disease). It predicts whether a Phase II trial will advance to Phase III or meet its primary endpoint using biomarker data, trial design parameters, and patient enrollment characteristics.

**Current State:** Backend API is production-ready; Frontend is partially integrated; Frontend-to-Backend connection needs completion.

---

## 🏗️ PROJECT ARCHITECTURE

### Overall Data Flow
```
User Input (Frontend) 
    ↓
REST API (/predict endpoint)
    ↓
Input Validation & Feature Engineering
    ↓
Trained Logistic Regression Model
    ↓
Structured JSON Response
    ↓
Display Results (Frontend)
```

---

## 📁 COMPLETE FOLDER STRUCTURE & PURPOSE

### ROOT LEVEL FILES
| File | Purpose |
|------|---------|
| `README.md` | Project overview & quick start guide |
| `requirements.txt` | Python dependencies (FastAPI, sklearn, pandas, numpy, etc.) |
| `Dockerfile` | Docker containerization for deployment |
| `docker-compose.yml` | Docker Compose configuration |
| `Procfile` | Heroku deployment configuration |
| `runtime.txt` | Python version specification (Heroku) |
| `DEPLOYMENT.md` | Full deployment guide (local, Docker, Heroku) |
| `CONTRIBUTING.md` | Contribution guidelines |
| `LICENSE` | License file |
| `ML_SCOPE.md` | ML project scope & success metrics |
| `run_api_tests.py` | Script to run API tests |

---

## 🎯 FOLDER BREAKDOWN

### `API/` - REST API Backend
**Status:** ✅ Production Ready

| File | Purpose |
|------|---------|
| `main.py` | FastAPI application with all endpoints |
| `models.py` | Pydantic validation schemas (request/response) |
| `auth.py` | API key management & rate limiting |
| `config.py` | Environment configuration & settings |
| `flask_app.py` | Legacy Flask wrapper (lightweight endpoint) |
| `example_usage.py` | Example API client code |
| `test_api.py` | Pytest test suite for API |
| `README.md` | API documentation |

**Key Endpoints:**
- `POST /predict` - Main prediction endpoint
- `GET /health` - Health check
- `GET /docs` - Interactive Swagger UI
- `GET /redoc` - ReDoc documentation
- `GET /api-key/status` - Check API key limits

**Current API Features:**
- ✅ Input validation (required fields, type checking, range validation)
- ✅ Prediction engine integration
- ✅ API key authentication & rate limiting
- ✅ CORS enabled for browser requests
- ✅ Comprehensive logging
- ✅ Error handling with structured responses
- ✅ Interactive API docs
- ✅ Support for both `x-api-key` and `Authorization: Bearer` headers

---

### `Models/` - Machine Learning Engine
**Status:** ✅ Complete & Trained

| File | Purpose |
|------|---------|
| `predict_trial.py` | Main prediction function & feature engineering |
| `train_logistic_regression.py` | Model training script |
| `rule_based_scorer.py` | Alternative rule-based scoring |
| `README.md` | Model documentation |
| `models/artifacts/logistic_model.pkl` | Trained model binary |
| `models/artifacts/feature_scaler.pkl` | Feature scaler binary |

**Model Specs:**
- **Algorithm:** Logistic Regression (binary classification)
- **Target:** Trial success probability (0-1)
- **Output:** Risk tiers (LOW/MEDIUM/HIGH)
- **Features:** 29 engineered features (including one-hot encoded categoricals)
- **Top Drivers:** Returns top 5 feature importance scores

**Feature Engineering Pipeline:**
1. Extracts 22 base features from input
2. Fills missing values (median for numerical, "unknown" for categorical)
3. One-hot encodes categorical features (endpoint_type, primary_endpoint_name, biomarker_enrichment_strategy, randomization_ratio)
4. Scales features using StandardScaler
5. Passes to logistic regression model

**Input Features (22 base):**
- Biomarkers: apoe_e4_carrier, ptau217_high, amyloid_pet_positive, tau_pet_positive, csf_abeta42_40_ratio_low, csf_ptau_elevated, hippocampal_atrophy_binary, etc.
- Trial Design: trial_sample_size, trial_duration_weeks, number_of_arms, randomization_ratio
- Endpoints: endpoint_type, primary_endpoint_name
- Enrollment: age_mean, baseline_mmse, baseline_moca, cdr_baseline
- Enrichment: biomarker_enrichment_strategy

---

### `FrontEnd/` - User Interface
**Status:** ⚠️ Partially Integrated - NEEDS WORK

**Frontend Files (3 total):**

#### 1. **`dashboard.html`** - Predictions Dashboard
- **Purpose:** Main working dashboard for viewing prediction results
- **Features:**
  - Summary table showing processed trials
  - Top drivers bar chart (Plotly)
  - Risk tier heatmap
  - Probability trend line chart
  - File upload for CSV results
  - Load from API button
- **Status:** ✅ Mostly functional
- **Integration:** Expects API running at `http://localhost:8000`
- **Video Embedded:** ❌ NO

#### 2. **`index.html`** - Marketing Landing Page
- **Purpose:** Marketing/promotional site for Genivra
- **Features:**
  - Hero section with call-to-action
  - Platform capabilities showcase
  - How-it-works section (4 steps)
  - Features grid (6 major features)
  - Impact/stats section
  - Footer with links
  - Fully responsive design
  - Gradient backgrounds & animations
- **Status:** ✅ Complete (marketing site)
- **Integration:** ❌ NO API integration
- **Video Embedded:** ❌ NO
- **Purpose:** This is a standalone marketing website, NOT the working application

#### 3. **`upload.html`** - Batch CSV Upload Tool
- **Purpose:** Upload multiple trials in CSV format for batch predictions
- **Features:**
  - CSV file upload (max 5 MB)
  - Row-by-row prediction processing
  - Results table display
  - Download results as CSV
  - Error handling per row
  - Download example CSV template
- **Status:** ✅ Functional
- **Integration:** Expects `/predict` endpoint at same origin
- **Video Embedded:** ❌ NO

**Summary of 3 Frontends:**
- `dashboard.html` - Main prediction results viewer ✅
- `index.html` - Marketing landing page (no video) ✅
- `upload.html` - Batch CSV upload tool ✅

---

### `Tests/` - Testing Suite
**Status:** ✅ Complete

| File | Purpose |
|------|---------|
| `test_predict_trial.py` | Core prediction logic tests |
| `test_flask_predict.py` | Flask API endpoint tests |
| `test_rule_based_scorer.py` | Rule-based scorer tests |
| `README.md` | Testing documentation |

**Run Tests:**
```bash
pytest Tests/                    # All tests
pytest Tests/test_predict_trial.py  # Specific file
pytest --cov=Models --cov=API Tests/  # With coverage
```

---

### `Features/` - Feature Engineering Documentation
**Status:** 📝 Documentation & Catalog

| File | Purpose |
|------|---------|
| `build_features.py` | Feature engineering utilities |
| `biomarker_feature_catalog.md` | Catalog of all biomarkers |
| `utils.py` | Helper functions |
| `README.md` | Features documentation |

---

### `Evaluation/` - ML Evaluation & Reporting
**Status:** 📊 Evaluation Tools

| File | Purpose |
|------|---------|
| `metrics.py` | Model evaluation metrics (AUC, accuracy, precision, recall, F1) |
| `plots.py` | Visualization functions (ROC, calibration, feature importance) |
| `README.md` | Evaluation documentation |

---

### `Notebooks/` - Jupyter Analysis
**Status:** 📓 Exploratory Analysis

| File | Purpose |
|------|---------|
| `01_data_exploration.ipynb` | Data exploration & descriptive stats |
| `02_feature_validation.ipynb` | Feature engineering validation |
| `03_model_prototype.ipynb` | Model prototyping & testing |
| `README.md` | Notebooks guide |

---

### `Config/` - Configuration
**Status:** 🔧 Configuration Files

| File | Purpose |
|------|---------|
| `config.yaml` | Model hyperparameters & settings |
| `logging_config.yaml` | Logging configuration |
| `README.md` | Config documentation |

---

### `Docs/` - Documentation
**Status:** 📚 Project Documentation

| File | Purpose |
|------|---------|
| `architecture.md` | High-level architecture overview |

---

## 🔄 CURRENT FRONTEND-BACKEND INTEGRATION STATUS

### ✅ WHAT'S WORKING

1. **Backend API (`API/main.py`)** - Production ready
   - FastAPI running at `http://localhost:8000`
   - Endpoints fully functional
   - Interactive docs at `/docs`
   - CORS enabled for browser requests
   - Authentication & rate limiting active

2. **Model Engine** - Fully trained
   - Logistic regression model loaded from `models/artifacts/`
   - Feature engineering pipeline complete
   - Predictions generating correctly

3. **Individual Frontend Files**
   - `dashboard.html` - Can load and render predictions
   - `upload.html` - Can upload CSV and get predictions
   - `index.html` - Marketing site complete

### ⚠️ WHAT'S BROKEN / INCOMPLETE

1. **Frontend ↔ API Connection Issue**
   - Frontends expect API at `http://localhost:8000`
   - But frontend files are served from `http://localhost:8001`
   - **CORS Origin Issue:** Browser may block requests due to port mismatch
   - **Current Workaround:** API has CORS enabled, but cross-origin issues may still occur

2. **No Unified Frontend Experience**
   - Three separate HTML files (no navigation between them)
   - No central dashboard/app shell
   - Marketing site (`index.html`) doesn't link to prediction tools
   - No consistent branding/theme across all frontend files

3. **No Batch Processing UI**
   - `upload.html` exists but not integrated into main dashboard
   - Users must manually navigate to `upload.html`

4. **Missing Features**
   - No user authentication on frontend
   - No history/saved predictions
   - No data export options in dashboard
   - No API key management UI
   - No real-time API status monitoring on frontend

---

## 🚀 HOW TO RUN THE PROJECT

### Prerequisites
```bash
python --version  # Should be 3.8+
pip install -r requirements.txt
```

### Start Backend (Terminal 1)
```bash
uvicorn API.main:app --reload --host 127.0.0.1 --port 8000
```
**Access:** http://localhost:8000/docs

### Start Frontend (Terminal 2)
```bash
python -m http.server 8001 --directory FrontEnd
```
**Access:** 
- Dashboard: http://localhost:8001/dashboard.html
- Upload: http://localhost:8001/upload.html
- Marketing: http://localhost:8001/index.html

### Make a Test Prediction
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -H "x-api-key: demo_tier2_key_67890" \
  -d '{
    "phase":"Phase II",
    "indication":"Alzheimers Disease",
    "trial_design":{"trial_sample_size":200,"trial_duration_weeks":52},
    "endpoints":{"endpoint_type":"objective","primary_endpoint_name":"CDR-SB"},
    "biomarkers":{"apoe_e4_carrier":1,"ptau217_high":1,"amyloid_pet_positive":1},
    "enrollment":{"age_mean":72.5,"baseline_mmse":23,"cdr_baseline":0.5}
  }'
```

### Run Tests
```bash
pytest Tests/ -v
```

---

## 📋 COMPLETE PROJECT CHECKLIST

### ✅ COMPLETED ITEMS
- [x] ML model trained & validated
- [x] Feature engineering pipeline built
- [x] FastAPI backend fully functional
- [x] API key authentication & rate limiting
- [x] Input validation & error handling
- [x] Interactive API documentation (/docs)
- [x] CORS enabled for browser requests
- [x] Test suite created
- [x] Docker configuration
- [x] Deployment documentation
- [x] 3 frontend HTML files created
- [x] Plotting library integration (Plotly)
- [x] CSV upload functionality
- [x] CSV download functionality
- [x] Marketing landing page
- [x] API examples & documentation

### ⚠️ IN PROGRESS / NEEDS WORK
- [ ] Frontend-Backend CORS issue resolution
- [ ] Frontend unification (single app vs. 3 separate files)
- [ ] Navigation between frontend pages
- [ ] Frontend error handling & user feedback
- [ ] API connection validation on frontend
- [ ] Loading indicators on frontend
- [ ] Real-time API status checking

### ❌ NOT STARTED / TODO
- [ ] User authentication on frontend
- [ ] User accounts & saved predictions
- [ ] Prediction history/database
- [ ] API key management UI
- [ ] Advanced filtering in dashboard
- [ ] Export to PDF functionality
- [ ] Email report generation
- [ ] WebSocket for real-time updates
- [ ] Mobile responsive frontend refinement
- [ ] Dark/light theme toggle
- [ ] Accessibility improvements (WCAG)
- [ ] Frontend unit tests
- [ ] End-to-end (E2E) tests
- [ ] Performance optimization
- [ ] Caching layer (Redis)
- [ ] Analytics/tracking integration
- [ ] Deployment to production server
- [ ] CI/CD pipeline setup
- [ ] Monitoring & alerting setup
- [ ] Database for prediction logs
- [ ] Admin dashboard
- [ ] API rate limiting UI

---

## 🎯 KEY ISSUES TO FIX (PRIORITY ORDER)

### BLOCKER #1: Frontend CORS/Connection Issues
**Problem:** Frontend files at `localhost:8001` can't reliably communicate with API at `localhost:8000`

**Solution Options:**
1. Use a proxy in development (Vite/Webpack dev server)
2. Run frontend on same port as API
3. Add explicit API base URL to frontend
4. Use relative URLs instead of absolute

**Impact:** HIGH - Users can't submit predictions

---

### BLOCKER #2: No Unified Frontend Experience
**Problem:** Three separate HTML files with no navigation or central app shell

**Solution:**
1. Create an app shell/layout component (could be simple HTML)
2. Add navigation between dashboard, upload, and marketing pages
3. Create a unified login/auth entry point
4. Move marketing site to separate `/marketing/` folder

**Impact:** MEDIUM - UI/UX fragmentation

---

### BLOCKER #3: Missing Frontend Error Handling
**Problem:** Frontend doesn't gracefully handle API errors or connection failures

**Solution:**
1. Add try/catch error handling in JavaScript
2. Display user-friendly error messages
3. Add loading states
4. Add API health check on page load

**Impact:** MEDIUM - Poor user experience on errors

---

### BLOCKER #4: No Input Form on Dashboard
**Problem:** `dashboard.html` shows results but doesn't have form to ENTER new predictions

**Solution:**
1. Add prediction form to dashboard.html
2. Integrate form submission with API
3. Display results inline

**Impact:** HIGH - Users need to edit HTML to test dashboard

---

## 🔧 TECHNICAL DETAILS

### API Key Authentication
- **Tier 1 (Demo):** `demo_tier1_key_12345` - 100 requests/month
- **Tier 2 (Demo):** `demo_tier2_key_67890` - Unlimited requests
- **Header Options:**
  - `x-api-key: <key>`
  - `Authorization: Bearer <key>`

### Model Risk Thresholds
| Tier | Probability Range | Meaning |
|------|------------------|---------|
| HIGH | < 0.40 | High failure risk |
| MEDIUM | 0.40 - 0.69 | Moderate risk |
| LOW | ≥ 0.70 | Low failure risk |

### Feature Importance Output
Model returns top 5 features with:
- Feature name
- Coefficient value
- Direction (positive/negative)
- Impact magnitude

### Confidence Flags
- **HIGH:** All required biomarkers present (≥10 of 11)
- **MEDIUM:** Most biomarkers present (7-9 of 11)
- **LOW:** Missing several biomarkers (<7 of 11)

---

## 📊 PROJECT STATISTICS

| Metric | Value |
|--------|-------|
| Total Files | 50+ |
| Python Files | 25+ |
| HTML Files | 3 |
| Notebooks | 3 |
| API Endpoints | 5+ |
| Model Features (after engineering) | 29 |
| Base Input Features | 22 |
| Docker Support | ✅ Yes |
| Test Coverage | Partial |
| Production Ready (Backend) | ✅ Yes |
| Production Ready (Frontend) | ⚠️ Partial |
| Video Embeds | ❌ None |

---

## 🎬 VIDEO EMBEDDED LOCATIONS

**Video in Project:** ❌ NONE FOUND

All 3 frontend files checked:
- `dashboard.html` - ❌ No video tags, no iframes
- `index.html` - ❌ No video tags, no iframes, no YouTube embeds
- `upload.html` - ❌ No video tags, no iframes

---

## 🔐 SECURITY STATUS

✅ Implemented:
- API key authentication
- Rate limiting
- CORS policy
- Input validation
- Error masking (no stack traces in responses)

⚠️ Missing:
- HTTPS/TLS in local development (OK for dev)
- User password hashing (no user system yet)
- CSRF protection (not needed for API-only)
- Rate limiting per user (key-based only)
- Request signing

---

## 🚨 NEXT IMMEDIATE ACTIONS REQUIRED

### TODAY:
1. **Fix Frontend Connection Issue**
   - Test API from browser console
   - Debug CORS errors in browser
   - Verify API is accessible from localhost:8001

2. **Add Prediction Form to Dashboard**
   - Add form HTML to dashboard.html
   - Wire form to /predict endpoint
   - Display results below form

3. **Add Error Handling**
   - Wrap fetch calls in try/catch
   - Display error messages to user
   - Add loading spinner

### THIS WEEK:
4. **Create App Navigation**
   - Link between dashboard/upload/marketing
   - Create consistent header/footer

5. **Add API Status Check**
   - Test API health on page load
   - Show connection status to user

6. **Frontend Testing**
   - Test with different sample data
   - Test error scenarios
   - Test CSV upload

---

## 💡 ARCHITECTURE NOTES

- **Frontend:** Static HTML + JavaScript (no framework)
- **Backend:** FastAPI (async Python)
- **Model:** Scikit-learn Logistic Regression
- **Deployment:** Docker ready, Heroku ready, also supports local development
- **Database:** None currently (stateless API)
- **Authentication:** API key based (no user accounts)
- **Scaling:** Horizontal (stateless, can run multiple API instances)

---

## 📞 KEY CONTACT POINTS

**Main Entry Points:**
- API Docs: `http://localhost:8000/docs`
- Dashboard: `http://localhost:8001/dashboard.html`
- Upload Tool: `http://localhost:8001/upload.html`
- Marketing: `http://localhost:8001/index.html`

**Key Files to Edit:**
- API Logic: `API/main.py`
- Prediction Engine: `Models/predict_trial.py`
- Dashboard UI: `FrontEnd/dashboard.html`
- Upload UI: `FrontEnd/upload.html`

---

## 🎓 LEARNING PATH

If you're new to this project, read in this order:

1. `README.md` - Project overview
2. `ML_SCOPE.md` - What the model does
3. `API/README.md` - How the API works
4. `DEPLOYMENT.md` - How to run it
5. `Docs/architecture.md` - Technical details
6. `API/main.py` - Backend code
7. `Models/predict_trial.py` - Model code
8. `FrontEnd/dashboard.html` - Frontend code

---

**Last Updated:** May 28, 2026  
**Status:** Development - Frontend Integration Phase
