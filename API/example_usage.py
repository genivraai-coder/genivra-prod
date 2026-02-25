"""
Example script demonstrating how to call the Genivra API.

This script shows how to:
1. Start the API server
2. Send a prediction request
3. Parse the response

Run the API first:
    uvicorn API.main:app --reload

Then run this script:
    python API/example_usage.py
"""

import requests
import json
from datetime import datetime

# ============================================================================
# API Configuration
# ============================================================================

API_URL = "http://localhost:8000"
PREDICT_ENDPOINT = f"{API_URL}/predict"
HEALTH_ENDPOINT = f"{API_URL}/health"


# ============================================================================
# Example Prediction Payloads
# ============================================================================

LECANEMAB_LIKE_TRIAL = {
    "phase": "Phase II",
    "indication": "Alzheimer's Disease",
    "trial_design": {
        "phase": "Phase II",
        "indication": "Alzheimer's Disease",
        "trial_sample_size": 150,
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
        "tau_pet_positive": 1,
        "hippocampal_atrophy_binary": 1
    },
    "enrollment": {
        "age_mean": 70.0,
        "baseline_mmse": 20.0,
        "cdr_baseline": 1.0
    },
    "biomarker_enrichment_strategy": "at_positive"
}

HIGH_RISK_TRIAL = {
    "phase": "Phase II",
    "indication": "Alzheimer's Disease",
    "trial_design": {
        "trial_sample_size": 50,
        "trial_duration_weeks": 12,
        "number_of_arms": 2,
        "randomization_ratio": "1:1"
    },
    "endpoints": {
        "endpoint_type": "subjective",
        "primary_endpoint_name": "MMSE"
    },
    "biomarkers": {
        "apoe_e4_carrier": 0,
        "ptau217_high": 0,
        "amyloid_pet_positive": 0,
        "tau_pet_positive": 0
    },
    "enrollment": {
        "age_mean": 65.0,
        "baseline_mmse": 26.0,
        "cdr_baseline": 0.5
    },
    "biomarker_enrichment_strategy": "cognitive_only"
}


# ============================================================================
# API Functions
# ============================================================================

def check_health():
    """Check if API is running."""
    try:
        response = requests.get(HEALTH_ENDPOINT)
        if response.status_code == 200:
            print("✓ API is running")
            return True
        else:
            print(f"✗ API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("✗ Could not connect to API. Make sure it's running:")
        print("  uvicorn API.main:app --reload")
        return False


def predict_trial(payload):
    """
    Send a prediction request to the API.
    
    Args:
        payload: Dictionary with trial parameters
    
    Returns:
        dict: API response or None if failed
    """
    try:
        response = requests.post(
            PREDICT_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: API returned status {response.status_code}")
            print(f"Response: {response.text}")
            return None
    
    except Exception as e:
        print(f"Error calling API: {str(e)}")
        return None


def print_prediction(result):
    """Pretty-print prediction results."""
    if not result:
        return
    
    print("\n" + "=" * 80)
    print("PREDICTION RESULTS")
    print("=" * 80)
    print(f"Success Probability: {result['trial_success_probability']:.1%}")
    print(f"Risk Tier: {result['risk_tier']}")
    print(f"Confidence: {result['confidence_flag']}")
    print(f"Model Version: {result['model_version']}")
    print(f"Timestamp: {result['generated_timestamp']}")
    
    print("\nTop Drivers:")
    for i, driver in enumerate(result['top_drivers'][:3], 1):
        direction = "↑" if driver['direction'] == 'positive' else "↓"
        print(f"  {i}. {driver['feature_name']} ({direction}) - Impact: {driver['impact_magnitude']:.3f}")
    
    print(f"\nBiomarker Explanation:")
    print(f"  {result['biomarker_explanation']}")
    
    print("=" * 80 + "\n")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("Genivra API Example Client")
    print("=" * 80 + "\n")
    
    # Check health
    if not check_health():
        exit(1)
    
    # Test Case 1: Lecanemab-like (high success)
    print("\n--- Test 1: High-Success Lecanemab-like Trial ---")
    result1 = predict_trial(LECANEMAB_LIKE_TRIAL)
    print_prediction(result1)
    
    # Test Case 2: High-risk trial
    print("\n--- Test 2: High-Risk Trial ---")
    result2 = predict_trial(HIGH_RISK_TRIAL)
    print_prediction(result2)
    
    print("✓ Example complete!")
