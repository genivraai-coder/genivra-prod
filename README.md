# Genivra Neuro Trial Success Prediction

Genivra is a **Python platform for predicting clinical trial success risk in neurological indications**, integrating **curated biomarker, trial, and patient data** to generate **interpretable risk scores**. Designed for biomedical researchers, data scientists, and AI practitioners working on neuro-focused trial analytics.

## Features

- **Neuro Indication Focus**
  - Supports multiple indications: Alzheimer’s, ALS, Epilepsy, Parkinson’s
  - Structured biomarker intelligence mapping
- **Biomarker & Trial Feature Integration**
  - Combines genetic, CSF, plasma, and imaging biomarkers
  - Tracks trial design features and endpoints for scoring
- **ML-Ready Pipelines**
  - Modular structure for feature engineering, model training, and evaluation
  - Simulated trial scoring logic feeds ML training
- **Evaluation & Metrics**
  - Calculates success/failure predictions
  - Produces interpretable visualizations for clinical insights
- **Reproducible & Extensible**
  - Modular folders: `data/`, `features/`, `models/`, `evaluation/`, `notebooks/`, `config/`
  - Future expansion for additional indications or scoring models
- **Demo-Ready Assets**
  - Generates playbooks, logic sheets, and citations
  - Supports integration with internal dashboards and ML engines

## Installation

```bash
git clone https://github.com/yourusername/genivra_ml_project.git
cd genivra_ml_project
python -m venv venv
source venv/bin/activate  # Mac/Linux
venv\Scripts\activate     # Windows
pip install -r requirements.txt
## Usage

```bash
# Train models
python scripts/run_train.py --config config/config.yaml

# Predict on new trial data
python scripts/run_predict.py --input data/new_trials.csv

# Evaluate model performance
python scripts/run_eval.py --results outputs/predictions.csv

# Run tests
pytest tests/