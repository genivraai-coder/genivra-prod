"""
Trial Success Prediction Module

Loads trained logistic regression model and generates structured predictions
for Alzheimer's Disease Phase II trials.

Provides:
- trial_success_probability (0-1 float)
- risk_tier (HIGH/MEDIUM/LOW)
- top_feature_importance (list of feature names ranked by impact)
- biomarker_explanation (plain-English summary of main drivers)
- confidence_flag (HIGH/MEDIUM/LOW based on data completeness)

Author: Genivra ML Team
Date: February 20, 2026
Version: 1.0
"""

import os
import pickle
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler


# ============================================================================
# Configuration
# ============================================================================

class PredictionConfig:
    """Prediction configuration."""
    
    ARTIFACT_DIR = "models/artifacts"
    MODEL_PATH = os.path.join(ARTIFACT_DIR, "logistic_model.pkl")
    SCALER_PATH = os.path.join(ARTIFACT_DIR, "feature_scaler.pkl")
    
    # Risk tier thresholds (from ML_SCOPE.md)
    RISK_THRESHOLDS = {
        "HIGH": 0.40,    # < 0.40 = HIGH risk
        "MEDIUM": 0.70,  # 0.40 - 0.69 = MEDIUM risk
        "LOW": 1.0       # >= 0.70 = LOW risk
    }
    
    # Required biomarker fields for HIGH confidence (marked as "Yes" in feature catalog)
    REQUIRED_BIOMARKERS = [
        "apoe_e4_carrier",           # APOE ε4 Genotype
        "ptau217_high",              # Plasma p-tau217
        "amyloid_pet_positive",      # Amyloid PET
        "age_mean",                  # Baseline age
        "baseline_mmse",             # MMSE score (cognitive severity)
        "cdr_baseline",              # CDR-SB (preferred cognitive endpoint)
        "trial_sample_size",         # Study enrollment
        "trial_duration_weeks",      # Study duration
        "endpoint_type",             # Objective vs. subjective endpoint
        "primary_endpoint_name",     # Specific endpoint (CDR-SB, ADAS-Cog, etc.)
        "biomarker_enrichment_strategy",  # Trial enrichment approach
    ]
    
    # Features that were one-hot encoded during training
    # (these will be handled separately in engineering)
    CATEGORICAL_FEATURES = [
        "endpoint_type",
        "primary_endpoint_name",
        "biomarker_enrichment_strategy",
        "randomization_ratio",
    ]
    
    # Features to exclude from raw input (same as training)
    EXCLUDE_FEATURES = [
        "trial_id",
        "trial_success_probability",
        "trial_success",
    ]
    
    # Expected ordered features from scaler (after one-hot encoding)
    # This matches the exact output of the training pipeline
    EXPECTED_FEATURES = [
        "apoe_e4_carrier",
        "apoe_e4_homozygous",
        "ptau217_continuous",
        "ptau217_high",
        "csf_abeta42_40_ratio_continuous",
        "csf_abeta42_40_ratio_low",
        "csf_ptau_elevated",
        "amyloid_pet_positive",
        "tau_pet_positive",
        "hippocampal_atrophy_mri",
        "hippocampal_atrophy_binary",
        "age_mean",
        "baseline_mmse",
        "baseline_moca",
        "cdr_baseline",
        "trial_sample_size",
        "trial_duration_weeks",
        "number_of_arms",
        "endpoint_type_objective",
        "endpoint_type_subjective",
        "primary_endpoint_name_ADCOMS",
        "primary_endpoint_name_CDR-SB",
        "primary_endpoint_name_MMSE",
        "biomarker_enrichment_strategy_at_positive",
        "biomarker_enrichment_strategy_cognitive_only",
        "biomarker_enrichment_strategy_none",
        "biomarker_enrichment_strategy_tau_positive",
        "randomization_ratio_2:1",
        "randomization_ratio_open_label",
    ]
    
    # All possible one-hot encoded feature values (from training data)
    # Maps categorical feature -> list of possible encoded names
    ONE_HOT_FEATURES = {
        "endpoint_type": [
            "endpoint_type_objective",
            "endpoint_type_subjective",
        ],
        "primary_endpoint_name": [
            "primary_endpoint_name_ADCOMS",
            "primary_endpoint_name_CDR-SB",
            "primary_endpoint_name_MMSE",
        ],
        "biomarker_enrichment_strategy": [
            "biomarker_enrichment_strategy_at_positive",
            "biomarker_enrichment_strategy_cognitive_only",
            "biomarker_enrichment_strategy_none",
            "biomarker_enrichment_strategy_tau_positive",
        ],
        "randomization_ratio": [
            "randomization_ratio_2:1",
            "randomization_ratio_open_label",
        ],
    }


# ============================================================================
# Model Loading
# ============================================================================

def load_model_and_scaler() -> Tuple[Any, StandardScaler]:
    """
    Load trained logistic regression model and feature scaler from artifacts.
    
    Returns:
        Tuple of (model, scaler)
    
    Raises:
        FileNotFoundError: If model or scaler files not found.
    """
    if not os.path.exists(PredictionConfig.MODEL_PATH):
        raise FileNotFoundError(
            f"Model not found at {PredictionConfig.MODEL_PATH}. "
            "Run Models/train_logistic_regression.py first."
        )
    
    if not os.path.exists(PredictionConfig.SCALER_PATH):
        raise FileNotFoundError(
            f"Scaler not found at {PredictionConfig.SCALER_PATH}. "
            "Run Models/train_logistic_regression.py first."
        )
    
    with open(PredictionConfig.MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    
    with open(PredictionConfig.SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)
    
    return model, scaler


# ============================================================================
# Feature Engineering (matching train_logistic_regression.py)
# ============================================================================

def engineer_features(input_dict: Dict[str, Any]) -> Tuple[pd.DataFrame, List[str]]:
    """
    Convert raw trial input dict to engineered features matching training pipeline.
    
    Performs the same transformations as train_logistic_regression.py:
    1. Select 22 base features (exclude target-related fields)
    2. Fill missing values (median for numerical, "unknown" for categorical)
    3. One-hot encode categorical features
    4. Reorder to match expected feature order
    
    Args:
        input_dict: Raw trial data with 22 features.
    
    Returns:
        Tuple of (engineered_features DataFrame, feature_names list)
    """
    # Start with input dict
    X = pd.DataFrame([input_dict]).copy()
    
    # Fill missing values in numerical columns
    numerical_cols = [
        "apoe_e4_carrier", "apoe_e4_homozygous", "ptau217_continuous", "ptau217_high",
        "csf_abeta42_40_ratio_continuous", "csf_abeta42_40_ratio_low", "csf_ptau_elevated",
        "amyloid_pet_positive", "tau_pet_positive", "hippocampal_atrophy_mri",
        "hippocampal_atrophy_binary", "age_mean", "baseline_mmse", "baseline_moca",
        "cdr_baseline", "trial_sample_size", "trial_duration_weeks", "number_of_arms"
    ]
    
    for col in numerical_cols:
        if col in X.columns:
            X[col] = pd.to_numeric(X[col], errors='coerce')
            if X[col].isnull().any():
                X[col] = X[col].fillna(0.0)
        else:
            # Add missing numerical columns with 0
            X[col] = 0.0
    
    # Handle categorical columns
    categorical_cols = [
        "endpoint_type", "primary_endpoint_name", 
        "biomarker_enrichment_strategy", "randomization_ratio"
    ]
    
    for col in categorical_cols:
        if col in X.columns:
            X[col] = X[col].fillna("unknown")
            X[col] = X[col].astype(str)
        else:
            # Add missing categorical columns with "unknown"
            X[col] = "unknown"
    
    # One-hot encode categorical features (with drop_first=True as in training)
    X_encoded = pd.get_dummies(X, columns=categorical_cols, drop_first=True)
    
    # Now we need to add any missing encoded features with 0 values
    for feature in PredictionConfig.EXPECTED_FEATURES:
        if feature not in X_encoded.columns:
            X_encoded[feature] = 0
    
    # Reorder columns to match expected feature order
    X_final = X_encoded[PredictionConfig.EXPECTED_FEATURES].copy()
    
    return X_final, PredictionConfig.EXPECTED_FEATURES


# ============================================================================
# Feature Importance Extraction
# ============================================================================

def get_top_features(
    model: Any,
    feature_names: List[str],
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Extract top K most important features from logistic regression model.
    
    Importance is measured by absolute value of coefficient magnitude.
    
    Args:
        model: Trained logistic regression model.
        feature_names: List of feature names in same order as model.coef_.
        top_k: Number of top features to return.
    
    Returns:
        List of dicts with feature name, importance score, and direction.
    """
    # Extract coefficients
    coefficients = model.coef_[0]
    
    # Create (feature_name, coefficient) pairs
    feature_importance = list(zip(feature_names, coefficients))
    
    # Sort by absolute value of coefficient (descending)
    feature_importance_sorted = sorted(
        feature_importance,
        key=lambda x: abs(x[1]),
        reverse=True
    )
    
    # Build output list
    top_features = []
    for rank, (feature_name, coef) in enumerate(feature_importance_sorted[:top_k], 1):
        direction = "increases_probability" if coef > 0 else "decreases_probability"
        
        top_features.append({
            "rank": rank,
            "feature": feature_name,
            "coefficient": float(coef),
            "importance_score": float(abs(coef)),
            "direction": direction
        })
    
    return top_features


# ============================================================================
# Risk Tier Assignment
# ============================================================================

def get_risk_tier(success_probability: float) -> str:
    """
    Map success probability to risk tier.
    
    Args:
        success_probability: Predicted probability (0-1).
    
    Returns:
        Risk tier: "LOW", "MEDIUM", or "HIGH".
    
    Note:
        - HIGH risk: <0.40 (failure likely)
        - MEDIUM risk: 0.40-0.69 (uncertain)
        - LOW risk: >=0.70 (success likely)
    """
    if success_probability >= PredictionConfig.RISK_THRESHOLDS["MEDIUM"]:
        return "LOW"
    elif success_probability >= PredictionConfig.RISK_THRESHOLDS["HIGH"]:
        return "MEDIUM"
    else:
        return "HIGH"


# ============================================================================
# Confidence Assessment
# ============================================================================

def assess_confidence(input_dict: Dict[str, Any]) -> Tuple[str, int]:
    """
    Assess prediction confidence based on biomarker data completeness.
    
    Args:
        input_dict: Raw trial input dict.
    
    Returns:
        Tuple of (confidence_flag, missing_count)
    """
    missing_required = 0
    
    for biomarker in PredictionConfig.REQUIRED_BIOMARKERS:
        value = input_dict.get(biomarker)
        
        # Check if missing or null
        if value is None or (isinstance(value, float) and np.isnan(value)):
            missing_required += 1
        # For string features, check if "unknown"
        elif isinstance(value, str) and value.lower() == "unknown":
            missing_required += 1
    
    # Assign confidence based on count
    if missing_required == 0:
        confidence_flag = "HIGH"
    elif missing_required <= 2:
        confidence_flag = "MEDIUM"
    else:
        confidence_flag = "LOW"
    
    return confidence_flag, missing_required


# ============================================================================
# Biomarker Explanation Generation
# ============================================================================

def generate_biomarker_explanation(
    input_dict: Dict[str, Any],
    top_features: List[Dict[str, Any]],
    success_probability: float
) -> str:
    """
    Generate plain-English explanation of main biomarker drivers.
    
    Args:
        input_dict: Raw trial input dict.
        top_features: Top 5 features from model.
        success_probability: Predicted success probability.
    
    Returns:
        Natural language explanation string.
    """
    explanation_parts = []
    
    # Start with biomarker profile
    biomarker_profile = []
    
    if input_dict.get("amyloid_pet_positive") == 1:
        biomarker_profile.append("amyloid PET positive")
    
    if input_dict.get("ptau217_high") == 1:
        biomarker_profile.append("elevated plasma p-tau217")
    
    if input_dict.get("apoe_e4_carrier") == 1:
        if input_dict.get("apoe_e4_homozygous") == 1:
            biomarker_profile.append("APOE e4 homozygous")
        else:
            biomarker_profile.append("APOE e4 carrier")
    
    if biomarker_profile:
        profile_str = " and ".join(biomarker_profile)
        explanation_parts.append(
            f"This trial enrolls participants with {profile_str} biomarker profile."
        )
    
    # Add trial design info
    enrichment = input_dict.get("biomarker_enrichment_strategy", "unknown")
    if enrichment and enrichment != "unknown":
        explanation_parts.append(
            f"Enrichment strategy is '{enrichment}', targeting specific biomarker populations."
        )
    
    # Add sample size and duration context
    sample_size = input_dict.get("trial_sample_size")
    duration = input_dict.get("trial_duration_weeks")
    
    design_comments = []
    if sample_size and sample_size >= 250:
        design_comments.append("adequate sample size")
    elif sample_size and sample_size < 100:
        design_comments.append("smaller sample size")
    
    if duration and duration >= 52:
        design_comments.append("extended follow-up duration")
    elif duration and duration < 24:
        design_comments.append("shorter trial duration")
    
    if design_comments:
        design_str = " and ".join(design_comments)
        explanation_parts.append(f"Trial design includes {design_str}.")
    
    # Risk assessment
    prob_pct = success_probability * 100
    if success_probability >= 0.70:
        risk_desc = "strong evidence for success"
    elif success_probability >= 0.40:
        risk_desc = "moderate evidence for success"
    else:
        risk_desc = "elevated failure risk"
    
    explanation_parts.append(
        f"Model predicts {prob_pct:.0f}% success probability, indicating {risk_desc}."
    )
    
    # Top drivers
    if top_features:
        top_drivers = []
        for feat in top_features[:2]:  # Top 2 features
            direction = "increases" if "increases" in feat["direction"] else "decreases"
            top_drivers.append(f"{feat['feature'].replace('_', ' ')} ({direction} success)")
        
        if top_drivers:
            drivers_str = " and ".join(top_drivers)
            explanation_parts.append(
                f"Primary model drivers: {drivers_str}."
            )
    
    return " ".join(explanation_parts)


# ============================================================================
# Main Prediction Function
# ============================================================================

def predict_trial(input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Predict trial success probability and generate structured output.
    
    Args:
        input_dict: Raw trial data dict with up to 22 features:
            Required: apoe_e4_carrier, ptau217_high, amyloid_pet_positive,
                      age_mean, baseline_mmse, cdr_baseline, trial_sample_size,
                      trial_duration_weeks, endpoint_type, primary_endpoint_name,
                      biomarker_enrichment_strategy
            Optional: apoe_e4_homozygous, ptau217_continuous, csf_abeta42_40_ratio_low,
                      csf_abeta42_40_ratio_continuous, csf_ptau_elevated, tau_pet_positive,
                      hippocampal_atrophy_mri, hippocampal_atrophy_binary, baseline_moca,
                      number_of_arms, randomization_ratio
    
    Returns:
        Structured dict with:
        - trial_success_probability (float, 0-1)
        - risk_tier (str: "HIGH", "MEDIUM", "LOW")
        - top_feature_importance (list of dicts)
        - biomarker_explanation (str)
        - confidence_flag (str: "HIGH", "MEDIUM", "LOW")
        - missing_biomarker_count (int)
        - model_version (str)
        - generated_timestamp (str)
    
    Example:
        >>> trial_data = {
        ...     "apoe_e4_carrier": 1,
        ...     "ptau217_high": 1,
        ...     "amyloid_pet_positive": 1,
        ...     "age_mean": 72.5,
        ...     "baseline_mmse": 23,
        ...     "cdr_baseline": 0.5,
        ...     "trial_sample_size": 200,
        ...     "trial_duration_weeks": 52,
        ...     "endpoint_type": "objective",
        ...     "primary_endpoint_name": "CDR-SB",
        ...     "biomarker_enrichment_strategy": "amyloid_positive",
        ...     # ... additional optional fields
        ... }
        >>> result = predict_trial(trial_data)
        >>> print(f"Success probability: {result['trial_success_probability']:.2%}")
        >>> print(f"Risk tier: {result['risk_tier']}")
    """
    
    try:
        # 1. Load model and scaler
        model, scaler = load_model_and_scaler()
        
        # 2. Engineer features
        X_engineered, feature_names = engineer_features(input_dict)
        
        # 3. Scale features (matching training pipeline)
        X_scaled = scaler.transform(X_engineered)
        
        # 4. Get prediction probability
        success_probability = float(model.predict_proba(X_scaled)[0, 1])
        
        # 5. Assign risk tier
        risk_tier = get_risk_tier(success_probability)
        
        # 6. Extract top features
        top_features = get_top_features(model, feature_names, top_k=5)
        
        # 7. Assess confidence
        confidence_flag, missing_count = assess_confidence(input_dict)
        
        # 8. Generate explanation
        biomarker_explanation = generate_biomarker_explanation(
            input_dict,
            top_features,
            success_probability
        )
        
        # 9. Build output dict
        output = {
            "trial_success_probability": success_probability,
            "risk_tier": risk_tier,
            "top_feature_importance": top_features,
            "biomarker_explanation": biomarker_explanation,
            "confidence_flag": confidence_flag,
            "missing_biomarker_count": missing_count,
            "model_version": "v1.0",
            "generated_timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
        return output
    
    except Exception as e:
        # Return error response
        return {
            "error": str(e),
            "trial_success_probability": None,
            "risk_tier": "ERROR",
            "confidence_flag": "ERROR",
            "generated_timestamp": datetime.utcnow().isoformat() + "Z",
        }


# ============================================================================
# Batch Prediction
# ============================================================================

def predict_trials_batch(trials_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Predict success for multiple trials.
    
    Args:
        trials_list: List of trial input dicts.
    
    Returns:
        List of prediction dicts (one per trial).
    """
    results = []
    for trial in trials_list:
        result = predict_trial(trial)
        results.append(result)
    
    return results


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Example trial data
    example_trial = {
        "apoe_e4_carrier": 1,
        "apoe_e4_homozygous": 0,
        "ptau217_high": 1,
        "ptau217_continuous": 18.5,
        "csf_abeta42_40_ratio_low": 1,
        "csf_abeta42_40_ratio_continuous": 0.42,
        "csf_ptau_elevated": 1,
        "amyloid_pet_positive": 1,
        "tau_pet_positive": 0,
        "hippocampal_atrophy_mri": 3.8,
        "hippocampal_atrophy_binary": 1,
        "age_mean": 72.5,
        "baseline_mmse": 23,
        "baseline_moca": 22,
        "cdr_baseline": 0.5,
        "trial_sample_size": 234,
        "trial_duration_weeks": 52,
        "endpoint_type": "objective",
        "primary_endpoint_name": "CDR-SB",
        "biomarker_enrichment_strategy": "amyloid_positive",
        "number_of_arms": 2,
        "randomization_ratio": "1:1",
    }
    
    # Make prediction
    result = predict_trial(example_trial)
    
    # Print results
    print("\n" + "=" * 80)
    print("TRIAL SUCCESS PREDICTION")
    print("=" * 80)
    
    # Check for errors
    if "error" in result:
        print(f"\n❌ ERROR: {result['error']}")
    else:
        print(f"\nTrial Success Probability: {result['trial_success_probability']:.1%}")
        print(f"Risk Tier: {result['risk_tier']}")
        print(f"Confidence: {result['confidence_flag']}")
        print(f"Missing Biomarkers: {result['missing_biomarker_count']}")
        
        print("\nTop Features:")
        for feat in result['top_feature_importance']:
            print(f"  {feat['rank']}. {feat['feature']}: {feat['coefficient']:+.4f} ({feat['direction']})")
        
        print(f"\nExplanation:\n  {result['biomarker_explanation']}")
    
    print("\n" + "=" * 80)
