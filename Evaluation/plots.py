import matplotlib.pyplot as plt
from sklearn.metrics import RocCurveDisplay, PrecisionRecallDisplay, ConfusionMatrixDisplay
from .metrics import calibration_curve_plot


def plot_roc_curve(y_true, y_pred_proba, ax=None):
    if ax is None:
        fig, ax = plt.subplots()
    RocCurveDisplay.from_predictions(y_true, y_pred_proba, ax=ax)
    ax.set_title("ROC Curve")
    return ax


def plot_precision_recall_curve(y_true, y_pred_proba, ax=None):
    if ax is None:
        fig, ax = plt.subplots()
    PrecisionRecallDisplay.from_predictions(y_true, y_pred_proba, ax=ax)
    ax.set_title("Precision-Recall Curve")
    return ax


def plot_confusion_matrix(y_true, y_pred, ax=None, labels=None):
    if ax is None:
        fig, ax = plt.subplots()
    ConfusionMatrixDisplay.from_predictions(y_true, y_pred, ax=ax, display_labels=labels)
    ax.set_title("Confusion Matrix")
    return ax


def plot_calibration_curve(y_true, y_pred_proba, n_bins=10, ax=None):
    if ax is None:
        fig, ax = plt.subplots()
    frac_pos, mean_pred = calibration_curve_plot(y_true, y_pred_proba, n_bins=n_bins)
    ax.plot(mean_pred, frac_pos, "s-", label="Model")
    ax.plot([0, 1], [0, 1], "k--", label="Perfectly calibrated")
    ax.set_xlabel("Mean predicted probability")
    ax.set_ylabel("Fraction of positives")
    ax.set_title("Calibration Curve")
    ax.legend()
    return ax