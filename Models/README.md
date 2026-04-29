# Models

This folder contains the machine learning engine and prediction logic. Start with `Models/predict_trial.py` first.

## Files

- `predict_trial.py`: Main prediction function using logistic regression
- `train_logistic_regression.py`: Logistic regression training script
- `rule_based_scorer.py`: Rule-based scoring system

## Model Details

The primary model is a logistic regression classifier that predicts trial success probability based on:

- Biomarker data (APOE ε4, p-tau217, amyloid PET, etc.)
- Trial design features (sample size, duration, endpoints)
- Patient characteristics (age, baseline cognition)

## Usage

```python
from Models.predict_trial import predict_trial

# Predict single trial
result = predict_trial(trial_data)
print(f"Success probability: {result['trial_success_probability']:.2%}")

# Train model
python Models/train_logistic_regression.py
```