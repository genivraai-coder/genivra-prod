# Quick Reference: Using predict_trial

**Version:** 1.0 | **Status:** Production Ready | **Date:** Feb 20, 2026

---

## Import & Execute

```python
from Models.predict_trial import predict_trial

result = predict_trial(trial_dict)
```

---

## Input Template (Minimal)

```python
trial = {
    # 11 REQUIRED fields (HIGH confidence)
    "apoe_e4_carrier": 1,                      # 0 or 1
    "ptau217_high": 1,                         # 0 or 1
    "amyloid_pet_positive": 1,                 # 0 or 1
    "age_mean": 72.5,                          # float
    "baseline_mmse": 23,                       # float (0–30)
    "cdr_baseline": 0.5,                       # float (0–18)
    "trial_sample_size": 234,                  # int
    "trial_duration_weeks": 52,                # int
    "endpoint_type": "objective",              # str: "objective", "subjective", "mixed"
    "primary_endpoint_name": "CDR-SB",         # str: "CDR-SB", "MMSE", "ADCOMS"
    "biomarker_enrichment_strategy": "amyloid_positive",  # str
    
    # 11 OPTIONAL fields (improve confidence & predictions)
    # "apoe_e4_homozygous": 0,
    # "ptau217_continuous": 18.5,
    # "tau_pet_positive": 1,
    # "csf_abeta42_40_ratio_low": 1,
    # ... plus 7 more (see PREDICT_TRIAL_GUIDE.md)
}
```

---

## Output Format

```python
{
    "trial_success_probability": 0.998,         # 0–1 float
    "risk_tier": "LOW",                         # "LOW", "MEDIUM", or "HIGH"
    "confidence_flag": "HIGH",                  # "HIGH", "MEDIUM", or "LOW"
    "top_feature_importance": [                 # List of top 5 features
        {
            "rank": 1,
            "feature": "trial_sample_size",
            "coefficient": 1.4222,
            "importance_score": 1.4222,
            "direction": "increases_probability"
        },
        # ... 4 more features ...
    ],
    "biomarker_explanation": "This trial enrolls...",  # Natural language
    "missing_biomarker_count": 0,               # Count
    "model_version": "v1.0",
    "generated_timestamp": "2026-02-20T14:32:00Z"
}
```

---

## Risk Tier Decision Table

| Success % | Risk Tier | Recommendation |
|-----------|-----------|---|
| ≥ 70% | **LOW** | ✅ Proceed with Phase III planning |
| 40–69% | **MEDIUM** | ⚠️ Consider design changes |
| < 40% | **HIGH** | 🛑 Strong evidence against advancement |

---

## Confidence Assessment

| Confidence | Missing Required Fields | Action |
|-----------|------------------------|--------|
| **HIGH** | 0 | All biomarkers present; prediction fully reliable |
| **MEDIUM** | 1–2 | One or two fields missing; use with some caution |
| **LOW** | > 2 | Significant data gaps; use for reference only |

---

## Top 5 Feature Drivers (From Model)

**Positive Drivers (increase success):**
1. Trial sample size (+1.42) — More participants = higher success
2. APOE ε4 homozygous (+0.86) — Homozygous carriers improve odds
3. Trial duration (+0.78) — Longer trials detect effects better
4. Amyloid PET positive (+0.76) — Biomarker enrichment helps
5. p-tau217 high (+0.54) — Additional biomarker support

**Negative Drivers (decrease success):**
1. Cognitive-only enrichment (-1.49) ⚠️ **Most impactful** — No biomarker enrollment very risky
2. CSF Aβ42/Aβ40 low (-1.03) — Indicates pathology but model disfavors
3. MoCA baseline (-0.57) — Higher baseline cognitive function = lower slope
4. Tau PET positive (-0.56) — Tau-targeting trials harder
5. Objective endpoints (-0.52) — Biomarker endpoints more variable

---

## Example Results

### Scenario A: Lecanemab-like Trial
```python
trial = {
    "apoe_e4_carrier": 1,
    "ptau217_high": 1,
    "amyloid_pet_positive": 1,
    "age_mean": 72.5,
    "baseline_mmse": 23.0,
    "cdr_baseline": 0.5,
    "trial_sample_size": 234,
    "trial_duration_weeks": 52,
    "endpoint_type": "objective",
    "primary_endpoint_name": "CDR-SB",
    "biomarker_enrichment_strategy": "amyloid_positive",
}
# → Success: 99.8% | Risk: LOW | Confidence: HIGH
```

### Scenario B: Risky Trial Design
```python
trial = {
    "apoe_e4_carrier": 0,
    "ptau217_high": 0,
    "amyloid_pet_positive": 0,
    "age_mean": 65.0,
    "baseline_mmse": 26.0,
    "cdr_baseline": 0.0,
    "trial_sample_size": 50,
    "trial_duration_weeks": 12,
    "endpoint_type": "subjective",
    "primary_endpoint_name": "MMSE",
    "biomarker_enrichment_strategy": "cognitive_only",
}
# → Success: 6.3% | Risk: HIGH | Confidence: HIGH
```

---

## Batch Processing

```python
from Models.predict_trial import predict_trials_batch

trials = [trial1, trial2, trial3, ...]
results = predict_trials_batch(trials)

for result in results:
    probability = result['trial_success_probability']
    risk = result['risk_tier']
    print(f"Success: {probability:.1%} | Risk: {risk}")
```

---

## Testing

Run the full test suite (4 scenarios):
```bash
python Scripts/test_predict_trial.py
```

Expected output shows:
- ✅ High-confidence success (99.8%)
- ✅ Low-confidence with missing fields (99.3%)  
- ✅ High-risk failure (6.3%)
- ✅ Medium-risk moderate success (98.4%)

---

## When to Use This Model

✅ **Good Use Cases:**
- Early trial design evaluation (Phase I → Phase II planning)
- Biomarker enrichment strategy assessment
- Risk-benefit analysis for investment decisions
- Sample size and duration optimization

❌ **Poor Use Cases:**
- Real Phase II trial prediction (trained on synthetic data only)
- Single patient prognosis (model predicts trial-level outcomes)
- Non-AD indications (AD Phase II only)
- Predicting unplanned early terminations (doesn't model these)

---

## Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| `FileNotFoundError: Model not found` | Models not trained | Run `python Models/train_logistic_regression.py` |
| `KeyError: 'randomization_ratio'` | Missing categorical field | Auto-filled with "unknown"; no action needed |
| `NoneType` in output | All predictions failed | Check input dict has correct types |
| Success < 40% when expected high | Cognitive-only enrichment detected | Change to biomarker enrichment strategy |

---

## Documentation

- **Full Guide:** `PREDICT_TRIAL_GUIDE.md` (API, schema, limitations)
- **Implementation Details:** `IMPLEMENTATION_SUMMARY.md` (internals, testing)
- **ML Scope:** `ML_SCOPE.md` (objective, output requirements)
- **Features:** `Features/biomarker_feature_catalog.md` (encoding rules)

---

## Model Card

| Metric | Value |
|--------|-------|
| Algorithm | Logistic Regression (L2 penalty) |
| Training Data | 300 synthetic AD Phase II trials |
| Features | 29 engineered (from 22 base) |
| Test Accuracy | 98.33% |
| Test ROC-AUC | 1.0000 |
| CV Accuracy (5-fold) | 98.00% ± 1.25% |
| Class Balance | 98% success, 2% failure |

---

**Questions?** See `PREDICT_TRIAL_GUIDE.md` or contact engineering+ml@genivra.ai
