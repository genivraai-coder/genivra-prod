"""
Logistic Regression Model Training for Alzheimer's Trial Success Prediction

Trains a logistic regression baseline model on synthetic AD trials dataset.
Includes cross-validation, feature importance analysis, and model evaluation.

Outputs:
- Model performance metrics (Accuracy, AUC, Confusion Matrix)
- Feature importance ranked by coefficient magnitude
- Trained model saved as pickle artifact

Author: Genivra ML Team
Date: February 20, 2026
Version: 1.0
"""

import os
import pickle
import warnings
from typing import Dict, Tuple

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


# ============================================================================
# Configuration
# ============================================================================

class Config:
    """Training configuration."""
    
    DATA_PATH = "data/processed/synthetic_ad_trials.csv"
    ARTIFACT_DIR = "models/artifacts"
    MODEL_SAVE_PATH = os.path.join(ARTIFACT_DIR, "logistic_model.pkl")
    SCALER_SAVE_PATH = os.path.join(ARTIFACT_DIR, "feature_scaler.pkl")
    TREE_MODEL_SAVE_PATH = os.path.join(ARTIFACT_DIR, "decision_tree_model.pkl")
    
    TEST_SIZE = 0.20
    RANDOM_STATE = 42
    
    # Features to exclude from training
    EXCLUDE_FEATURES = [
        "trial_id",
        "trial_success_probability",  # Target-adjacent (leakage risk)
        "trial_success",  # This is our label
    ]
    
    # Features to include (can be customized)
    INCLUDE_FEATURES = None  # If None, auto-detect


# ============================================================================
# Data Loading & Preparation
# ============================================================================

def load_and_prepare_data(data_path: str) -> Tuple[pd.DataFrame, pd.Series, list]:
    """
    Load synthetic trial data and prepare for training.
    
    Args:
        data_path (str): Path to CSV file.
    
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
        if col not in Config.EXCLUDE_FEATURES
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
    
    # Convert categorical features to numeric
    categorical_cols = X.select_dtypes(include=['object']).columns.tolist()
    if len(categorical_cols) > 0:
        print(f"\n  ⚠ Found {len(categorical_cols)} categorical features:")
        for col in categorical_cols:
            print(f"    - {col}: {X[col].nunique()} unique values")
        
        # One-hot encode
        X = pd.get_dummies(X, columns=categorical_cols, drop_first=True)
        print(f"  ✓ One-hot encoded categorical features")
        print(f"    New shape: {X.shape}")
    
    return X, y, X.columns.tolist()


# ============================================================================
# Model Training
# ============================================================================

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
    
    # Standardize features (important for logistic regression)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    # Train model
    model = LogisticRegression(
        max_iter=1000,
        random_state=Config.RANDOM_STATE,
        solver="lbfgs",
        class_weight="balanced",  # Handle class imbalance if present
        verbose=0
    )
    
    model.fit(X_train_scaled, y_train)
    
    print(f"  ✓ Model trained")
    print(f"    Intercept: {model.intercept_[0]:.4f}")
    print(f"    Coefficients learned: {len(model.coef_[0])} features")
    
    return model, scaler


# ============================================================================
# Model Evaluation
# ============================================================================

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
        model: Trained logistic regression model.
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
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    conf_matrix = confusion_matrix(y_test, y_pred)
    
    print(f"  Accuracy:  {accuracy:.4f}")
    print(f"  ROC-AUC:   {roc_auc:.4f}")
    
    print(f"\n  Confusion Matrix:")
    print(f"    TN: {conf_matrix[0, 0]:3d}  |  FP: {conf_matrix[0, 1]:3d}")
    print(f"    FN: {conf_matrix[1, 0]:3d}  |  TP: {conf_matrix[1, 1]:3d}")
    
    # Detailed classification report
    print(f"\n  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["Fail (0)", "Success (1)"]))
    
    # Feature importance
    feature_importance = compute_feature_importance(model, feature_names)
    
    results = {
        "accuracy": accuracy,
        "roc_auc": roc_auc,
        "confusion_matrix": conf_matrix,
        "y_pred": y_pred,
        "y_pred_proba": y_pred_proba,
        "feature_importance": feature_importance,
    }
    
    return results


def compute_feature_importance(model: LogisticRegression, feature_names: list) -> pd.DataFrame:
    """
    Extract feature importance from logistic regression coefficients.
    
    Args:
        model: Trained model.
        feature_names: List of feature names.
    
    Returns:
        DataFrame with features ranked by importance.
    """
    print(f"\nFeature Importance (from coefficients)")
    print("=" * 80)
    
    # Extract coefficients
    coefficients = model.coef_[0]
    
    # Create importance dataframe
    importance_df = pd.DataFrame({
        "feature": feature_names,
        "coefficient": coefficients,
        "abs_coefficient": np.abs(coefficients),
    })
    
    # Sort by absolute coefficient (magnitude = importance)
    importance_df = importance_df.sort_values("abs_coefficient", ascending=False)
    importance_df["rank"] = range(1, len(importance_df) + 1)
    
    # Display top 20
    print(f"\n  Top 20 Most Important Features:")
    print(f"  (Positive = increases success probability; Negative = decreases)")
    print()
    
    top_n = min(20, len(importance_df))
    for idx, row in importance_df.head(top_n).iterrows():
        direction = "↑ increases" if row["coefficient"] > 0 else "↓ decreases"
        print(f"    {row['rank']:2d}. {row['feature']:40s} {row['coefficient']:8.4f}  {direction}")
    
    print(f"\n  Bottom 10 Least Important Features:")
    print()
    bottom_n = min(10, len(importance_df))
    for idx, row in importance_df.tail(bottom_n).iterrows():
        direction = "↑ increases" if row["coefficient"] > 0 else "↓ decreases"
        print(f"    {row['rank']:2d}. {row['feature']:40s} {row['coefficient']:8.4f}  {direction}")
    
    return importance_df


# ============================================================================
# Decision Tree Training & Evaluation
# ============================================================================

def train_decision_tree(X_train: pd.DataFrame, y_train: pd.Series, max_depth: int = 4) -> DecisionTreeClassifier:
    """
    Train decision tree classifier.
    
    Args:
        X_train: Training features.
        y_train: Training labels.
        max_depth: Maximum tree depth. Default 4 to prevent overfitting.
    
    Returns:
        Trained decision tree model.
    """
    print("\nTraining Decision Tree Model (max_depth={})".format(max_depth))
    print("=" * 80)
    
    # Train model (no scaling needed for trees)
    model = DecisionTreeClassifier(
        max_depth=max_depth,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=Config.RANDOM_STATE,
        class_weight="balanced",
    )
    
    model.fit(X_train, y_train)
    
    print(f"  ✓ Decision tree trained")
    print(f"    Max depth: {max_depth}")
    print(f"    Leaf nodes: {model.get_n_leaves()}")
    print(f"    Tree depth: {model.get_depth()}")
    
    return model


def evaluate_decision_tree(
    model: DecisionTreeClassifier,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    feature_names: list
) -> Dict:
    """
    Evaluate decision tree on test set.
    
    Args:
        model: Trained decision tree model.
        X_test: Test features.
        y_test: Test labels.
        feature_names: List of feature names.
    
    Returns:
        Dictionary with evaluation metrics.
    """
    print("\nDecision Tree Evaluation")
    print("=" * 80)
    
    # Predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Metrics
    accuracy = accuracy_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    conf_matrix = confusion_matrix(y_test, y_pred)
    
    print(f"  Accuracy:  {accuracy:.4f}")
    print(f"  ROC-AUC:   {roc_auc:.4f}")
    
    print(f"\n  Confusion Matrix:")
    print(f"    TN: {conf_matrix[0, 0]:3d}  |  FP: {conf_matrix[0, 1]:3d}")
    print(f"    FN: {conf_matrix[1, 0]:3d}  |  TP: {conf_matrix[1, 1]:3d}")
    
    # Detailed classification report
    print(f"\n  Classification Report:")
    print(classification_report(y_test, y_pred, target_names=["Fail (0)", "Success (1)"]))
    
    # Feature importance
    feature_importance = compute_tree_feature_importance(model, feature_names)
    
    results = {
        "accuracy": accuracy,
        "roc_auc": roc_auc,
        "confusion_matrix": conf_matrix,
        "y_pred": y_pred,
        "y_pred_proba": y_pred_proba,
        "feature_importance": feature_importance,
    }
    
    return results


def compute_tree_feature_importance(model: DecisionTreeClassifier, feature_names: list) -> pd.DataFrame:
    """
    Extract feature importance from decision tree.
    
    Args:
        model: Trained decision tree model.
        feature_names: List of feature names.
    
    Returns:
        DataFrame with features ranked by importance.
    """
    print(f"\nFeature Importance (from decision tree splits)")
    print("=" * 80)
    
    # Extract importances (Gini-based)
    importances = model.feature_importances_
    
    # Create importance dataframe
    importance_df = pd.DataFrame({
        "feature": feature_names,
        "importance": importances,
        "importance_pct": importances * 100,
    })
    
    # Sort by importance
    importance_df = importance_df.sort_values("importance", ascending=False)
    importance_df["rank"] = range(1, len(importance_df) + 1)
    
    # Display top 15
    print(f"\n  Top 15 Most Important Features:")
    print()
    
    top_n = min(15, len(importance_df))
    for idx, row in importance_df.head(top_n).iterrows():
        pct_bar = "█" * int(row["importance_pct"] / 2)  # Scale to 50 chars max
        print(f"    {row['rank']:2d}. {row['feature']:40s} {row['importance']:.4f}  {pct_bar}")
    
    return importance_df


def run_cross_validation(X: pd.DataFrame, y: pd.Series, n_folds: int = 5) -> Dict:
    """
    Run k-fold cross-validation for both logistic regression and decision tree.
    
    Args:
        X: Features.
        y: Labels.
        n_folds: Number of folds.
    
    Returns:
        Dictionary with CV results for both models.
    """
    print(f"\nCross-Validation ({n_folds}-fold)")
    print("=" * 80)
    
    # Scale features for logistic regression
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Logistic Regression CV
    print("\nLogistic Regression:")
    lr_model = LogisticRegression(
        max_iter=1000,
        random_state=Config.RANDOM_STATE,
        solver="lbfgs",
        class_weight="balanced"
    )
    
    lr_cv_scores_accuracy = cross_val_score(lr_model, X_scaled, y, cv=n_folds, scoring="accuracy")
    lr_cv_scores_auc = cross_val_score(lr_model, X_scaled, y, cv=n_folds, scoring="roc_auc")
    
    print(f"  Accuracy: {lr_cv_scores_accuracy.mean():.4f} (+/- {lr_cv_scores_accuracy.std():.4f})")
    print(f"  ROC-AUC:  {lr_cv_scores_auc.mean():.4f} (+/- {lr_cv_scores_auc.std():.4f})")
    
    # Decision Tree CV
    print("\nDecision Tree (max_depth=4):")
    dt_model = DecisionTreeClassifier(
        max_depth=4,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=Config.RANDOM_STATE,
        class_weight="balanced"
    )
    
    dt_cv_scores_accuracy = cross_val_score(dt_model, X, y, cv=n_folds, scoring="accuracy")
    dt_cv_scores_auc = cross_val_score(dt_model, X, y, cv=n_folds, scoring="roc_auc")
    
    print(f"  Accuracy: {dt_cv_scores_accuracy.mean():.4f} (+/- {dt_cv_scores_accuracy.std():.4f})")
    print(f"  ROC-AUC:  {dt_cv_scores_auc.mean():.4f} (+/- {dt_cv_scores_auc.std():.4f})")
    
    return {
        "logistic_regression": {
            "accuracy_scores": lr_cv_scores_accuracy,
            "auc_scores": lr_cv_scores_auc,
        },
        "decision_tree": {
            "accuracy_scores": dt_cv_scores_accuracy,
            "auc_scores": dt_cv_scores_auc,
        }
    }



# ============================================================================
# Model Persistence
# ============================================================================

def save_model(model: LogisticRegression, scaler: StandardScaler, artifact_dir: str = Config.ARTIFACT_DIR) -> None:
    """
    Save trained models and scaler to disk.
    
    Args:
        model: Trained logistic regression model dict or single model.
        scaler: Fitted feature scaler.
        artifact_dir: Directory to save artifacts.
    """
    print(f"\nSaving Model Artifacts")
    print("=" * 80)
    
    os.makedirs(artifact_dir, exist_ok=True)
    
    # Handle both single model and dict of models
    if isinstance(model, dict):
        # Save logistic regression
        with open(Config.MODEL_SAVE_PATH, "wb") as f:
            pickle.dump(model.get("logistic_regression"), f)
        print(f"  ✓ Logistic Regression model saved to: {Config.MODEL_SAVE_PATH}")
        
        # Save decision tree
        with open(Config.TREE_MODEL_SAVE_PATH, "wb") as f:
            pickle.dump(model.get("decision_tree"), f)
        print(f"  ✓ Decision Tree model saved to: {Config.TREE_MODEL_SAVE_PATH}")
    else:
        # Legacy: single model
        with open(Config.MODEL_SAVE_PATH, "wb") as f:
            pickle.dump(model, f)
        print(f"  ✓ Model saved to: {Config.MODEL_SAVE_PATH}")
    
    # Save scaler
    with open(Config.SCALER_SAVE_PATH, "wb") as f:
        pickle.dump(scaler, f)
    print(f"  ✓ Scaler saved to: {Config.SCALER_SAVE_PATH}")


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """
    Main training pipeline: train both logistic regression and decision tree.
    """
    print("\n" + "=" * 80)
    print("Baseline Model Training - Alzheimer's Trial Success Prediction")
    print("=" * 80)
    
    # Load data
    X, y, feature_names = load_and_prepare_data(Config.DATA_PATH)
    
    # Train/test split
    print(f"\nTrain/Test Split ({(1-Config.TEST_SIZE)*100:.0f}% / {Config.TEST_SIZE*100:.0f}%)")
    print("=" * 80)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=Config.TEST_SIZE,
        random_state=Config.RANDOM_STATE,
        stratify=y
    )
    print(f"  Train set: {len(X_train)} samples")
    print(f"  Test set:  {len(X_test)} samples")
    print(f"  Train labels: {y_train.value_counts().to_dict()}")
    print(f"  Test labels:  {y_test.value_counts().to_dict()}")
    
    # ===== LOGISTIC REGRESSION =====
    lr_model, scaler = train_model(X_train, y_train)
    lr_results = evaluate_model(lr_model, scaler, X_test, y_test, feature_names)
    
    # ===== DECISION TREE =====
    dt_model = train_decision_tree(X_train, y_train, max_depth=4)
    dt_results = evaluate_decision_tree(dt_model, X_test, y_test, feature_names)
    
    # ===== CROSS-VALIDATION =====
    cv_results = run_cross_validation(X, y, n_folds=5)
    
    # ===== COMPARISON TABLE =====
    print_comparison_table(lr_results, dt_results, cv_results)
    
    # ===== SAVE MODELS =====
    models = {
        "logistic_regression": lr_model,
        "decision_tree": dt_model,
    }
    save_model(models, scaler)
    
    # Summary
    print(f"\n" + "=" * 80)
    print("Training Complete")
    print("=" * 80)
    print(f"\nModel artifacts saved to: {Config.ARTIFACT_DIR}/")
    print("=" * 80 + "\n")
    
    return {
        "logistic_regression": {"model": lr_model, "results": lr_results},
        "decision_tree": {"model": dt_model, "results": dt_results},
    }, scaler, cv_results


def print_comparison_table(lr_results: Dict, dt_results: Dict, cv_results: Dict) -> None:
    """
    Print a comparison table of model performance.
    
    Args:
        lr_results: Logistic regression evaluation results.
        dt_results: Decision tree evaluation results.
        cv_results: Cross-validation results.
    """
    print("\n" + "=" * 80)
    print("Model Comparison Summary")
    print("=" * 80)
    
    # Prepare comparison data
    comparison_data = {
        "Metric": [
            "Test Accuracy",
            "Test ROC-AUC",
            "CV Accuracy (mean)",
            "CV Accuracy (std)",
            "CV ROC-AUC (mean)",
            "CV ROC-AUC (std)",
        ],
        "Logistic Regression": [
            f"{lr_results['accuracy']:.4f}",
            f"{lr_results['roc_auc']:.4f}",
            f"{cv_results['logistic_regression']['accuracy_scores'].mean():.4f}",
            f"{cv_results['logistic_regression']['accuracy_scores'].std():.4f}",
            f"{cv_results['logistic_regression']['auc_scores'].mean():.4f}",
            f"{cv_results['logistic_regression']['auc_scores'].std():.4f}",
        ],
        "Decision Tree (depth=4)": [
            f"{dt_results['accuracy']:.4f}",
            f"{dt_results['roc_auc']:.4f}",
            f"{cv_results['decision_tree']['accuracy_scores'].mean():.4f}",
            f"{cv_results['decision_tree']['accuracy_scores'].std():.4f}",
            f"{cv_results['decision_tree']['auc_scores'].mean():.4f}",
            f"{cv_results['decision_tree']['auc_scores'].std():.4f}",
        ],
    }
    
    comparison_df = pd.DataFrame(comparison_data)
    
    print("\n" + comparison_df.to_string(index=False))
    
    # Determine winner
    print("\n" + "-" * 80)
    lr_acc = lr_results['accuracy']
    dt_acc = dt_results['accuracy']
    
    if lr_acc > dt_acc:
        print(f"✓ Logistic Regression wins on test accuracy: {lr_acc:.4f} > {dt_acc:.4f}")
    elif dt_acc > lr_acc:
        print(f"✓ Decision Tree wins on test accuracy: {dt_acc:.4f} > {lr_acc:.4f}")
    else:
        print(f"✓ Tie: Both models achieve {lr_acc:.4f} accuracy")
    
    lr_auc = lr_results['roc_auc']
    dt_auc = dt_results['roc_auc']
    
    if lr_auc > dt_auc:
        print(f"✓ Logistic Regression wins on test AUC: {lr_auc:.4f} > {dt_auc:.4f}")
    elif dt_auc > lr_auc:
        print(f"✓ Decision Tree wins on test AUC: {dt_auc:.4f} > {lr_auc:.4f}")
    else:
        print(f"✓ Tie: Both models achieve {lr_auc:.4f} AUC")
    
    print("\n" + "=" * 80)
    
    # Feature importance comparison
    print("\nTop 10 Important Features - Logistic Regression:")
    print("-" * 80)
    lr_top = lr_results['feature_importance'].head(10)[['rank', 'feature', 'coefficient']]
    for idx, row in lr_top.iterrows():
        print(f"  {int(row['rank']):2d}. {row['feature']:40s} {row['coefficient']:8.4f}")
    
    print("\nTop 10 Important Features - Decision Tree:")
    print("-" * 80)
    dt_top = dt_results['feature_importance'].head(10)[['rank', 'feature', 'importance']]
    for idx, row in dt_top.iterrows():
        print(f"  {int(row['rank']):2d}. {row['feature']:40s} {row['importance']:.4f}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    models, scaler, cv_results = main()
