# Genivra Project Restructuring - Migration Guide

**Date:** March 3, 2026  
**Status:** ✅ COMPLETE

---

## Summary

The Genivra project has been reorganized into a clean, collaborative structure with clearly defined modules. All code, configuration, and documentation has been consolidated into new, purpose-built directories.

---

## New Directory Structure

```
genivra/
├── api/                          # REST API endpoints and request handlers
│   ├── __init__.py
│   ├── main.py                   # FastAPI application core
│   ├── models.py                 # Pydantic request/response schemas
│   ├── auth.py                   # API key authentication
│   ├── config.py                 # FastAPI configuration
│   ├── predict_trial.py          # Trial prediction inference engine
│   ├── rule_based_scorer.py      # Deterministic baseline scorer
│   ├── example_usage.py          # Python client example
│   ├── test_api.py               # API unit tests
│   ├── flask_app.py              # (Deprecated alternatives)
│   └── QUICK_START.py            # Quick reference guide
│
├── engine/                       # ML engine and feature engineering
│   ├── __init__.py
│   ├── ml_engine.py              # Model training (consolidated)
│   ├── feature_engineering.py    # Feature transformation pipeline
│   └── (Models/artifacts/ → Models/artifacts/ kept for trained models)
│
├── config/                       # Configuration files
│   ├── __init__.py
│   ├── config.yaml               # Main application config
│   ├── logging_config.yaml       # Logging setup
│   └── README.md
│
├── dashboards/                   # Web UI components
│   ├── index.html                # Main landing page
│   ├── dashboard.html            # Training prediction dashboard
│   ├── upload.html               # CSV batch upload interface
│   ├── js/                       # JavaScript utilities (optional)
│   ├── css/                      # Stylesheets (optional)
│   └── README.md
│
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── test_api_comprehensive.py # API endpoint tests
│   ├── test_batch_predictions.py # Batch prediction tests
│   ├── test_flask_predict.py     # Flask integration tests
│   ├── test_predict_trial.py     # Inference engine tests
│   ├── test_rule_based_scorer.py # Baseline scorer tests
│   └── __pycache__/
│
├── docs/                         # Documentation
│   ├── architecture.md           # System architecture
│   ├── DEPLOYMENT.md             # Deployment guide
│   ├── API_IMPLEMENTATION_SUMMARY.md  # API overview
│   ├── IMPLEMENTATION_SUMMARY.md # ML engine documentation
│   ├── PREDICT_TRIAL_GUIDE.md    # Inference engine guide
│   ├── citations/                # Research references
│   └── playbooks/                # Operational guides
│
├── Data/                         # (Unchanged - data directory)
├── Evaluation/                   # (Unchanged - evaluation metrics)
├── Notebooks/                    # (Unchanged - Jupyter notebooks)
├── Scripts/                      # (Unchanged - utility scripts)
├── Models/                       # (Kept - contains trained model artifacts)
│   ├── artifacts/                # Trained models and scaler (not moved)
│   ├── saved_models/             # Additional saved models
│   └── __init__.py
│
├── requirements.txt              # Python dependencies
├── Dockerfile                    # Container configuration
├── docker-compose.yml            # Docker Compose setup
├── Procfile                      # Cloud deployment configuration
├── runtime.txt                   # Python version specification
├── .env.example                  # Environment variables template
├── .gitignore                    # Git ignore rules
├── README.md                     # Project README
└── LICENSE                       # License file

```

---

## Migration Mapping

### From → To

| Old Location | New Location | Notes |
|--------------|--------------|-------|
| `API/main.py` | `api/main.py` | FastAPI application |
| `API/models.py` | `api/models.py` | Pydantic schemas |
| `API/auth.py` | `api/auth.py` | Authentication |
| `API/config.py` | `api/config.py` | Configuration |
| `API/example_usage.py` | `api/example_usage.py` | Client example |
| `API/test_api.py` | `api/test_api.py` | API tests |
| `Models/predict_trial.py` | `api/predict_trial.py` | Inference engine (inference is called by API) |
| `Models/rule_based_scorer.py` | `api/rule_based_scorer.py` | Baseline scorer (called by API) |
| `Models/train_logistic_regression.py` | `engine/ml_engine.py` | Consolidated training module |
| `Models/train_model.py` | `engine/ml_engine.py` | (Merged into ml_engine.py) |
| `Features/build_features.py` | `engine/feature_engineering.py` | Feature pipeline |
| `Features/utils.py` | `engine/feature_engineering.py` | (Merged into feature_engineering.py) |
| `Config/config.yaml` | `config/config.yaml` | Application config |
| `Config/logging_config.yaml` | `config/logging_config.yaml` | Logging config |
| `FrontEnd/dashboard.html` | `dashboards/dashboard.html` | Web dashboard |
| `FrontEnd/index.html` | `dashboards/index.html` | Landing page |
| `FrontEnd/upload.html` | `dashboards/upload.html` | CSV upload interface |
| `Tests/*.py` | `tests/*.py` | All test files |
| `Docs/architecture.md` | `docs/architecture.md` | Architecture documentation |
| `Docs/citations/` | `docs/citations/` | Research references |
| `Docs/playbooks/` | `docs/playbooks/` | Operational guides |
| `DEPLOYMENT.md` | `docs/DEPLOYMENT.md` | Deployment guide |
| `API_IMPLEMENTATION_SUMMARY.md` | `docs/API_IMPLEMENTATION_SUMMARY.md` | API overview |
| `IMPLEMENTATION_SUMMARY.md` | `docs/IMPLEMENTATION_SUMMARY.md` | ML engine docs |
| `PREDICT_TRIAL_GUIDE.md` | `docs/PREDICT_TRIAL_GUIDE.md` | Inference guide |
| `Models/artifacts/` | `Models/artifacts/` | **NOT MOVED** - contains trained models |
| `Data/` | `Data/` | **NOT MOVED** - data files |
| `Evaluation/` | `Evaluation/` | **NOT MOVED** - metrics code |
| `Notebooks/` | `Notebooks/` | **NOT MOVED** - Jupyter notebooks |
| `Scripts/` | `Scripts/` | **NOT MOVED** - utility scripts |

---

## Key Changes

### Organizational Benefits

1. **Clear Module Boundaries**
   - `api/` contains all API-related code and request/response handling
   - `engine/` contains ML training and feature engineering
   - `config/` centralizes all configuration
   - `dashboards/` groups all UI components
   - `tests/` consolidates all tests
   - `docs/` centralizes documentation

2. **Easier to Navigate**
   - No more hunting for files across `API/`, `Models/`, `Features/` directories
   - Each module has a clear purpose
   - `__init__.py` files in all folders enable proper Python package structure

3. **Better for Collaboration**
   - Clear code ownership (API team → api/, ML team → engine/, etc.)
   - Easier code reviews by package
   - Self-documenting structure

4. **Scalability**
   - Easy to add new sub-packages (e.g., `api/routes/`, `engine/models/`)
   - Clear extensibility patterns
   - Reduced namespace collisions

### Breaking Changes & Fixes Required

**Import Updates Required:**

All internal imports must be updated to reflect the new structure:

```python
# OLD (before restructuring)
from API.main import app
from API.auth import APIKeyManager
from Models.predict_trial import predict_trial
from Features.build_features import create_features

# NEW (after restructuring)
from api.main import app
from api.auth import APIKeyManager
from api.predict_trial import predict_trial
from engine.feature_engineering import create_features
```

**Files that need import updates:**
- `api/main.py` - imports from `api.predict_trial`, `api.auth`, `api.models`, `api.config`
- `api/example_usage.py` - imports from `api.*`
- `tests/` - imports from `api.`, `engine.*`
- Any scripts that imported from old locations

**Deprecation Notes:**
- `API/flask_app.py` → still in `api/` (legacy, may be removed)
- `Models/` directory → kept intact for artifacts, only code moved
- `Features/` directory → kept intact if additional files exist, code consolidated

---

## Import Reference Guide

### API Module Imports

```python
# Configuration
from api.config import settings, print_settings_summary

# Authentication  
from api.auth import APIKeyManager, KeyTier

# Request/Response Models
from api.models import (
    PredictionRequest,
    PredictionResponse,
    HealthResponse,
    ErrorResponse,
)

# Prediction & Scoring
from api.predict_trial import predict_trial
from api.rule_based_scorer import TrialScorer, RuleBasedWeights

# Main Application
from api.main import app  # FastAPI instance
```

### Engine Module Imports

```python
# ML Training
from engine.ml_engine import (
    train_model,
    evaluate_model,
    save_model,
    compute_feature_importance,
)

# Feature Engineering
from engine.feature_engineering import (
    load_raw_data,
    create_features,
    save_features,
)
```

### Running the API

```bash
# With new structure
cd genivra/
uvicorn api.main:app --reload

# Tests
pytest tests/

# Model training (if needed)
python -m engine.ml_engine
```

---

## Files Still In Original Locations

These directories and files were **NOT moved** and remain in their original locations:

- `Models/artifacts/` - Contains trained .pkl files (keep for production)
- `Models/saved_models/` - Additional model storage
- `Data/` - All data files (Raw, Processed, External)
- `Evaluation/` - Metrics calculation code
- `Notebooks/` - Jupyter notebooks for exploration
- `Scripts/` - Utility scripts and helpers

---

## Old Directories (Safe to Archive or Delete)

These directories have been fully migrated and can be safely archived/deleted:

- `API/` - All files moved to `api/`
- `Models/train_*.py` - Moved to `engine/ml_engine.py`
- `Features/` - Code consolidated to `engine/feature_engineering.py`
- `Tests/` - All tests migrated (but can keep for reference)
- `FrontEnd/` - All files moved to `dashboards/`
- `Config/` - All files moved to `config/`
- `Docs/` - Core content moved to `docs/`

### Backup & Archive Strategy

Before deletion, recommended protocol:

```bash
# Create backup archive
tar czf genivra_old_structure_backup_$(date +%Y%m%d).tar.gz API/ Models/train_*.py Features/ Tests/ FrontEnd/ Config/ Docs/

# Store safely (Git, S3, etc.)
mv genivra_old_structure_backup_*.tar.gz backups/

# Then safely remove old directories
rm -rf API/ Models/train_*.py Features/ Tests/ FrontEnd/ Config/ Docs/
```

---

## Next Steps (Recommended)

1. **Update all imports** in code to reference new locations
2. **Test thoroughly** to ensure all imports work
3. **Update CI/CD pipelines** if they reference old paths
4. **Archive old directories** (don't delete immediately)
5. **Update documentation** to reference new structure
6. **Update `.gitignore`** if needed for new paths

---

## Project Navigation Guide

### For API Developers
→ Start in `api/`
- Main entry point: `api/main.py`
- Modify endpoints here
- Add new routes following existing patterns
- Check tests: `tests/test_api_*.py`

### For ML Engineers
→ Start in `engine/`
- Training code: `engine/ml_engine.py`
- Features: `engine/feature_engineering.py`
- Inference: `api/predict_trial.py` (uses engine features)
- Model artifacts: `Models/artifacts/`

### For Frontend Developers
→ Start in `dashboards/`
- UI components: `dashboards/*.html`
- CSS: `dashboards/css/`
- JavaScript: `dashboards/js/`
- API calls: documented in `docs/API_IMPLEMENTATION_SUMMARY.md`

### For Operations/DevOps
→ Check `config/`
- Application settings: `config/config.yaml`
- Logging: `config/logging_config.yaml`
- Deployment: `docs/DEPLOYMENT.md`
- Docker: `Dockerfile`, `docker-compose.yml`

### For QA/Testing
→ Start in `tests/`
- Test suite: `tests/*.py`
- Run: `pytest tests/`
- Docs: `docs/` for expected behavior

---

## Configuration Files Location

- Application config: `config/config.yaml`
- Logging config: `config/logging_config.yaml`
- FastAPI config: `api/config.py` (Python module)
- Environment: `.env` (create from `.env.example`)

---

## Troubleshooting

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'API'`

**Solution:** Update import to lowercase
```python
# ✗ Old
from API.main import app

# ✓ New
from api.main import app
```

### API Won't Start

**Problem:** FastAPI can't find `predict_trial` function

**Solution:** Ensure relative imports work
```python
# In api/main.py
from api.predict_trial import predict_trial  # Absolute import
# or
from .predict_trial import predict_trial  # Relative import (if in same package)
```

###Test Failures

**Problem:** Tests failing with import errors

**Solution:** Update test imports
```bash
# Run tests from project root
pytest tests/

# Or specify Python path
PYTHONPATH=. pytest tests/
```

---

## Questions?

Refer to:
- API Documentation: `docs/API_IMPLEMENTATION_SUMMARY.md`
- Deployment Guide: `docs/DEPLOYMENT.md`
- Architecture: `docs/architecture.md`
- ML Guide: `docs/IMPLEMENTATION_SUMMARY.md`

---

## Version History

- **v1.0** (Mar 3, 2026): Initial reorganization complete
- **Next**: Update imports in all files and thorough testing

