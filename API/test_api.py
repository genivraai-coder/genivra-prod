"""
API Tests

Test suite for Genivra API endpoints.

Run with:
    pytest API/test_api.py -v
"""

import pytest
import json
from fastapi.testclient import TestClient
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from API.main import app


# ============================================================================
# Test Client Setup
# ============================================================================

client = TestClient(app)
DEFAULT_AUTH_HEADERS = {"Authorization": "Bearer demo_tier2_key_67890"}


def auth_headers(extra=None):
    headers = DEFAULT_AUTH_HEADERS.copy()
    if extra:
        headers.update(extra)
    return headers


def auth_post(path, json=None, **kwargs):
    headers = auth_headers(kwargs.pop("headers", None))
    return client.post(path, json=json, headers=headers, **kwargs)



# ============================================================================
# Test Data
# ============================================================================

VALID_REQUEST = {
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
        "tau_pet_positive": 0
    },
    "enrollment": {
        "age_mean": 72.5,
        "baseline_mmse": 22.0,
        "cdr_baseline": 1.5
    },
    "biomarker_enrichment_strategy": "at_positive"
}

MINIMAL_REQUEST = {
    "trial_design": {
        "trial_sample_size": 100,
        "trial_duration_weeks": 26
    },
    "endpoints": {
        "endpoint_type": "objective",
        "primary_endpoint_name": "CDR-SB"
    },
    "biomarkers": {},
    "enrollment": {
        "age_mean": 70.0
    }
}


# ============================================================================
# Health Check Tests
# ============================================================================

class TestHealth:
    """Test health check endpoints."""
    
    def test_root_health_check(self):
        """Test GET / endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data
    
    def test_health_endpoint(self):
        """Test GET /health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data


class TestApiKeyAuth:
    """Test API key authentication and usage status endpoints."""

    def test_authorization_bearer_header_works(self):
        response = client.post(
            "/predict",
            json=VALID_REQUEST,
            headers={"Authorization": "Bearer demo_tier2_key_67890"}
        )
        assert response.status_code == 200

    def test_api_key_status_endpoint(self):
        response = client.get(
            "/api-key/status",
            headers={"x-api-key": "demo_tier2_key_67890"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tier"] == "tier_2"
        assert data["usage"]["api_key"] == "demo_tier2_key_67890"
        assert "current_usage" in data["usage"]
        assert "remaining" in data["usage"]


# ============================================================================
# Prediction Tests
# ============================================================================

class TestPredictions:
    """Test prediction endpoints."""
    
    def test_valid_prediction(self):
        """Test POST /predict with valid input."""
        response = auth_post("/predict", json=VALID_REQUEST)
        assert response.status_code == 200
        
        data = response.json()
        
        # Validate response structure
        assert "trial_success_probability" in data
        assert "risk_tier" in data
        assert "top_drivers" in data
        assert "biomarker_explanation" in data
        assert "confidence_flag" in data
        assert "model_version" in data
        assert "generated_timestamp" in data
        
        # Validate data types
        assert isinstance(data["trial_success_probability"], float)
        assert 0 <= data["trial_success_probability"] <= 1
        assert data["risk_tier"] in ["LOW", "MEDIUM", "HIGH"]
        assert data["confidence_flag"] in ["HIGH", "MEDIUM", "LOW"]
        assert isinstance(data["top_drivers"], list)
        assert len(data["top_drivers"]) <= 5
        
        # Validate feature drivers
        for driver in data["top_drivers"]:
            assert "feature_name" in driver
            assert "coefficient" in driver
            assert "direction" in driver
            assert driver["direction"] in ["positive", "negative"]
    
    def test_minimal_request(self):
        """Test prediction with minimal input."""
        response = auth_post("/predict", json=MINIMAL_REQUEST)
        assert response.status_code == 200
        data = response.json()
        assert "trial_success_probability" in data
        assert "risk_tier" in data
    
    def test_missing_trial_design(self):
        """Test error handling for missing trial_design."""
        invalid_request = {
            "endpoints": {
                "endpoint_type": "objective",
                "primary_endpoint_name": "CDR-SB"
            },
            "biomarkers": {},
            "enrollment": {"age_mean": 70.0}
        }
        response = auth_post("/predict", json=invalid_request)
        assert response.status_code == 400
        assert "error" in response.json()
    
    def test_missing_endpoints(self):
        """Test error handling for missing endpoints."""
        invalid_request = {
            "trial_design": {
                "trial_sample_size": 100,
                "trial_duration_weeks": 26
            },
            "biomarkers": {},
            "enrollment": {"age_mean": 70.0}
        }
        response = auth_post("/predict", json=invalid_request)
        assert response.status_code == 400
    
    def test_missing_enrollment(self):
        """Test error handling for missing enrollment."""
        invalid_request = {
            "trial_design": {
                "trial_sample_size": 100,
                "trial_duration_weeks": 26
            },
            "endpoints": {
                "endpoint_type": "objective",
                "primary_endpoint_name": "CDR-SB"
            },
            "biomarkers": {}
        }
        response = auth_post("/predict", json=invalid_request)
        assert response.status_code == 400
    
    def test_invalid_sample_size(self):
        """Test validation of sample size > 0."""
        invalid_request = MINIMAL_REQUEST.copy()
        invalid_request["trial_design"]["trial_sample_size"] = 0
        response = auth_post("/predict", json=invalid_request)
        assert response.status_code == 422  # Pydantic validation error
    
    def test_invalid_duration(self):
        """Test validation of duration > 0."""
        invalid_request = MINIMAL_REQUEST.copy()
        invalid_request["trial_design"]["trial_duration_weeks"] = -10
        response = auth_post("/predict", json=invalid_request)
        assert response.status_code == 422
    
    def test_invalid_endpoint_type(self):
        """Test validation of endpoint_type enum."""
        invalid_request = MINIMAL_REQUEST.copy()
        invalid_request["endpoints"]["endpoint_type"] = "invalid_type"
        response = auth_post("/predict", json=invalid_request)
        assert response.status_code == 422
    
    def test_invalid_mmse_range(self):
        """Test validation of MMSE in range 0-30."""
        invalid_request = MINIMAL_REQUEST.copy()
        invalid_request["enrollment"]["baseline_mmse"] = 35
        response = auth_post("/predict", json=invalid_request)
        assert response.status_code == 422
    
    def test_invalid_cdr_range(self):
        """Test validation of CDR in range 0-18."""
        invalid_request = MINIMAL_REQUEST.copy()
        invalid_request["enrollment"]["cdr_baseline"] = 20
        response = auth_post("/predict", json=invalid_request)
        assert response.status_code == 422
    
    def test_biomarker_optional(self):
        """Test that biomarkers are optional."""
        request_no_biomarkers = {
            "trial_design": {
                "trial_sample_size": 100,
                "trial_duration_weeks": 26
            },
            "endpoints": {
                "endpoint_type": "objective",
                "primary_endpoint_name": "CDR-SB"
            },
            "biomarkers": {
                # All None
            },
            "enrollment": {"age_mean": 70.0}
        }
        response = auth_post("/predict", json=request_no_biomarkers)
        assert response.status_code == 200


# ============================================================================
# Risk Tier Tests
# ============================================================================

class TestRiskTiers:
    """Test risk tier classification."""
    
    def test_high_success_low_risk(self):
        """Test high-success, low-risk scenario."""
        response = auth_post("/predict", json=VALID_REQUEST)
        assert response.status_code == 200
        data = response.json()
        
        # High biomarker signal should give HIGH success and LOW risk
        if data["trial_success_probability"] > 0.7:
            assert data["risk_tier"] == "LOW"
    
    def test_risk_tier_thresholds(self):
        """Test risk tier threshold mapping."""
        # Success prob >= 0.70 → LOW risk
        # Success prob 0.40-0.69 → MEDIUM risk
        # Success prob < 0.40 → HIGH risk
        
        response = auth_post("/predict", json=VALID_REQUEST)
        data = response.json()
        
        prob = data["trial_success_probability"]
        tier = data["risk_tier"]
        
        if prob >= 0.70:
            assert tier == "LOW"
        elif 0.40 <= prob < 0.70:
            assert tier == "MEDIUM"
        else:
            assert tier == "HIGH"


# ============================================================================
# Confidence Flag Tests
# ============================================================================

class TestConfidenceFlags:
    """Test confidence assessment."""
    
    def test_high_confidence_all_biomarkers(self):
        """Test HIGH confidence with all required biomarkers."""
        response = auth_post("/predict", json=VALID_REQUEST)
        data = response.json()
        assert "confidence_flag" in data
    
    def test_missing_biomarker_count(self):
        """Test missing_biomarker_count field."""
        response = auth_post("/predict", json=MINIMAL_REQUEST)
        data = response.json()
        assert "missing_biomarker_count" in data
        assert isinstance(data["missing_biomarker_count"], int)
        assert data["missing_biomarker_count"] >= 0


# ============================================================================
# Response Format Tests
# ============================================================================

class TestResponseFormat:
    """Test API response format and structure."""
    
    def test_timestamp_format(self):
        """Test timestamp is ISO 8601."""
        response = auth_post("/predict", json=MINIMAL_REQUEST)
        data = response.json()
        timestamp = data["generated_timestamp"]
        
        # Should be ISO 8601 UTC format
        assert isinstance(timestamp, str)
        assert "T" in timestamp
        assert "Z" in timestamp
    
    def test_feature_drivers_sorted_by_impact(self):
        """Test that top drivers are sorted by impact."""
        response = auth_post("/predict", json=VALID_REQUEST)
        data = response.json()
        drivers = data["top_drivers"]
        
        if len(drivers) > 1:
            # Check if sorted by impact_magnitude (descending)
            magnitudes = [d["impact_magnitude"] for d in drivers]
            assert magnitudes == sorted(magnitudes, reverse=True)
    
    def test_biomarker_explanation_not_empty(self):
        """Test that biomarker explanation is non-empty."""
        response = auth_post("/predict", json=VALID_REQUEST)
        data = response.json()
        assert len(data["biomarker_explanation"]) > 0


# ============================================================================
# Content Type Tests
# ============================================================================

class TestContentType:
    """Test content type handling."""
    
    def test_json_content_type(self):
        """Test response has JSON content type."""
        response = auth_post(
            "/predict",
            json=MINIMAL_REQUEST,
            headers={"Content-Type": "application/json"}
        )
        assert response.headers["content-type"] == "application/json"
    
    def test_invalid_json(self):
        """Test error handling for invalid JSON."""
        response = client.post(
            "/predict",
            content=b"not valid json",
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer demo_tier2_key_67890",
            }
        )
        assert response.status_code == 422


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
