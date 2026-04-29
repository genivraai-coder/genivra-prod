# Features

This directory contains feature engineering and data preprocessing utilities.

## Files

- `build_features.py`: Core feature engineering functions
- `utils.py`: Helper utilities for feature processing
- `biomarker_feature_catalog.md`: Documentation of biomarker features

## Usage

```python
from Features.build_features import create_features, load_raw_data

# Load and process data
df = load_raw_data('data/trials.csv')
df_featured = create_features(df)
```