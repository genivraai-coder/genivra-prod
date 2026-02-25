#!/usr/bin/env python3
"""
Test script for API key authentication system.
Tests all authentication flows and error cases.
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"
DEMO_KEY_TIER1 = "demo_tier1_key_12345"
DEMO_KEY_TIER2 = "demo_tier2_key_67890"
INVALID_KEY = "invalid_key_xyz"

def print_test(name: str):
    """Print test header"""
    print(f"\n{'='*70}")
    print(f"TEST: {name}")
    print('='*70)

def print_result(status: str, message: str):
    """Print test result"""
    symbol = "✓" if status == "PASS" else "✗"
    print(f"{symbol} {status}: {message}")

def test_health_check():
    """Test health check requires no auth"""
    print_test("Health Check (No Auth Required)")
    try:
        resp = requests.get(f"{BASE_URL}/")
        assert resp.status_code == 200
        print_result("PASS", "Health check accessible without auth key")
        print(f"Response: {resp.json()}")
    except Exception as e:
        print_result("FAIL", str(e))

def test_missing_api_key():
    """Test request without API key returns 401"""
    print_test("Missing API Key")
    try:
        resp = requests.post(
            f"{BASE_URL}/predict",
            json={"phase": "Phase 3"}
        )
        assert resp.status_code == 401
        assert "Missing x-api-key header" in resp.json()["detail"]
        print_result("PASS", "Missing API key returns 401 Unauthorized")
        print(f"Response: {resp.json()}")
    except Exception as e:
        print_result("FAIL", str(e))

def test_invalid_api_key():
    """Test request with invalid API key returns 401"""
    print_test("Invalid API Key")
    try:
        resp = requests.post(
            f"{BASE_URL}/predict",
            headers={"x-api-key": INVALID_KEY},
            json={"phase": "Phase 3"}
        )
        assert resp.status_code == 401
        assert "Invalid or inactive API key" in resp.json()["detail"]
        print_result("PASS", "Invalid API key returns 401 Unauthorized")
        print(f"Response: {resp.json()}")
    except Exception as e:
        print_result("FAIL", str(e))

def test_valid_api_key_tier2():
    """Test request with valid Tier 2 API key"""
    print_test("Valid API Key (Tier 2)")
    try:
        # Build a valid request
        headers = {"x-api-key": DEMO_KEY_TIER2}
        payload = {
            "phase": "Phase 2",
            "indication": "Alzheimer's disease",
            "trial_design": {
                "trial_sample_size": 100,
                "trial_duration_weeks": 26,
                "number_of_arms": 2,
                "randomization_ratio": "1:1"
            },
            "endpoints": {
                "endpoint_type": "objective",
                "primary_endpoint_name": "CDR-SB"
            },
            "biomarkers": {},
            "enrollment": {
                "age_mean": 72.0
            }
        }
        resp = requests.post(f"{BASE_URL}/predict", headers=headers, json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "trial_success_probability" in data
        print_result("PASS", f"Tier 2 key accepted, probability: {data['trial_success_probability']:.1%}")
    except Exception as e:
        print_result("FAIL", str(e))

def test_valid_api_key_tier1():
    """Test request with valid Tier 1 API key"""
    print_test("Valid API Key (Tier 1)")
    try:
        headers = {"x-api-key": DEMO_KEY_TIER1}
        payload = {
            "phase": "Phase 2",
            "indication": "Alzheimer's disease",
            "trial_design": {
                "trial_sample_size": 100,
                "trial_duration_weeks": 26,
                "number_of_arms": 2,
                "randomization_ratio": "1:1"
            },
            "endpoints": {
                "endpoint_type": "objective",
                "primary_endpoint_name": "CDR-SB"
            },
            "biomarkers": {},
            "enrollment": {
                "age_mean": 72.0
            }
        }
        resp = requests.post(f"{BASE_URL}/predict", headers=headers, json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "trial_success_probability" in data
        print_result("PASS", f"Tier 1 key accepted, probability: {data['trial_success_probability']:.1%}")
    except Exception as e:
        print_result("FAIL", str(e))

def test_usage_lookup():
    """Test usage statistics endpoint"""
    print_test("API Usage Statistics")
    try:
        resp = requests.get(f"{BASE_URL}/admin/api-keys/usage/{DEMO_KEY_TIER1}")
        assert resp.status_code == 200
        data = resp.json()
        assert "tier" in data
        assert "current_usage" in data
        assert "limit" in data
        assert "remaining" in data
        print_result("PASS", f"Usage lookup successful")
        print(f"Tier: {data['tier']}")
        print(f"Usage: {data['current_usage']}/{data['limit']}")
        print(f"Remaining: {data['remaining']}")
    except Exception as e:
        print_result("FAIL", str(e))

def test_list_keys():
    """Test list all API keys endpoint"""
    print_test("List All API Keys")
    try:
        resp = requests.get(f"{BASE_URL}/admin/api-keys/list")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_keys" in data
        assert "keys" in data
        print_result("PASS", f"List keys successful - {data['total_keys']} keys found")
        for key_info in data["keys"]:
            print(f"  - {key_info['name']} ({key_info['tier']}): {key_info['current_month_usage']} requests")
    except Exception as e:
        print_result("FAIL", str(e))

def test_batch_predictions():
    """Test batch predictions with API key"""
    print_test("Batch Predictions (CSV Upload)")
    try:
        # Create test CSV
        csv_content = """trial_name,trial_sample_size,trial_duration_weeks,endpoint_type,primary_endpoint_name,age_mean
TRIAL-001,200,52,objective,CDR-SB,72.5
TRIAL-002,150,26,subjective,ADAS-Cog,70.0
TRIAL-003,300,52,mixed,ADCOMS,74.2"""
        
        headers = {"x-api-key": DEMO_KEY_TIER2}
        files = {"file": ("test.csv", csv_content)}
        resp = requests.post(f"{BASE_URL}/predict_batch", headers=headers, files=files)
        
        assert resp.status_code == 200
        data = resp.json()
        assert "total_rows" in data
        assert "successful" in data
        assert "failed" in data
        print_result("PASS", f"Batch prediction successful - {data['successful']}/{data['total_rows']} succeeded")
    except Exception as e:
        print_result("FAIL", str(e))

def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("GENIVRA API KEY AUTHENTICATION TESTS")
    print("="*70)
    
    # Check if API is running
    try:
        resp = requests.get(f"{BASE_URL}/", timeout=2)
    except requests.ConnectionError:
        print("\n✗ FAIL: Cannot connect to API at http://localhost:8000")
        print("   Make sure API is running: uvicorn API.main:app --reload")
        return
    
    # Run tests
    test_health_check()
    test_missing_api_key()
    test_invalid_api_key()
    test_valid_api_key_tier2()
    test_valid_api_key_tier1()
    test_usage_lookup()
    test_list_keys()
    test_batch_predictions()
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print("✓ All authentication tests completed")
    print("\nDemo Keys Available:")
    print(f"  Tier 1 (100/month): {DEMO_KEY_TIER1}")
    print(f"  Tier 2 (unlimited): {DEMO_KEY_TIER2}")
    print("\nNext Steps:")
    print("  1. Use demo keys to test in dashboard or CLI")
    print("  2. Create custom API keys via /admin/api-keys/create endpoint")
    print("  3. Monitor usage via /admin/api-keys/usage/{key}")
    print("  4. Reference API_KEY_AUTH_GUIDE.md for production setup")
    print()

if __name__ == "__main__":
    main()
