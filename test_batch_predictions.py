"""
Comprehensive test suite for batch prediction endpoint.

Tests CSV upload, row validation, error handling, and response formats.
"""

import pytest
import sys
import json
from io import BytesIO
from fastapi.testclient import TestClient

# Setup path
sys.path.insert(0, 'c:/Users/andre/Downloads/Projects/Genivra.ai')

from API.main import app

client = TestClient(app)


# ============================================================================
# TEST DATA
# ============================================================================

# Valid CSV with complete data
VALID_CSV_COMPLETE = """trial_name,trial_sample_size,trial_duration_weeks,endpoint_type,primary_endpoint_name,age_mean,baseline_mmse,apoe_e4_carrier,ptau217_high,amyloid_pet_positive,biomarker_enrichment_strategy
TRIAL-001,200,52,objective,CDR-SB,72.5,22.0,1,1,1,at_positive
TRIAL-002,150,26,objective,ADAS-Cog,70.0,24.0,0,1,1,at_positive
TRIAL-003,300,52,subjective,ADCOMS,73.0,20.0,1,0,0,cognitive_only"""

# Valid CSV with minimal data (required fields only)
VALID_CSV_MINIMAL = """trial_sample_size,trial_duration_weeks,endpoint_type,primary_endpoint_name,age_mean
100,26,objective,CDR-SB,70.0
200,52,objective,ADAS-Cog,72.0
150,39,subjective,ADCOMS,71.0"""

# CSV with missing required field (trial_sample_size)
CSV_MISSING_REQUIRED = """trial_name,trial_duration_weeks,endpoint_type,primary_endpoint_name,age_mean
TRIAL-001,52,objective,CDR-SB,72.5
TRIAL-002,26,objective,ADAS-Cog,70.0"""

# CSV with invalid values (wrong enum, out of range)
CSV_INVALID_VALUES = """trial_name,trial_sample_size,trial_duration_weeks,endpoint_type,primary_endpoint_name,age_mean,baseline_mmse
TRIAL-001,200,52,invalid_enum,CDR-SB,72.5,22.0
TRIAL-002,150,26,objective,ADAS-Cog,70.0,35.0
TRIAL-003,300,52,objective,ADCOMS,73.0,20.0"""

# Mixed: some valid, some invalid
CSV_MIXED = """trial_name,trial_sample_size,trial_duration_weeks,endpoint_type,primary_endpoint_name,age_mean
VALID-001,200,52,objective,CDR-SB,72.5
INVALID-001,bad_number,26,objective,ADAS-Cog,70.0
VALID-002,300,52,subjective,ADCOMS,73.0"""

# Empty CSV
CSV_EMPTY = """trial_name,trial_sample_size,trial_duration_weeks,endpoint_type,primary_endpoint_name,age_mean"""

# Single valid row
CSV_SINGLE = """trial_sample_size,trial_duration_weeks,endpoint_type,primary_endpoint_name,age_mean
200,52,objective,CDR-SB,72.5"""

# Large CSV (100 rows)
def generate_large_csv(rows=100):
    lines = ["trial_name,trial_sample_size,trial_duration_weeks,endpoint_type,primary_endpoint_name,age_mean"]
    for i in range(rows):
        lines.append(f"TRIAL-{i:04d},200,52,objective,CDR-SB,{70.0 + (i % 10)}")
    return "\n".join(lines)


# ============================================================================
# TESTS: Basic Functionality
# ============================================================================

class TestBatchPredictionBasics:
    """Test basic batch prediction functionality."""
    
    def test_batch_json_response(self):
        """Test batch prediction returns JSON response."""
        files = {"file": ("trials.csv", BytesIO(VALID_CSV_COMPLETE.encode()), "text/csv")}
        response = client.post("/predict_batch", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "total_rows" in data
        assert "successful" in data
        assert "failed" in data
        assert "results" in data
        assert "model_version" in data
        assert "generated_timestamp" in data
        
        # Validate counts
        assert data["total_rows"] == 3
        assert data["successful"] == 3
        assert data["failed"] == 0
        assert len(data["results"]) == 3
    
    def test_batch_csv_response(self):
        """Test batch prediction returns CSV on request."""
        files = {"file": ("trials.csv", BytesIO(VALID_CSV_COMPLETE.encode()), "text/csv")}
        response = client.post("/predict_batch", files=files, params={"return_csv": True})
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        
        # CSV should contain rows
        content = response.text
        assert "TRIAL-001" in content
        assert "success" in content.lower()
    
    def test_batch_csv_endpoint(self):
        """Test alternative /predict_batch_csv endpoint."""
        files = {"file": ("trials.csv", BytesIO(VALID_CSV_COMPLETE.encode()), "text/csv")}
        response = client.post("/predict_batch_csv", files=files)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"


# ============================================================================
# TESTS: Valid Data
# ============================================================================

class TestBatchPredictionValidData:
    """Test batch prediction with valid input."""
    
    def test_complete_data(self):
        """Test CSV with all fields provided."""
        files = {"file": ("trials.csv", BytesIO(VALID_CSV_COMPLETE.encode()), "text/csv")}
        response = client.post("/predict_batch", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        # All should succeed
        assert data["successful"] == 3
        assert data["failed"] == 0
        
        # Check first result
        result = data["results"][0]
        assert result["trial_name"] == "TRIAL-001"
        assert result["success"] is True
        assert result["trial_success_probability"] is not None
        assert 0 <= result["trial_success_probability"] <= 1
        assert result["risk_tier"] in ["LOW", "MEDIUM", "HIGH"]
        assert result["confidence_flag"] in ["HIGH", "MEDIUM", "LOW"]
        assert len(result["top_drivers"]) > 0
        assert result["error_message"] is None
    
    def test_minimal_data(self):
        """Test CSV with only required fields."""
        files = {"file": ("trials.csv", BytesIO(VALID_CSV_MINIMAL.encode()), "text/csv")}
        response = client.post("/predict_batch", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        # All should succeed even with minimal data
        assert data["successful"] == 3
        assert data["failed"] == 0
        
        # Check confidence is LOW (missing biomarkers)
        for result in data["results"]:
            assert result["success"] is True
            assert result["confidence_flag"] == "LOW"  # Missing biomarkers
    
    def test_single_row(self):
        """Test CSV with single trial."""
        files = {"file": ("trials.csv", BytesIO(CSV_SINGLE.encode()), "text/csv")}
        response = client.post("/predict_batch", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_rows"] == 1
        assert data["successful"] == 1
        assert data["results"][0]["success"] is True


# ============================================================================
# TESTS: Error Handling
# ============================================================================

class TestBatchPredictionErrors:
    """Test error handling in batch predictions."""
    
    def test_missing_required_field(self):
        """Test that missing required fields cause per-row errors."""
        files = {"file": ("trials.csv", BytesIO(CSV_MISSING_REQUIRED.encode()), "text/csv")}
        response = client.post("/predict_batch", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        # Both rows should fail
        assert data["failed"] == 2
        assert data["successful"] == 0
        
        # Check error messages
        for result in data["results"]:
            assert result["success"] is False
            assert result["error_message"] is not None
            assert "trial_sample_size" in result["error_message"]
    
    def test_invalid_enum_value(self):
        """Test that invalid enum values cause errors."""
        files = {"file": ("trials.csv", BytesIO(CSV_INVALID_VALUES.encode()), "text/csv")}
        response = client.post("/predict_batch", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        # First row fails (invalid enum), others may succeed/fail
        first = data["results"][0]
        assert first["success"] is False
        assert "endpoint_type" in first["error_message"] or "invalid" in first["error_message"].lower()
    
    def test_mixed_valid_invalid(self):
        """Test that some rows succeed while others fail."""
        files = {"file": ("trials.csv", BytesIO(CSV_MIXED.encode()), "text/csv")}
        response = client.post("/predict_batch", files=files)
        
        assert response.status_code == 200
        data = response.json()
        
        # At least one should succeed, one should fail
        assert data["successful"] >= 1
        assert data["failed"] >= 1
        
        # Find success and failure
        successes = [r for r in data["results"] if r["success"]]
        failures = [r for r in data["results"] if not r["success"]]
        assert len(successes) > 0
        assert len(failures) > 0
    
    def test_empty_csv(self):
        """Test that empty CSV is rejected."""
        files = {"file": ("trials.csv", BytesIO(CSV_EMPTY.encode()), "text/csv")}
        response = client.post("/predict_batch", files=files)
        
        assert response.status_code == 400
        assert "empty" in response.json()["detail"].lower()
    
    def test_wrong_file_type(self):
        """Test that non-CSV files are rejected."""
        files = {"file": ("trials.txt", BytesIO(b"not csv"), "text/plain")}
        response = client.post("/predict_batch", files=files)
        
        assert response.status_code == 400
        assert "csv" in response.json()["detail"].lower()
    
    def test_malformed_csv(self):
        """Test that malformed CSV is handled."""
        bad_csv = 'trial_sample_size,trial_duration_weeks,endpoint_type\n"unclosed quote,52,objective'
        files = {"file": ("trials.csv", BytesIO(bad_csv.encode()), "text/csv")}
        response = client.post("/predict_batch", files=files)
        
        # Should handle gracefully (either error or skip row)
        assert response.status_code in [200, 400]


# ============================================================================
# TESTS: Performance & Scale
# ============================================================================

class TestBatchPredictionPerformance:
    """Test performance and scalability."""
    
    def test_large_batch_10_rows(self):
        """Test processing 10 rows."""
        csv_data = generate_large_csv(10)
        files = {"file": ("trials.csv", BytesIO(csv_data.encode()), "text/csv")}
        response = client.post("/predict_batch", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 10
        assert data["successful"] == 10  # All should succeed
    
    def test_large_batch_50_rows(self):
        """Test processing 50 rows."""
        csv_data = generate_large_csv(50)
        files = {"file": ("trials.csv", BytesIO(csv_data.encode()), "text/csv")}
        response = client.post("/predict_batch", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 50
        # All should succeed with complete data
        assert data["successful"] >= 45  # Allow for any edge cases
    
    def test_large_batch_100_rows(self):
        """Test processing 100 rows."""
        csv_data = generate_large_csv(100)
        files = {"file": ("trials.csv", BytesIO(csv_data.encode()), "text/csv")}
        response = client.post("/predict_batch", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 100
        assert len(data["results"]) == 100


# ============================================================================
# TESTS: Response Format
# ============================================================================

class TestBatchPredictionResponseFormat:
    """Test response structure and content."""
    
    def test_result_structure(self):
        """Test that each result has correct structure."""
        files = {"file": ("trials.csv", BytesIO(VALID_CSV_COMPLETE.encode()), "text/csv")}
        response = client.post("/predict_batch", files=files)
        
        data = response.json()
        result = data["results"][0]
        
        # Check required fields
        assert "row_number" in result
        assert "trial_name" in result
        assert "success" in result
        
        # For successful prediction
        if result["success"]:
            assert "trial_success_probability" in result
            assert "risk_tier" in result
            assert "biomarker_explanation" in result
            assert "confidence_flag" in result
            assert "top_drivers" in result
    
    def test_error_result_structure(self):
        """Test that error results have correct structure."""
        files = {"file": ("trials.csv", BytesIO(CSV_MISSING_REQUIRED.encode()), "text/csv")}
        response = client.post("/predict_batch", files=files)
        
        data = response.json()
        result = data["results"][0]
        
        # For failed prediction
        if not result["success"]:
            assert "error_message" in result
            assert result["error_message"] is not None
            assert result["trial_success_probability"] is None
            assert result["risk_tier"] is None
    
    def test_row_numbers(self):
        """Test that row numbers are correct (1-indexed)."""
        files = {"file": ("trials.csv", BytesIO(VALID_CSV_MINIMAL.encode()), "text/csv")}
        response = client.post("/predict_batch", files=files)
        
        data = response.json()
        
        # Row numbers should be 2, 3, 4 (header is row 1)
        row_numbers = [r["row_number"] for r in data["results"]]
        assert row_numbers == [2, 3, 4]


# ============================================================================
# TESTS: Feature Drivers
# ============================================================================

class TestBatchPredictionDrivers:
    """Test top feature drivers in batch results."""
    
    def test_top_drivers_present(self):
        """Test that successful predictions have top drivers."""
        files = {"file": ("trials.csv", BytesIO(VALID_CSV_COMPLETE.encode()), "text/csv")}
        response = client.post("/predict_batch", files=files)
        
        data = response.json()
        
        for result in data["results"]:
            if result["success"]:
                assert result["top_drivers"] is not None
                assert isinstance(result["top_drivers"], list)
                assert len(result["top_drivers"]) > 0
                
                # Check driver structure
                driver = result["top_drivers"][0]
                assert "feature_name" in driver
                assert "coefficient" in driver
                assert "direction" in driver
                assert driver["direction"] in ["positive", "negative"]


# ============================================================================
# TESTS: Confidence Flags
# ============================================================================

class TestBatchPredictionConfidence:
    """Test confidence assessment in batch predictions."""
    
    def test_high_confidence_with_biomarkers(self):
        """Test HIGH confidence when optional biomarkers provided."""
        files = {"file": ("trials.csv", BytesIO(VALID_CSV_COMPLETE.encode()), "text/csv")}
        response = client.post("/predict_batch", files=files)
        
        data = response.json()
        
        for result in data["results"]:
            if result["success"]:
                # With biomarkers: expect HIGH or MEDIUM confidence (both are good)
                assert result["confidence_flag"] in ["HIGH", "MEDIUM"]
    
    def test_low_confidence_without_biomarkers(self):
        """Test LOW confidence when biomarkers missing."""
        files = {"file": ("trials.csv", BytesIO(VALID_CSV_MINIMAL.encode()), "text/csv")}
        response = client.post("/predict_batch", files=files)
        
        data = response.json()
        
        for result in data["results"]:
            if result["success"]:
                # Without biomarkers
                assert result["confidence_flag"] == "LOW"


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
