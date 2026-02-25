import json
import os
import sys
import pytest

# Ensure repo root is on sys.path so `API` package can be imported when running pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API import flask_app


@pytest.fixture
def client():
    flask_app.app.config["TESTING"] = True
    with flask_app.app.test_client() as client:
        yield client


def test_predict_success(client, monkeypatch):
    # Stub the predict_trial function to return a predictable output
    stub_result = {
        "trial_success_probability": 0.72,
        "risk_tier": "MEDIUM",
        "top_feature_importance": [
            {"feature": "apoe_e4_carrier", "coefficient": -0.3},
            {"feature": "baseline_mmse", "coefficient": 0.2},
        ],
        "biomarker_explanation": "Main drivers: APOE, baseline MMSE",
        "confidence_flag": "HIGH",
    }

    monkeypatch.setattr(flask_app, "predict_trial", lambda payload: stub_result)

    payload = {
        "phase": "Phase II",
        "indication": "Alzheimer's Disease",
        "trial_design": {"trial_sample_size": 200, "trial_duration_weeks": 52},
        "endpoints": {"primary": "CDR-SB"},
        "biomarkers": {"apoe_e4_carrier": True, "ptau217_high": False},
        "enrollment": {"sites": 20}
    }

    resp = client.post("/predict", json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["probability_of_success"] == pytest.approx(0.72)
    assert data["risk_tier"] == "MEDIUM"
    assert isinstance(data["top_drivers"], list)
    assert data["biomarker_explanation"] == "Main drivers: APOE, baseline MMSE"
    assert data["confidence_flag"] == "HIGH"


def test_predict_missing_fields(client):
    # Missing required fields should return 400
    payload = {"phase": "Phase II"}
    resp = client.post("/predict", json=payload)
    assert resp.status_code == 400
    data = resp.get_json()
    assert "missing" in data
    assert isinstance(data["missing"], list)
