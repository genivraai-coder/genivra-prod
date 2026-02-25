"""Evaluation package placeholder to ensure import paths work after reorganization."""
from .metrics import compute_metrics, calibration_curve_plot
from .visualization import plot_roc_curve, plot_feature_importance
from .reporting import generate_evaluation_report

__all__ = [
    "compute_metrics",
    "calibration_curve_plot",
    "plot_roc_curve",
    "plot_feature_importance",
    "generate_evaluation_report",
]