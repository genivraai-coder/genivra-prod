"""
Comprehensive API Test & Validation Script

Tests:
1. Valid request with all fields
2. Valid request with minimal fields
3. Missing required fields
4. Wrong data types
5. Invalid enum values
6. Out-of-range values
"""

import requests
import json
import time
import subprocess
import sys
import os
from pathlib import Path

# ============================================================================
# Configuration
# ============================================================================

API_URL = "http://127.0.0.1:8000"
PREDICT_ENDPOINT = f"{API_URL}/predict"
HEALTH_ENDPOINT = f"{API_URL}/health"

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

MISSING_ENDPOINTS = {
    "trial_design": {
        "trial_sample_size": 100,
        "trial_duration_weeks": 26
    },
    "biomarkers": {},
    "enrollment": {"age_mean": 70.0}
}

MISSING_ENROLLMENT = {
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

MISSING_REQUIRED_FIELD = {
    "trial_design": {
        # Missing: trial_sample_size
        "trial_duration_weeks": 26
    },
    "endpoints": {
        "endpoint_type": "objective",
        "primary_endpoint_name": "CDR-SB"
    },
    "biomarkers": {},
    "enrollment": {"age_mean": 70.0}
}

WRONG_TYPE_SAMPLE_SIZE = {
    "trial_design": {
        "trial_sample_size": "two-hundred",  # Should be integer
        "trial_duration_weeks": 26
    },
    "endpoints": {
        "endpoint_type": "objective",
        "primary_endpoint_name": "CDR-SB"
    },
    "biomarkers": {},
    "enrollment": {"age_mean": 70.0}
}

WRONG_TYPE_AGE = {
    "trial_design": {
        "trial_sample_size": 100,
        "trial_duration_weeks": 26
    },
    "endpoints": {
        "endpoint_type": "objective",
        "primary_endpoint_name": "CDR-SB"
    },
    "biomarkers": {},
    "enrollment": {"age_mean": "seventy"}  # Should be float/int
}

INVALID_ENUM = {
    "trial_design": {
        "trial_sample_size": 100,
        "trial_duration_weeks": 26
    },
    "endpoints": {
        "endpoint_type": "invalid_type",  # Should be objective/subjective/mixed
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
        "baseline_mmse": 35  # Should be 0-30
    }
}

OUT_OF_RANGE_CDR = {
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
        "cdr_baseline": 25  # Should be 0-18
    }
}

NEGATIVE_SAMPLE_SIZE = {
    "trial_design": {
        "trial_sample_size": -100,  # Should be > 0
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
# Helper Functions
# ============================================================================

def check_health(max_retries=5):
    """Check if API is running."""
    for attempt in range(max_retries):
        try:
            response = requests.get(HEALTH_ENDPOINT, timeout=2)
            if response.status_code == 200:
                return True
        except requests.exceptions.ConnectionError:
            if attempt < max_retries - 1:
                time.sleep(1)
    return False


def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_subheader(title):
    """Print a formatted subheader."""
    print(f"\n  {title}")
    print("  " + "-" * 76)


def print_json(data, label=""):
    """Pretty print JSON data."""
    if label:
        print(f"  {label}:")
    for line in json.dumps(data, indent=2).split("\n"):
        print(f"    {line}")


def test_valid_request(payload, name):
    """Test a valid request."""
    print_subheader(f"✓ VALID: {name}")
    
    try:
        response = requests.post(PREDICT_ENDPOINT, json=payload, timeout=10)
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            # Validate response structure
            required_fields = [
                "trial_success_probability",
                "risk_tier",
                "top_drivers",
                "biomarker_explanation",
                "confidence_flag",
                "model_version",
                "generated_timestamp"
            ]
            
            missing = [f for f in required_fields if f not in result]
            if missing:
                print(f"  ❌ MISSING FIELDS: {missing}")
                return False
            
            # Print results
            print(f"\n  📊 Prediction Results:")
            print(f"    • Success Probability: {result['trial_success_probability']:.1%}")
            print(f"    • Risk Tier: {result['risk_tier']}")
            print(f"    • Confidence: {result['confidence_flag']}")
            print(f"    • Missing Biomarkers: {result['missing_biomarker_count']}")
            
            print(f"\n  🎯 Top Drivers (Top 3):")
            for i, driver in enumerate(result['top_drivers'][:3], 1):
                direction = "↑ positive" if driver['direction'] == 'positive' else "↓ negative"
                print(f"    {i}. {driver['feature_name']:30} {direction:15} (coef: {driver['coefficient']:.3f})")
            
            print(f"\n  📝 Explanation:")
            for line in result['biomarker_explanation'].split(". "):
                if line:
                    print(f"    {line.strip()}.")
            
            print(f"\n  ✅ Response valid with all required fields")
            return True
        else:
            print(f"  ❌ Unexpected status code: {response.status_code}")
            print_json(response.json(), "Response")
            return False
    
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False


def test_error_request(payload, name, expected_status=400):
    """Test an invalid request."""
    print_subheader(f"✗ ERROR TEST: {name}")
    
    try:
        response = requests.post(PREDICT_ENDPOINT, json=payload, timeout=10)
        
        print(f"  Status Code: {response.status_code}")
        
        if response.status_code == expected_status:
            error_data = response.json()
            print(f"  ✅ Correctly rejected with {expected_status}")
            
            # Show error details
            if "error" in error_data:
                print(f"\n  Error Type: {error_data.get('error', 'N/A')}")
            if "message" in error_data:
                print(f"  Message: {error_data.get('message', 'N/A')}")
            elif "detail" in error_data:
                print(f"  Detail: {error_data.get('detail', 'N/A')}")
            
            return True
        else:
            print(f"  ❌ Expected {expected_status}, got {response.status_code}")
            print_json(response.json(), "Response")
            return False
    
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return False


# ============================================================================
# Main Test Suite
# ============================================================================

def main():
    """Run all tests."""
    print_header("GENIVRA API VALIDATION TEST SUITE")
    
    # Step 1: Check if API is running
    print("\n⏳ Checking API status...")
    if not check_health():
        print("\n❌ API is not running. Please start it with:")
        print("   uvicorn API.main:app --reload")
        print("\nTo start in the background, use another terminal window.")
        return False
    
    print("✅ API is running at http://127.0.0.1:8000")
    
    # Statistics
    passed = 0
    failed = 0
    
    # ========================================================================
    # VALID REQUEST TESTS
    # ========================================================================
    print_header("PART 1: VALID REQUESTS (Should Return 200)")
    
    if test_valid_request(VALID_COMPLETE, "Complete Request with All Fields"):
        passed += 1
    else:
        failed += 1
    
    if test_valid_request(VALID_MINIMAL, "Minimal Request (Only Required Fields)"):
        passed += 1
    else:
        failed += 1
    
    # ========================================================================
    # ERROR TESTS: Missing Required Sections
    # ========================================================================
    print_header("PART 2: ERROR HANDLING - Missing Required Sections")
    
    if test_error_request(MISSING_TRIAL_DESIGN, "Missing trial_design section", 400):
        passed += 1
    else:
        failed += 1
    
    if test_error_request(MISSING_ENDPOINTS, "Missing endpoints section", 400):
        passed += 1
    else:
        failed += 1
    
    if test_error_request(MISSING_ENROLLMENT, "Missing enrollment section", 400):
        passed += 1
    else:
        failed += 1
    
    # ========================================================================
    # ERROR TESTS: Missing Required Fields
    # ========================================================================
    print_header("PART 3: ERROR HANDLING - Missing Required Fields")
    
    if test_error_request(MISSING_REQUIRED_FIELD, "Missing trial_sample_size (required)", 422):
        passed += 1
    else:
        failed += 1
    
    # ========================================================================
    # ERROR TESTS: Wrong Data Types
    # ========================================================================
    print_header("PART 4: ERROR HANDLING - Wrong Data Types")
    
    if test_error_request(WRONG_TYPE_SAMPLE_SIZE, "Sample size as string instead of integer", 422):
        passed += 1
    else:
        failed += 1
    
    if test_error_request(WRONG_TYPE_AGE, "Age as string instead of number", 422):
        passed += 1
    else:
        failed += 1
    
    # ========================================================================
    # ERROR TESTS: Invalid Enum Values
    # ========================================================================
    print_header("PART 5: ERROR HANDLING - Invalid Enum Values")
    
    if test_error_request(INVALID_ENUM, "Invalid endpoint_type (should be objective/subjective/mixed)", 422):
        passed += 1
    else:
        failed += 1
    
    # ========================================================================
    # ERROR TESTS: Out of Range Values
    # ========================================================================
    print_header("PART 6: ERROR HANDLING - Out of Range Values")
    
    if test_error_request(OUT_OF_RANGE_MMSE, "MMSE = 35 (should be 0-30)", 422):
        passed += 1
    else:
        failed += 1
    
    if test_error_request(OUT_OF_RANGE_CDR, "CDR = 25 (should be 0-18)", 422):
        passed += 1
    else:
        failed += 1
    
    if test_error_request(NEGATIVE_SAMPLE_SIZE, "Sample size = -100 (should be > 0)", 422):
        passed += 1
    else:
        failed += 1
    
    # ========================================================================
    # Summary
    # ========================================================================
    print_header("TEST SUMMARY")
    
    total = passed + failed
    print(f"\n  Total Tests: {total}")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    
    if failed == 0:
        print(f"\n  🎉 ALL TESTS PASSED! API is working correctly.")
    else:
        print(f"\n  ⚠️  {failed} test(s) failed. Review output above.")
    
    print("\n" + "=" * 80)
    print("  Test Complete")
    print("=" * 80 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
