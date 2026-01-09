# Neuro Trial Success Prediction - ML Architecture

## Overview
This project predicts clinical trial success risk across neuro indications using a modular ML pipeline.  
It integrates curated trial and biomarker data to generate interpretable risk scores.

## Project Structure

repo/
├── data/ # Raw and processed datasets
├── features/ # Feature engineering and transformation
├── models/ # Model definitions and checkpoints
├── evaluation/ # Evaluation metrics, plots, and reporting
├── notebooks/ # Exploratory analysis and prototyping
├── config/ # YAML config files (hyperparameters, logging)
├── logs/ # Logging outputs
├── README.md
├── architecture.md
└── requirements.txt

markdown
Copy code

## Data Flow

1. **Data Ingestion**
   - Load clinical trial and biomarker datasets (CSV, JSON, or SQL sources)
   - Validate schema and missing values
   - Output: `data/processed/`  

2. **Feature Engineering**
   - Transform raw biomarkers into structured features
   - Encode categorical variables, normalize continuous variables
   - Create indication-specific and trial-specific aggregates
   - Output: `features/`  

3. **Modeling**
   - Train ML models for trial success prediction:
     - Candidate models: Gradient Boosting, Random Forest, Neural Networks
   - Support for hyperparameter tuning via config
   - Save trained models to `models/`  

4. **Evaluation**
   - Evaluate model performance with cross-validation
   - Metrics: AUC, accuracy, precision, recall, F1, calibration
   - Generate plots: feature importance, ROC curves, calibration curves
   - Output: `evaluation/`  

5. **Prediction / Inference**
   - Apply trained models to new trial data
   - Output interpretable trial risk scores
   - Integrate with signal engine for downstream scoring  

## Logging and Config
- Configs in `config/config.yaml` and `config/logging_config.yaml`
- Logging handled via Python `logging` with both console and file output
- Separate loggers for data, features, models, evaluation

## Expansion Points
- Add new neuro indications (e.g., ALS, Parkinson’s)
- Extend feature engineering with additional biomarkers or trial design variables
- Plug in advanced ML models or ensemble architectures
- Automate evaluation and report generation