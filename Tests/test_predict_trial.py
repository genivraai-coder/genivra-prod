from typing import Dict, Any
import json
import sys

# Add project root to path
sys.path.insert(0, '.')

from Models.predict_trial import predict_trial


# Minimal smoke test wrapper; original script preserved behavior in tests/ for CI
def test_smoke_high_confidence():
    data = {
        "apoe_e4_carrier": 1,
        "ptau217_high": 1,
        "amyloid_pet_positive": 1,
        "age_mean": 72.5,
        "baseline_mmse": 23,
        "cdr_baseline": 0.5,
        "trial_sample_size": 234,
        "trial_duration_weeks": 52,
        "endpoint_type": "objective",
        "primary_endpoint_name": "CDR-SB",
        "biomarker_enrichment_strategy": "amyloid_positive",
    }
    res = predict_trial(data)
    assert isinstance(res, dict)
    assert 'trial_success_probability' in res
