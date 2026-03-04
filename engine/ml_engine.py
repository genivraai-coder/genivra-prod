"""
Genivra ML Engine - Consolidated Core ML Module

Unified machine learning engine combining:
- Data loading and synthetic trial generation
- Feature engineering and preprocessing
- Model training (logistic regression + decision tree)
- Trial prediction with interpretability
- Rule-based scoring baseline
- Utility functions

This module serves as the single source of truth for all ML operations.
All API endpoints should import from here.

Author: Genivra ML Team
Date: March 3, 2026
Version: 2.0 (Consolidated)
"""

# ====== IMPORTS ======
import os
import pickle
import warnings
from typing import Dict, Tuple, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
    roc_curve,
    auc,
)

warnings.filterwarnings("ignore", category=DeprecationWarning)


# ====== CONFIGURATION ======

class MLConfig:
    """Machine learning engine configuration."""
    
    # Paths
    DATA_PATH = "data/processed/synthetic_ad_trials.csv"
    ARTIFACT_DIR = "models/artifacts"
    MODEL_SAVE_PATH = os.path.join(ARTIFACT_DIR, "logistic_model.pkl")
    SCALER_SAVE_PATH = os.path.join(ARTIFACT_DIR, "feature_scaler.pkl")
    TREE_MODEL_SAVE_PATH = os.path.join(ARTIFACT_DIR, "decision_tree_model.pkl")
    
    # Training parameters
    TEST_SIZE = 0.20
    RANDOM_STATE = 42
    
    # Features to exclude from training
    EXCLUDE_FEATURES = [
        "trial_id",
        "trial_success_probability",
        "trial_success",
    ]
    
    # Risk tier thresholds (success probability cutoffs)
    RISK_THRESHOLDS = {
        "HIGH": 0.40,    # < 0.40 = HIGH risk
        "MEDIUM": 0.70,  # 0.40 - 0.69 = MEDIUM risk
        "LOW": 1.0       # >= 0.70 = LOW risk
    }
    
    # Required biomarkers for HIGH confidence
    REQUIRED_BIOMARKERS = [
        "apoe_e4_carrier",
        "ptau217_high",
        "amyloid_pet_positive",
        "age_mean",
        "baseline_mmse",
        "cdr_baseline",
        "trial_sample_size",
        "trial_duration_weeks",
        "endpoint_type",
        "primary_endpoint_name",
        "biomarker_enrichment_strategy",
    ]
    
    # Categorical features that need one-hot encoding
    CATEGORICAL_FEATURES = [
        "endpoint_type",
        "primary_endpoint_name",
        "biomarker_enrichment_strategy",
        "randomization_ratio",
    ]
    
    # Expected features after one-hot encoding (in training order)
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


class RuleBasedWeights:
    """Rule-based scoring weights encoding clinical domain knowledge."""
    
    # Biomarker contributions
    AMYLOID_PET_POSITIVE = 0.25
    PTAU217_HIGH = 0.20
    CSF_ABETA42_40_LOW = 0.15
    CSF_PTAU_ELEVATED = 0.12
    TAU_PET_POSITIVE = 0.10
    APOE_E4_CARRIER = 0.15
    APOE_E4_HOMOZYGOUS = 0.08
    HIPPOCAMPAL_ATROPHY = 0.05
    
    # Trial design contributions
    LONG_DURATION_GE_52_WEEKS = 0.10
    MEDIUM_DURATION_GE_36_WEEKS = 0.05
    ADEQUATE_SAMPLE_SIZE_GE_250 = 0.08
    GOOD_SAMPLE_SIZE_GE_150 = 0.04
    GOOD_ENDPOINT_TYPE_MIXED = 0.02
    GOOD_PRIMARY_ENDPOINT = 0.05
    RANDOMIZED_STRUCTURE = 0.03
    ADAPTIVE_RANDOMIZATION = 0.02
    
    # Cognitive stage contributions
    BASELINE_MMSE_MCI_SWEET_SPOT = 0.10
    BASELINE_MMSE_MILD_DEMENTIA = 0.03
    HIPPOCAMPAL_VOLUME_NORMAL = 0.05
    
    # Enrichment bonus
    ENRICHMENT_AT_POSITIVE = 0.08
    ENRICHMENT_AMYLOID_POSITIVE = 0.06
    
    # Age adjustment
    AGE_SWEET_SPOT_60_75 = 0.04
    
    # Penalties
    SMALL_SAMPLE_LT_100 = -0.20
    MEDIUM_SMALL_SAMPLE_LT_150 = -0.10
    SHORT_DURATION_LT_24_WEEKS = -0.12
    MEDIUM_SHORT_DURATION_LT_36_WEEKS = -0.06
    ADVANCED_DEMENTIA_MMSE_LT_16 = -0.20
    VERY_ADVANCED_DEMENTIA_MMSE_LT_10 = -0.30
    MILD_COGNITIVE_DECLINE_MMSE_GT_26 = -0.08
    NO_ENRICHMENT = -0.10
    OPEN_LABEL_STRUCTURE = -0.08
    OBJECTIVE_ENDPOINT_ONLY = -0.05
    UNCOMMON_ENDPOINT = -0.03
    
    # Age penalties
    AGE_LT_60 = -0.05
    AGE_GT_80 = -0.06


# ====== DATA LOADING FUNCTIONS ======

def load_and_prepare_data(data_path: str) -> Tuple[pd.DataFrame, pd.Series, list]:
    """
    Load synthetic trial data and prepare for training.
    
    Args:
        data_path: Path to CSV file with trial data.
    
    Returns:
        Tuple of (X: features DataFrame, y: labels Series, feature_names: list)
    """
    print(f"Loading data from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"  ✓ Loaded {len(df)} trials with {len(df.columns)} columns")
    
    # Extract labels
    y = df["trial_success"]
    print(f"  ✓ Labels: {y.value_counts().to_dict()}")
    
    # Select features
    feature_cols = [
        col for col in df.columns 
        if col not in MLConfig.EXCLUDE_FEATURES
    ]
    X = df[feature_cols].copy()
    
    print(f"  ✓ Selected {len(feature_cols)} features for training")
    
    # Handle missing values
    missing_per_col = X.isnull().sum()
    cols_with_missing = missing_per_col[missing_per_col > 0]
    
    if len(cols_with_missing) > 0:
        print(f"\n  ⚠ Found missing values:")
        for col, count in cols_with_missing.items():
            print(f"    - {col}: {count} missing ({count/len(X)*100:.1f}%)")
        
        # Fill missing with median for numerical, mode for categorical
        for col in X.columns:
            if X[col].dtype in ['float64', 'int64']:
                X[col] = X[col].fillna(X[col].median())
            else:
                mode_val = X[col].mode()[0] if len(X[col].mode()) > 0 else "unknown"
                X[col] = X[col].fillna(mode_val)
        print(f"  ✓ Filled missing values")
    
    # Convert categorical features to numeric via one-hot encoding
    categorical_cols = X.select_dtypes(include=['object']).columns.tolist()
    if len(categorical_cols) > 0:
        print(f"\n  ⚠ Found {len(categorical_cols)} categorical features")
        X = pd.get_dummies(X, columns=categorical_cols, drop_first=True)
        print(f"  ✓ One-hot encoded categorical features")
        print(f"    New shape: {X.shape}")
    
    return X, y, X.columns.tolist()


# ====== FEATURE ENGINEERING ======

def engineer_features(input_dict: Dict[str, Any]) -> Tuple[pd.DataFrame, List[str]]:
    """
    Convert raw trial input to engineered features matching training pipeline.
    
    Args:
        input_dict: Raw trial data with all fields.
    
    Returns:
        Tuple of (engineered_features DataFrame, feature_names list)
    """
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
            X[col] = "unknown"
    
    # One-hot encode categorical features
    X_encoded = pd.get_dummies(X, columns=categorical_cols, drop_first=True)
    
    # Add missing encoded features with 0 values
    for feature in MLConfig.EXPECTED_FEATURES:
        if feature not in X_encoded.columns:
            X_encoded[feature] = 0
    
    # Reorder columns to match expected feature order
    X_final = X_encoded[MLConfig.EXPECTED_FEATURES].copy()
    
    return X_final, MLConfig.EXPECTED_FEATURES


# ====== MODEL TRAINING ======

def train_model(X_train: pd.DataFrame, y_train: pd.Series) -> Tuple[LogisticRegression, StandardScaler]:
    """
    Train logistic regression model.
    
    Args:
        X_train: Training features.
        y_train: Training labels.
    
    Returns:
        Tuple of (trained model, fitted scaler)
    """
    print("\nTraining Logistic Regression Model")
    print("=" * 80)
    
    # Standardize features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    # Train model
    model = LogisticRegression(
        max_iter=1000,
        random_state=MLConfig.RANDOM_STATE,
        solver="lbfgs",
        class_weight="balanced",
        verbose=0
    )
    
    model.fit(X_train_scaled, y_train)
    
    print(f"  ✓ Model trained")
    print(f"    Intercept: {model.intercept_[0]:.4f}")
    print(f"    Coefficients learned: {len(model.coef_[0])} features")
    
    return model, scaler


def evaluate_model(
    model: LogisticRegression,
    scaler: StandardScaler,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    feature_names: list
) -> Dict:
    """
    Evaluate model on test set.
    
    Args:
        model: Trained model.
        scaler: Fitted feature scaler.
        X_test: Test features.
        y_test: Test labels.
        feature_names: List of feature names.
    
    Returns:
        Dictionary with evaluation metrics.
    """
    print("\nModel Evaluation")
    print("=" * 80)
    
    # Scale test features
    X_test_scaled = scaler.transform(X_test)
    
    # Predictions
    y_pred = model.predict(X_test_scaled)
    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
    
    # Metrics
    accuracy = accuracy_score(y_test, y_pred)
    auc_score = roc_auc_score(y_test, y_pred_proba)
    cm = confusion_matrix(y_test, y_pred)
    
    print(f"  ✓ Accuracy: {accuracy:.4f}")
    print(f"  ✓ AUC: {auc_score:.4f}")
    print(f"  ✓ Confusion Matrix:\n{cm}")
    
    return {
        "accuracy": accuracy,
        "auc": auc_score,
        "confusion_matrix": cm.tolist(),
    }


def save_model(model: LogisticRegression, scaler: StandardScaler, model_path: str = None, scaler_path: str = None):
    """
    Save trained model and scaler to disk.
    
    Args:
        model: Trained model object.
        scaler: Fitted scaler object.
        model_path: Path to save model (default: MLConfig.MODEL_SAVE_PATH).
        scaler_path: Path to save scaler (default: MLConfig.SCALER_SAVE_PATH).
    """
    model_path = model_path or MLConfig.MODEL_SAVE_PATH
    scaler_path = scaler_path or MLConfig.SCALER_SAVE_PATH
    
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"  ✓ Model saved to {model_path}")
    
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)
    print(f"  ✓ Scaler saved to {scaler_path}")


# ====== PREDICTION FUNCTIONS ======

def load_model_and_scaler(model_path: str = None, scaler_path: str = None) -> Tuple[Any, StandardScaler]:
    """
    Load trained model and scaler from disk.
    
    Args:
        model_path: Path to model (default: MLConfig.MODEL_SAVE_PATH).
        scaler_path: Path to scaler (default: MLConfig.SCALER_SAVE_PATH).
    
    Returns:
        Tuple of (model, scaler)
    
    Raises:
        FileNotFoundError: If model or scaler not found.
    """
    model_path = model_path or MLConfig.MODEL_SAVE_PATH
    scaler_path = scaler_path or MLConfig.SCALER_SAVE_PATH
    
    if not os.path.exists(model_path):
        raise FileNotFoundError(
            f"Model not found at {model_path}. "
            "Run ml_engine.train_full_pipeline() first."
        )
    
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(
            f"Scaler not found at {scaler_path}. "
            "Run ml_engine.train_full_pipeline() first."
        )
    
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    
    return model, scaler


def get_top_features(
    model: Any,
    feature_names: List[str],
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Extract top K most important features from model.
    
    Args:
        model: Trained logistic regression model.
        feature_names: List of feature names.
        top_k: Number of top features to return.
    
    Returns:
        List of dicts with feature info and importance.
    """
    coefficients = model.coef_[0]
    feature_importance = list(zip(feature_names, coefficients))
    feature_importance_sorted = sorted(
        feature_importance,
        key=lambda x: abs(x[1]),
        reverse=True
    )
    
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


def get_risk_tier(success_probability: float) -> str:
    """
    Map success probability to risk tier.
    
    Args:
        success_probability: Predicted probability (0-1).
    
    Returns:
        Risk tier: "LOW", "MEDIUM", or "HIGH"
    """
    if success_probability >= MLConfig.RISK_THRESHOLDS["MEDIUM"]:
        return "LOW"
    elif success_probability >= MLConfig.RISK_THRESHOLDS["HIGH"]:
        return "MEDIUM"
    else:
        return "HIGH"


def predict_trial(input_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Predict trial success using trained logistic regression model.
    
    Complete prediction function that:
    1. Engineers input features
    2. Loads model and scaler
    3. Generates probability prediction
    4. Assigns risk tier
    5. Extracts feature importance
    6. Assesses confidence
    7. Returns structured output
    
    Args:
        input_dict: Raw trial data with all required fields.
    
    Returns:
        Dictionary with:
        - trial_success_probability (float)
        - risk_tier (str)
        - top_drivers (list of dicts)
        - biomarker_explanation (str)
        - confidence_flag (str)
        - missing_biomarker_count (int)
    """
    # Engineer features
    X_engineered, feature_names = engineer_features(input_dict)
    
    # Load model and scaler
    try:
        model, scaler = load_model_and_scaler()
    except FileNotFoundError as e:
        raise RuntimeError(f"Cannot load model: {e}")
    
    # Scale features
    X_scaled = scaler.transform(X_engineered)
    
    # Predict probability
    probability = float(model.predict_proba(X_scaled)[0, 1])
    
    # Get risk tier
    risk_tier = get_risk_tier(probability)
    
    # Get top features
    top_features = get_top_features(model, feature_names, top_k=5)
    
    # Calculate confidence
    missing_count = sum(1 for field in MLConfig.REQUIRED_BIOMARKERS 
                       if input_dict.get(field) is None)
    
    if missing_count == 0:
        confidence = "HIGH"
    elif missing_count <= 3:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
    
    # Generate biomarker explanation
    explanation = _generate_biomarker_explanation(input_dict, top_features, risk_tier)
    
    return {
        "trial_success_probability": probability,
        "risk_tier": risk_tier,
        "top_drivers": top_features,
        "biomarker_explanation": explanation,
        "confidence_flag": confidence,
        "missing_biomarker_count": missing_count,
    }


def _generate_biomarker_explanation(
    input_dict: Dict[str, Any],
    top_features: List[Dict],
    risk_tier: str
) -> str:
    """
    Generate plain-English explanation of biomarker influences.
    
    Args:
        input_dict: Input trial data.
        top_features: Top feature drivers.
        risk_tier: Assessed risk tier.
    
    Returns:
        Plain-English explanation string.
    """
    explanation = f"Trial classified as {risk_tier} risk. "
    
    positive_features = [f["feature"] for f in top_features if f["direction"] == "increases_probability"]
    negative_features = [f["feature"] for f in top_features if f["direction"] == "decreases_probability"]
    
    if positive_features:
        explanation += f"Positive drivers: {', '.join(positive_features[:2])}. "
    
    if negative_features:
        explanation += f"Concerns: {', '.join(negative_features[:2])}. "
    
    explanation += "Review complete results for full feature analysis."
    
    return explanation


# ====== RULE-BASED SCORING ======

class TrialScorer:
    """Rule-based scorer for trial success using deterministic biomarker weights."""
    
    def __init__(self, weights: RuleBasedWeights = None):
        """
        Initialize scorer.
        
        Args:
            weights: RuleBasedWeights object. Uses defaults if None.
        """
        self.weights = weights or RuleBasedWeights()
    
    def score_trial(self, trial: Dict) -> Dict:
        """
        Score trial based on biomarkers and design features.
        
        Args:
            trial: Trial data dict.
        
        Returns:
            Dict with trial_success_probability, risk_tier, component_scores.
        """
        score = 0.50  # Neutral baseline
        components = {}
        
        # ===== BIOMARKER SCORING =====
        if self._safe_get(trial, "amyloid_pet_positive") == 1:
            score += self.weights.AMYLOID_PET_POSITIVE
            components["amyloid_pet_positive"] = self.weights.AMYLOID_PET_POSITIVE
        
        if self._safe_get(trial, "ptau217_high") == 1:
            score += self.weights.PTAU217_HIGH
            components["ptau217_high"] = self.weights.PTAU217_HIGH
        
        if self._safe_get(trial, "csf_abeta42_40_ratio_low") == 1:
            score += self.weights.CSF_ABETA42_40_LOW
            components["csf_abeta42_40_ratio_low"] = self.weights.CSF_ABETA42_40_LOW
        
        if self._safe_get(trial, "apoe_e4_carrier") == 1:
            score += self.weights.APOE_E4_CARRIER
            components["apoe_e4_carrier"] = self.weights.APOE_E4_CARRIER
        
        # ===== TRIAL DESIGN SCORING =====
        trial_duration = self._safe_get(trial, "trial_duration_weeks", 0)
        if trial_duration >= 52:
            score += self.weights.LONG_DURATION_GE_52_WEEKS
            components["long_duration"] = self.weights.LONG_DURATION_GE_52_WEEKS
        elif trial_duration < 24:
            score += self.weights.SHORT_DURATION_LT_24_WEEKS
            components["short_duration_penalty"] = self.weights.SHORT_DURATION_LT_24_WEEKS
        
        sample_size = self._safe_get(trial, "trial_sample_size", 0)
        if sample_size >= 250:
            score += self.weights.ADEQUATE_SAMPLE_SIZE_GE_250
            components["adequate_sample_size"] = self.weights.ADEQUATE_SAMPLE_SIZE_GE_250
        elif sample_size < 100:
            score += self.weights.SMALL_SAMPLE_LT_100
            components["small_sample_penalty"] = self.weights.SMALL_SAMPLE_LT_100
        
        # ===== COGNITIVE STAGE SCORING =====
        mmse = self._safe_get(trial, "baseline_mmse")
        if mmse is not None:
            if 18 <= mmse <= 26:
                score += self.weights.BASELINE_MMSE_MCI_SWEET_SPOT
                components["mmse_mci_sweet_spot"] = self.weights.BASELINE_MMSE_MCI_SWEET_SPOT
            elif mmse < 10:
                score += self.weights.VERY_ADVANCED_DEMENTIA_MMSE_LT_10
                components["very_advanced_dementia_penalty"] = self.weights.VERY_ADVANCED_DEMENTIA_MMSE_LT_10
        
        # ===== ENRICHMENT STRATEGY =====
        enrichment = self._safe_get(trial, "biomarker_enrichment_strategy", "").lower()
        if "at_positive" in enrichment or enrichment == "at":
            score += self.weights.ENRICHMENT_AT_POSITIVE
            components["at_positive_enrichment"] = self.weights.ENRICHMENT_AT_POSITIVE
        
        # ===== AGE ADJUSTMENT =====
        age = self._safe_get(trial, "age_mean")
        if age is not None:
            if 60 <= age <= 75:
                score += self.weights.AGE_SWEET_SPOT_60_75
                components["age_sweet_spot"] = self.weights.AGE_SWEET_SPOT_60_75
        
        # Normalize score to [0, 1]
        final_probability = np.clip(score, 0.0, 1.0)
        
        # Determine risk tier
        if final_probability >= 0.70:
            risk_tier = "LOW"
        elif final_probability >= 0.40:
            risk_tier = "MEDIUM"
        else:
            risk_tier = "HIGH"
        
        return {
            "trial_success_probability": float(final_probability),
            "risk_tier": risk_tier,
            "component_scores": components,
        }
    
    @staticmethod
    def _safe_get(trial: Dict, key: str, default=None):
        """Safely get value from trial dict with None handling."""
        value = trial.get(key, default)
        if value is None or (isinstance(value, float) and np.isnan(value)):
            return default
        return value


def score_trial_rule_based(trial: Dict) -> Dict:
    """
    Score a trial using rule-based approach.
    
    Convenience function that creates a scorer and scores the trial.
    
    Args:
        trial: Trial data dictionary.
    
    Returns:
        Scoring results dict.
    """
    scorer = TrialScorer()
    return scorer.score_trial(trial)


# ====== UTILITY FUNCTIONS ======

def train_full_pipeline(data_path: str = None) -> Tuple[Dict, str]:
    """
    Complete training pipeline: load, prepare, train, evaluate, save.
    
    Args:
        data_path: Path to training data (default: MLConfig.DATA_PATH).
    
    Returns:
        Tuple of (evaluation_results dict, success_message string)
    """
    data_path = data_path or MLConfig.DATA_PATH
    
    print("\n" + "=" * 80)
    print("GENIVRA ML ENGINE - FULL TRAINING PIPELINE")
    print("=" * 80)
    
    # Load and prepare
    X, y, feature_names = load_and_prepare_data(data_path)
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=MLConfig.TEST_SIZE, random_state=MLConfig.RANDOM_STATE
    )
    
    print(f"\n  ✓ Train/test split: {len(X_train)} / {len(X_test)}")
    
    # Train
    model, scaler = train_model(X_train, y_train)
    
    # Evaluate
    eval_results = evaluate_model(model, scaler, X_test, y_test, feature_names)
    
    # Save
    save_model(model, scaler)
    
    print("\n" + "=" * 80)
    print("TRAINING COMPLETE")
    print("=" * 80)
    
    return eval_results, "Training pipeline completed successfully."


# ====== INITIALIZATION ======

if __name__ == "__main__":
    # Test the engine
    print("Genivra ML Engine loaded successfully")
    print(f"Model path: {MLConfig.MODEL_SAVE_PATH}")
    print(f"Scaler path: {MLConfig.SCALER_SAVE_PATH}")
