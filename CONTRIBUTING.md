# Contributing to Genivra

This document explains how to contribute code and run the project locally.

## Branch structure

- `main`: The main production-ready branch.
- `andrew_dev2`: The current working branch for new development.
- Create feature branches from `andrew_dev2` and open pull requests into `main` or into `andrew_dev2` as directed by the team.

## Run tests before pushing

From the project root:

```bash
pytest Tests/
```

For API-specific testing:

```bash
python run_api_tests.py
```

If you add or modify API code, run both test commands.

## Start the API locally

1. Activate your virtual environment:
   ```bash
   source venv/bin/activate
   ```
2. Start the API server:
   ```bash
   uvicorn API.main:app --reload
   ```
3. Visit the docs in your browser at:
   ```bash
   http://localhost:8000/docs
   ```

## Start the frontend locally

The frontend is served from the `FrontEnd/` folder.

```bash
python -m http.server 8001 --directory FrontEnd
```

Then open:

```bash
http://localhost:8001/dashboard.html
```

The frontend sends requests to the API, so make sure the API is running first.

## Notes for new contributors

- Look at `API/main.py` first for request handling.
- Look at `Models/predict_trial.py` first for the prediction logic.
- Use `FrontEnd/dashboard.html` to test the UI.
