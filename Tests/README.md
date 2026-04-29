# Tests

This folder contains the automated checks used before pushing changes. Start with `Tests/test_predict_trial.py` first.

## Files

- `test_flask_predict.py`: Tests for Flask API prediction endpoints
- `test_predict_trial.py`: Tests for core prediction logic
- `test_rule_based_scorer.py`: Tests for rule-based scoring

## Running Tests

```bash
# Run all tests
pytest Tests/

# Run specific test file
pytest Tests/test_predict_trial.py

# Run with coverage
pytest --cov=Models --cov=API Tests/
```

## Test Coverage

Tests cover:
- Model prediction accuracy
- API endpoint functionality
- Feature engineering pipelines
- Error handling and edge cases