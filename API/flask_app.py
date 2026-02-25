"""Simple Flask wrapper exposing a /predict endpoint that calls the existing
Genivra `predict_trial()` engine function.

This file is intentionally lightweight — it validates required JSON fields,
calls `predict_trial`, and returns a concise JSON response.
"""
import sys
import os
import logging
from typing import Dict, Any

from flask import Flask, request, jsonify

# add project root so we can import Models.predict_trial
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Models.predict_trial import predict_trial

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)


REQUIRED_FIELDS = [
    "phase",
    "indication",
    "trial_design",
    "endpoints",
    "biomarkers",
    "enrollment",
]


@app.route("/predict", methods=["POST"])
def predict():
    """Accepts JSON, validates required fields, calls predict_trial, returns JSON.

    Expected JSON structure (example):
    {
        "phase": "Phase II",
        "indication": "Alzheimer's Disease",
        "trial_design": { "trial_sample_size": 500, "trial_duration_weeks": 52 },
        "endpoints": { ... },
        "biomarkers": { ... },
        "enrollment": { ... }
    }
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    payload = request.get_json()

    # Validate required top-level fields
    missing = [f for f in REQUIRED_FIELDS if f not in payload]
    if missing:
        return jsonify({"error": "Missing required fields", "missing": missing}), 400

    # Basic sanity checks: trial_design should be a dict with at least sample size
    if not isinstance(payload.get("trial_design"), dict):
        return jsonify({"error": "trial_design must be an object/dict"}), 400

    # Build input for predict_trial. The Genivra engine expects a dict; we'll pass through
    # the payload, but you can transform/massage fields here if needed.
    try:
        raw_result = predict_trial(payload)
    except Exception as exc:
        logger.exception("predict_trial failed")
        return jsonify({"error": "Internal server error", "detail": str(exc)}), 500

    # Map engine output to simplified API response
    response = {
        "probability_of_success": raw_result.get("trial_success_probability") if isinstance(raw_result, dict) else None,
        "risk_tier": raw_result.get("risk_tier") if isinstance(raw_result, dict) else None,
        "top_drivers": raw_result.get("top_feature_importance") if isinstance(raw_result, dict) else None,
        "biomarker_explanation": raw_result.get("biomarker_explanation") if isinstance(raw_result, dict) else None,
        "confidence_flag": raw_result.get("confidence_flag") if isinstance(raw_result, dict) else None,
        "raw": raw_result if isinstance(raw_result, dict) else None,
    }

    return jsonify(response), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    # Run local debug server for quick testing
    app.run(host="0.0.0.0", port=8001, debug=True)
