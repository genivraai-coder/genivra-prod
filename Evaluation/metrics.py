import numpy as np
from sklearn.metrics import (
    roc_auc_score,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    brier_score_loss,
    confusion_matrix,
)
from sklearn.calibration import calibration_curve


def compute_metrics(y_true, y_pred_proba, threshold=0.5):
    """
    Compute classification and calibration metrics for predicted probabilities.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
        Ground truth binary labels (0 or 1).
    y_pred_proba : array-like of shape (n_samples,)
        Predicted probabilities for the positive class.
    threshold : float, default=0.5
        Threshold to convert probabilities to binary predictions.

    Returns
    -------
    dict
        Dictionary with AUC, accuracy, precision, recall, F1, Brier score.
    """
    y_pred = (y_pred_proba >= threshold).astype(int)

    metrics = {
        "auc": roc_auc_score(y_true, y_pred_proba),
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "brier_score": brier_score_loss(y_true, y_pred_proba),
        "confusion_matrix": confusion_matrix(y_true, y_pred),
    }
    return metrics


def calibration_curve_plot(y_true, y_pred_proba, n_bins=10):
    """
    Compute calibration curve values.

    Parameters
    ----------
    y_true : array-like of shape (n_samples,)
    y_pred_proba : array-like of shape (n_samples,)
    n_bins : int, default=10
        Number of bins to use for calibration.

    Returns
    -------
    tuple of arrays
        fraction_of_positives, mean_predicted_value
    """
    fraction_of_positives, mean_predicted_value = calibration_curve(
        y_true, y_pred_proba, n_bins=n_bins, strategy="uniform"
    )
    return fraction_of_positives, mean_predicted_value