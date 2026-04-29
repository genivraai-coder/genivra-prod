# Evaluation

This directory contains tools for evaluating model performance and generating metrics.

## Files

- `metrics.py`: Functions for computing classification metrics (AUC, accuracy, precision, recall, F1, Brier score)
- `plots.py`: Visualization utilities for model evaluation

## Usage

```python
from Evaluation.metrics import compute_metrics

# Compute metrics for predictions
metrics = compute_metrics(y_true, y_pred_proba)
print(f"AUC: {metrics['auc']:.3f}")
print(f"Accuracy: {metrics['accuracy']:.3f}")
```