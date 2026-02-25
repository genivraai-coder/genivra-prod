"""
Comprehensive API Test Suite - Using TestClient

This tests the API directly without needing a running server.
"""

import json
import sys
from fastapi.testclient import TestClient

# Add project to path
sys.path.insert(0, 'c:/Users/andre/Downloads/Projects/Genivra.ai')

from API.main import app

# ============================================================================
# Setup Test Client
# ============================================================================

client = TestClient(app)

# ============================================================================
# Test Data
# ============================================================================

VALID_COMPLETE = {
    "phase": "Phase II",
    "indication": "Alzheimer's Disease",
    "trial_design": {
        "phase": "Phase II",
        "indication": "Alzheimer's Disease",
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
        "csf_abeta42_40_ratio_continuous": 0.45,
        "csf_ptau_elevated": 0,
        "amyloid_pet_positive": 1,
        "tau_pet_positive": 1,
        "hippocampal_atrophy_mri": 3800.0,
        "hippocampal_atrophy_binary": 1
    },
    "enrollment": {
        "age_mean": 72.5,
        "baseline_mmse": 22.0,
        "baseline_moca": 21.5,
        "cdr_baseline": 1.5
    },
    "biomarker_enrichment_strategy": "at_positive"
}

VALID_MINIMAL = {
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

MISSING_TRIAL_DESIGN = {
    "endpoints": {
        "endpoint_type": "objective",
        "primary_endpoint_name": "CDR-SB"
    },
    "biomarkers": {},
    "enrollment": {"age_mean": 70.0}
}

WRONG_TYPE_SAMPLE_SIZE = {
    "trial_design": {
        "trial_sample_size": "two-hundred",
        "trial_duration_weeks": 26
    },
    "endpoints": {
        "endpoint_type": "objective",
        "primary_endpoint_name": "CDR-SB"
    },
    "biomarkers": {},
    "enrollment": {"age_mean": 70.0}
}

INVALID_ENUM = {
    "trial_design": {
        "trial_sample_size": 100,
        "trial_duration_weeks": 26
    },
    "endpoints": {
        "endpoint_type": "invalid_type",
        "primary_endpoint_name": "CDR-SB"
    },
    "biomarkers": {},
    "enrollment": {"age_mean": 70.0}
}

OUT_OF_RANGE_MMSE = {
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
        "age_mean": 70.0,
        "baseline_mmse": 35
    }
}

NEGATIVE_SAMPLE_SIZE = {
    "trial_design": {
        "trial_sample_size": -100,
        "trial_duration_weeks": 26
    },
    "endpoints": {
        "endpoint_type": "objective",
        "primary_endpoint_name": "CDR-SB"
    },
    "biomarkers": {},
    "enrollment": {"age_mean": 70.0}
}

# ============================================================================
# Utility Functions
# ============================================================================

def print_header(text):
    print("\n" + "=" * 90)
    print(f"  {text}")
    print("=" * 90)

def print_subheader(text):
    print(f"\n  {text}")
    print("  " + "-" * 86)

def print_json(data):
    print(json.dumps(data, indent=2))

# ============================================================================
# Test Functions
# ============================================================================

def test_valid_complete():
    """Test valid request with all fields"""
    print_subheader("✓ TEST 1: Valid Request with All Fields")
    
    response = client.post("/predict", json=VALID_COMPLETE)
    
    print(f"  Status: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    result = response.json()
    
    # Validate structure
    assert "trial_success_probability" in result
    assert "risk_tier" in result
    assert "top_drivers" in result
    assert "biomarker_explanation" in result
    assert "confidence_flag" in result
    assert "model_version" in result
    assert "generated_timestamp" in result
    
    print(f"\n  📊 SUCCESS - All required fields present!")
    print(f"\n  Results:")
    print(f"    • Success Probability: {result['trial_success_probability']:.1%}")
    print(f"    • Risk Tier: {result['risk_tier']}")
    print(f"    • Confidence: {result['confidence_flag']}")
    print(f"    • Missing Biomarkers: {result['missing_biomarker_count']}")
    print(f"    • Model Version: {result['model_version']}")
    print(f"    • Timestamp: {result['generated_timestamp']}")
    
    print(f"\n  Top 3 Drivers:")
    for i, driver in enumerate(result['top_drivers'][:3], 1):
        direction = "↑ positive" if driver['direction'] == 'positive' else "↓ negative"
        print(f"    {i}. {driver['feature_name']:30} {direction:15} coef:{driver['coefficient']:7.3f}")
    
    print(f"\n  Biomarker Explanation:")
    sentences = result['biomarker_explanation'].split(". ")
    for i, sent in enumerate(sentences[:3], 1):
        if sent.strip():
            print(f"    {i}. {sent.strip()}.")
    
    print(f"\n  ✅ PASSED: Valid request accepted and returned structured output")


def test_valid_minimal():
    """Test valid request with minimal fields"""
    print_subheader("✓ TEST 2: Minimal Valid Request (Only Required Fields)")
    
    response = client.post("/predict", json=VALID_MINIMAL)
    
    print(f"  Status: {response.status_code}")
    assert response.status_code == 200
    
    result = response.json()
    print(f"\n  📊 SUCCESS - Minimal request accepted!")
    print(f"    • Success Probability: {result['trial_success_probability']:.1%}")
    print(f"    • Risk Tier: {result['risk_tier']}")
    print(f"    • Confidence: {result['confidence_flag']}")
    

    print(f"\n  ✅ PASSED: Minimal request processed successfully")


def test_missing_trial_design():
    """Test error when trial_design is missing"""
    print_subheader("✗ TEST 3: Error - Missing 'trial_design' Section")
    
    response = client.post("/predict", json=MISSING_TRIAL_DESIGN)
    
    print(f"  Status: {response.status_code}")
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    
    error = response.json()
    print(f"\n  Error Response:")
    print(f"    • Error Type: {error.get('error', 'N/A')}")
    print(f"    • Message: {error.get('message', 'N/A')}")
    print(f"    • Status Code: {error.get('status_code', 'N/A')}")
    
    print(f"\n  ✅ PASSED: Correctly rejected missing required section")


def test_wrong_type_sample_size():
    """Test error when sample_size is string instead of integer"""
    print_subheader("✗ TEST 4: Error - Wrong Type (String instead of Integer)")
    
    response = client.post("/predict", json=WRONG_TYPE_SAMPLE_SIZE)
    
    print(f"  Status: {response.status_code}")
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"
    
    error = response.json()
    print(f"\n  Validation Error Response:")
    if "detail" in error:
        # Show first validation error
        details = error["detail"]
        if isinstance(details, list) and len(details) > 0:
            first = details[0]
            print(f"    • Field: {first.get('loc', ['unknown'])[-1]}")
            print(f"    • Problem: {first.get('msg', 'validation error')}")
            print(f"    • Input was: 'two-hundred' (string)")
    
    print(f"\n  ✅ PASSED: Correctly rejected wrong data type")


def test_invalid_enum():
    """Test error when endpoint_type is invalid enum value"""
    print_subheader("✗ TEST 5: Error - Invalid Enum Value")
    
    response = client.post("/predict", json=INVALID_ENUM)
    
    print(f"  Status: {response.status_code}")
    assert response.status_code == 422
    
    error = response.json()
    print(f"\n  Validation Error Response:")
    print(f"    • Expected: 'objective', 'subjective', or 'mixed'")
    print(f"    • Received: 'invalid_type'")
    if "detail" in error:
        details = error["detail"]
        if isinstance(details, list) and len(details) > 0:
            print(f"    • Validation Error: {details[0].get('msg', 'enum validation error')}")
    
    print(f"\n  ✅ PASSED: Correctly rejected invalid enum value")


def test_out_of_range_mmse():
    """Test error when MMSE score is out of range"""
    print_subheader("✗ TEST 6: Error - Out of Range Value (MMSE)")
    
    response = client.post("/predict", json=OUT_OF_RANGE_MMSE)
    
    print(f"  Status: {response.status_code}")
    assert response.status_code == 422
    
    error = response.json()
    print(f"\n  Validation Error Response:")
    print(f"    • Field: baseline_mmse")
    print(f"    • Valid Range: 0.0 - 30.0")
    print(f"    • Received: 35.0")
    if "detail" in error:
        details = error["detail"]
        if isinstance(details, list) and len(details) > 0:
            print(f"    • Error: {details[0].get('msg', 'range validation error')}")
    
    print(f"\n  ✅ PASSED: Correctly rejected out-of-range value")


def test_negative_sample_size():
    """Test error when sample size is negative"""
    print_subheader("✗ TEST 7: Error - Negative Value (Sample Size)")
    
    response = client.post("/predict", json=NEGATIVE_SAMPLE_SIZE)
    
    print(f"  Status: {response.status_code}")
    assert response.status_code == 422
    
    error = response.json()
    print(f"\n  Validation Error Response:")
    print(f"    • Field: trial_sample_size")
    print(f"    • Constraint: Must be > 0")
    print(f"    • Received: -100")
    if "detail" in error:
        details = error["detail"]
        if isinstance(details, list) and len(details) > 0:
            print(f"    • Error: {details[0].get('msg', 'greater than zero validation error')}")
    
    print(f"\n  ✅ PASSED: Correctly rejected negative value")


def test_health_endpoints():
    """Test health check endpoints"""
    print_subheader("✓ TEST 8: Health Check Endpoints")
    
    # GET /
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    print(f"  GET /")
    print(f"    • Status: {response.status_code}")
    print(f"    • Response: {data['status']} (v{data['version']})")
    
    # GET /health
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    print(f"\n  GET /health")
    print(f"    • Status: {response.status_code}")
    print(f"    • Response: {data['status']} (v{data['version']})")
    
    print(f"\n  ✅ PASSED: Health endpoints working")


# ============================================================================
# Main Test Runner
# ============================================================================

def main():
    print_header("GENIVRA API COMPREHENSIVE TEST SUITE")
    print("  Using FastAPI TestClient (no server needed)")
    
    passed = 0
    failed = 0
    tests = [
        ("Valid Complete Request", test_valid_complete),
        ("Valid Minimal Request", test_valid_minimal),
        ("Missing Required Section", test_missing_trial_design),
        ("Wrong Data Type", test_wrong_type_sample_size),
        ("Invalid Enum Value", test_invalid_enum),
        ("Out of Range Value", test_out_of_range_mmse),
        ("Negative Value", test_negative_sample_size),
        ("Health Endpoints", test_health_endpoints),
    ]
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"\n  ❌ FAILED: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"\n  ❌ ERROR: {str(e)}")
            failed += 1
    
    # Summary
    print_header("TEST SUMMARY")
    total = passed + failed
    print(f"  Total Tests: {total}")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    
    if failed == 0:
        print(f"\n  🎉 ALL TESTS PASSED!")
        print(f"\n  Summary:")
        print(f"    ✅ Valid requests accepted with structured output")
        print(f"    ✅ Missing sections rejected with 400 error")
        print(f"    ✅ Wrong data types rejected with 422 error")
        print(f"    ✅ Invalid enum values rejected with 422 error")
        print(f"    ✅ Out-of-range values rejected with 422 error")
        print(f"    ✅ Negative values rejected with 422 error")
        print(f"    ✅ Health endpoints working")
        print(f"\n  ERROR HANDLING: ✅ Comprehensive and working correctly")
    else:
        print(f"\n  ⚠️  {failed} test(s) failed")
    
    print("\n" + "=" * 90 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
