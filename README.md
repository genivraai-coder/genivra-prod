# Genivra Neuro Trial Success Prediction

Genivra predicts Alzheimer's clinical trial success risk using biomarkers, trial design, and patient data.

## Getting Started in 5 minutes

1. Clone the repo and open it:
   ```bash
git clone https://github.com/genivraai-coder/genivra-prod.git
cd genivra-prod
```
2. Create and activate a virtual environment:
   ```bash
python -m venv venv
source venv/bin/activate
```
3. Install the Python dependencies:
   ```bash
pip install -r requirements.txt
```
4. Start the API locally:
   ```bash
uvicorn API.main:app --reload
```
5. Open the frontend dashboard or run tests:
   ```bash
python -m http.server 8001 --directory FrontEnd
pytest Tests/
```

## Frontend

The dashboard UI lives in `FrontEnd/` and connects to the API for predictions.

Run locally:

```bash
python -m http.server 8001 --directory FrontEnd
```

Then open:

```bash
http://localhost:8001/dashboard.html
```

The frontend requires the API running at `http://localhost:8000`.

## API

The API is in `API/` and serves prediction requests.

Start it locally:

```bash
uvicorn API.main:app --reload
```

Open interactive docs:

```bash
http://localhost:8000/docs
```

A simple request example:

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"phase":"Phase II","indication":"Alzheimer\'s Disease","trial_design":{"trial_sample_size":200,"trial_duration_weeks":52},"endpoints":{"endpoint_type":"objective","primary_endpoint_name":"CDR-SB"},"biomarkers":{"apoe_e4_carrier":1,"ptau217_high":1,"amyloid_pet_positive":1},"enrollment":{"age_mean":72.5,"baseline_mmse":23,"cdr_baseline":0.5}}'
```

## ML Engine

The machine learning code is in `Models/`.

Train the model locally:

```bash
python Models/train_logistic_regression.py
```

Use the prediction function:

```bash
python -c "from Models.predict_trial import predict_trial; print(predict_trial({'apoe_e4_carrier':1,'ptau217_high':1,'amyloid_pet_positive':1,'age_mean':72.5,'baseline_mmse':23,'cdr_baseline':0.5,'trial_sample_size':200,'trial_duration_weeks':52,'endpoint_type':'objective','primary_endpoint_name':'CDR-SB','biomarker_enrichment_strategy':'amyloid_positive'}))"
```

## Scripts

The main helper scripts are at the repository root.

Run API tests:

```bash
python run_api_tests.py
```

Run the general test suite:

```bash
pytest Tests/
```

## Folder structure

Only the most important files are shown below:

```
.
├── README.md
├── CONTRIBUTING.md
├── .gitignore
├── API/
│   ├── main.py
│   ├── flask_app.py
│   ├── models.py
│   └── README.md
├── FrontEnd/
│   ├── dashboard.html
│   └── README.md
├── Models/
│   ├── predict_trial.py
│   ├── train_logistic_regression.py
│   └── README.md
├── Tests/
│   ├── test_predict_trial.py
│   └── README.md
├── Config/
│   └── config.yaml
├── engine/
│   └── README.md
├── frontend/
│   └── README.md
├── scripts/
│   └── README.md
├── run_api_tests.py
└── requirements.txt
```

## What each part does

- **Frontend**: shows the dashboard and lets a user submit trial data to the API.
- **API**: receives requests, validates inputs, and returns prediction results.
- **ML Engine**: trains and scores trial data with the logistic regression model.
- **Scripts**: test commands and helper scripts for development.

## Notes for new team members

- Start with `API/main.py` for how prediction requests are served.
- Use `Models/predict_trial.py` to understand how inputs are converted into model features.
- Open `FrontEnd/dashboard.html` to see how the app submits data to the API.


## Deployment

The application can be deployed using Docker:

```bash
docker build -t genivra .
docker run -p 5000:5000 genivra
```

Or using Heroku (Procfile included):

```bash
heroku create your-app-name
git push heroku main
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## Nikhils Model with Changes

## License

See LICENSE file for details.