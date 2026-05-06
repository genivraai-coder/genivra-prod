"""
Genivra CNS Risk Engine API

FastAPI application for predicting clinical trial success in neurological indications.
Provides REST endpoints for trial risk scoring with interpretable probability assessments.

Author: Genivra Team
Date: February 24, 2026
Version: 1.0
"""

import sys
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from io import BytesIO

from fastapi import FastAPI, HTTPException, status, UploadFile, File, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
import logging
import pandas as pd

# Add parent directory to path so we can import from Models
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from Models.predict_trial import predict_trial
from API.auth import APIKeyManager, KeyTier
from API.config import settings, print_settings_summary
from API.models import (
    PredictionRequest,
    PredictionResponse,
    ErrorResponse,
    HealthResponse,
    FeatureDriver,
    BatchPredictionResponse,
    BatchPredictionRowResult,
)


# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# FASTAPI APP SETUP
# ============================================================================

app = FastAPI(
    title=settings.app_name,
    description="AI-powered predictive scoring engine for neurological clinical trials",
    version=settings.app_version,
    docs_url="/docs" if settings.enable_api_docs else None,
    redoc_url="/redoc" if settings.enable_redoc else None,
    openapi_url="/openapi.json" if settings.enable_openapi else None,
)


# ============================================================================
# CORS MIDDLEWARE
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# AUTHENTICATION DEPENDENCY
# ============================================================================

def get_api_key_from_headers(
    x_api_key: str = Header(None),
    authorization: str = Header(None),
) -> Optional[str]:
    """
    Extract the API key from request headers.

    Supports:
    - x-api-key: direct API key header
    - Authorization: Bearer <api_key>
    """
    if x_api_key and isinstance(x_api_key, str) and x_api_key.strip():
        return x_api_key.strip()

    if authorization and isinstance(authorization, str):
        parts = authorization.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1].strip()

    return None


async def verify_api_key(api_key: Optional[str] = Depends(get_api_key_from_headers)) -> Optional[Dict[str, str]]:
    """
    Verify API key from request headers if provided.
    
    Args:
        api_key: API key from x-api-key or Authorization Bearer header
    
    Returns:
        Dict with api_key and tier information, or None if no key was provided
    
    Raises:
        HTTPException: 401 if key invalid, 429 if rate limited
    """
    if os.getenv("ENV") == "dev":
        logger.info("ENV=dev detected; skipping API auth.")
        return None
    if not api_key:
        return None
    
    # Validate key format (basic check)
    if not isinstance(api_key, str) or len(api_key.strip()) == 0:
        logger.warning("API request with invalid key format")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Validate key exists and is active
    is_valid, tier, name = APIKeyManager.validate_key(api_key)
    if not is_valid:
        logger.warning(f"API request with invalid/inactive key: {api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Check rate limit
    allowed, message = APIKeyManager.check_rate_limit(api_key)
    if not allowed:
        logger.warning(f"Rate limit exceeded for key: {api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=message,
            headers={"Retry-After": "2592000"},  # 30 days in seconds
        )
    
    logger.info(f"API key validated: tier={tier}, name={name}")
    return {"api_key": api_key, "tier": tier, "name": name}


# ========================================================================
# UTILITY FUNCTIONS
# ========================================================================

def convert_prediction_output(raw_output: dict) -> PredictionResponse:
    """
    Convert raw predict_trial() output to Pydantic PredictionResponse.
    
    Args:
        raw_output: Dictionary from predict_trial()
    
    Returns:
        PredictionResponse: Validated Pydantic model
    """
    # Convert top_feature_importance list of dicts to FeatureDriver objects
    feature_drivers = []
    if "top_feature_importance" in raw_output:
        for feature_dict in raw_output["top_feature_importance"]:
            # Handle dict structure from get_top_features()
            # Dict contains: rank, feature, coefficient, importance_score, direction
            feature_name = feature_dict.get("feature", "unknown")
            coefficient = feature_dict.get("coefficient", 0.0)
            direction = "positive" if coefficient > 0 else "negative"
            impact_magnitude = feature_dict.get("importance_score", abs(coefficient))
            
            feature_drivers.append(
                FeatureDriver(
                    feature_name=feature_name,
                    coefficient=float(coefficient),
                    direction=direction,
                    impact_magnitude=float(impact_magnitude),
                )
            )
    
    return PredictionResponse(
        trial_success_probability=float(raw_output.get("trial_success_probability", 0.0)),
        risk_tier=raw_output.get("risk_tier", "UNKNOWN"),
        top_drivers=feature_drivers,
        biomarker_explanation=raw_output.get("biomarker_explanation", ""),
        confidence_flag=raw_output.get("confidence_flag", "LOW"),
        missing_biomarker_count=int(raw_output.get("missing_biomarker_count", 0)),
        model_version=raw_output.get("model_version", "v1.0"),
        generated_timestamp=raw_output.get("generated_timestamp", datetime.utcnow().isoformat() + "Z"),
    )


def build_input_dict(request: PredictionRequest) -> dict:
    """
    Convert PredictionRequest to input dictionary for predict_trial().
    
    Args:
        request: Parsed PredictionRequest
    
    Returns:
        dict: Input dictionary formatted for predict_trial()
    """
    input_dict = {
        # Phase and indication
        "phase": request.phase,
        "indication": request.indication,
        
        # Trial design
        "trial_sample_size": request.trial_design.trial_sample_size,
        "trial_duration_weeks": request.trial_design.trial_duration_weeks,
        "number_of_arms": request.trial_design.number_of_arms,
        "randomization_ratio": request.trial_design.randomization_ratio,
        
        # Endpoints
        "endpoint_type": request.endpoints.endpoint_type,
        "primary_endpoint_name": request.endpoints.primary_endpoint_name,
        
        # Biomarkers
        "apoe_e4_carrier": request.biomarkers.apoe_e4_carrier,
        "apoe_e4_homozygous": request.biomarkers.apoe_e4_homozygous,
        "ptau217_high": request.biomarkers.ptau217_high,
        "ptau217_continuous": request.biomarkers.ptau217_continuous,
        "csf_abeta42_40_ratio_low": request.biomarkers.csf_abeta42_40_ratio_low,
        "csf_abeta42_40_ratio_continuous": request.biomarkers.csf_abeta42_40_ratio_continuous,
        "csf_ptau_elevated": request.biomarkers.csf_ptau_elevated,
        "amyloid_pet_positive": request.biomarkers.amyloid_pet_positive,
        "tau_pet_positive": request.biomarkers.tau_pet_positive,
        "hippocampal_atrophy_mri": request.biomarkers.hippocampal_atrophy_mri,
        "hippocampal_atrophy_binary": request.biomarkers.hippocampal_atrophy_binary,
        
        # Enrollment
        "age_mean": request.enrollment.age_mean,
        "baseline_mmse": request.enrollment.baseline_mmse,
        "baseline_moca": request.enrollment.baseline_moca,
        "cdr_baseline": request.enrollment.cdr_baseline,
        
        # Enrichment strategy
        "biomarker_enrichment_strategy": request.biomarker_enrichment_strategy,
    }
    
    # Remove None values to let predict_trial handle defaults
    input_dict = {k: v for k, v in input_dict.items() if v is not None}
    
    return input_dict


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get(
    "/",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check endpoint",
)
async def root():
    """
    Health check endpoint. Returns API status and version.
    
    Returns:
        HealthResponse: Status and version information
    """
    return HealthResponse(
        status="running",
        version="1.0.0",
    )


@app.post(
    "/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Predictions"],
    summary="Predict CNS trial success",
    responses={
        200: {
            "description": "Successful prediction with risk assessment",
            "model": PredictionResponse,
        },
        400: {
            "description": "Invalid input or missing required fields",
            "model": ErrorResponse,
        },
        500: {
            "description": "Internal server error during prediction",
            "model": ErrorResponse,
        },
    },
)
async def predict(request: PredictionRequest, api_key_info: Optional[Dict[str, str]] = Depends(verify_api_key)):
    """
    Predict CNS trial success probability and risk tier.
    
    API key is optional for this endpoint.
    
    Accepts structured trial design, biomarker, and enrollment data.
    Returns interpretable success probability (0-1), risk category, and driver explanation.
    
    Args:
        request: PredictionRequest with trial parameters
    
    Returns:
        PredictionResponse: Prediction with probability, risk tier, and drivers
    
    Raises:
        HTTPException: If input validation fails or prediction fails
    
    Example:
        ```json
        {
            "phase": "Phase II",
            "indication": "Alzheimer's Disease",
            "trial_design": {
                "trial_sample_size": 200,
                "trial_duration_weeks": 52,
                "number_of_arms": 2,
                "randomization_ratio": "1:1"
            },
            "endpoints": {
                "endpoint_type": "objective",
                "primary_endpoint_name": "CDR-SB"
            },
            "biomarkers": {
                "apoe_e4_carrier": 1,
                "ptau217_high": 1,
                "amyloid_pet_positive": 1
            },
            "enrollment": {
                "age_mean": 72.5,
                "baseline_mmse": 22.0,
                "cdr_baseline": 1.5
            },
            "biomarker_enrichment_strategy": "at_positive"
        }
        ```
    """
    try:
        logger.info("Received prediction request")
        
        # Validate required fields
        if not request.trial_design or not request.endpoints or not request.biomarkers or not request.enrollment:
            logger.error("Missing required request sections")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: trial_design, endpoints, biomarkers, enrollment"
            )
        
        # Build input dictionary for predict_trial
        input_dict = build_input_dict(request)
        logger.info(f"Built input dictionary with {len(input_dict)} fields")
        
        # Call the ML model
        try:
            prediction_output = predict_trial(input_dict)
            logger.info(f"Prediction successful: {prediction_output['risk_tier']} risk")
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Model prediction failed: {str(e)}"
            )
        
        # Convert to response model
        response = convert_prediction_output(prediction_output)
        logger.info("Converted prediction to response model")
        
        # Track usage for this API key when provided
        if api_key_info is not None:
            APIKeyManager.increment_usage(api_key_info["api_key"])
            logger.info(f"Usage tracked for API key: {api_key_info['tier']}")
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in /predict: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during prediction"
        )


# ============================================================================
# BATCH PREDICTION HELPER
# ============================================================================

def process_batch_row(
    row_dict: Dict[str, Any],
    row_number: int,
) -> BatchPredictionRowResult:
    """
    Process a single row from batch prediction CSV.
    
    Args:
        row_dict: Dictionary with trial data (from CSV row)
        row_number: Row number (1-indexed)
    
    Returns:
        BatchPredictionRowResult: Result including prediction or error
    """
    trial_name = row_dict.get("trial_name")
    error_fields = {}
    
    try:
        # Build PredictionRequest from row data
        # Extract nested fields from flat CSV structure
        trial_design_data = {}
        endpoints_data = {}
        biomarkers_data = {}
        enrollment_data = {}
        
        # Map CSV columns to nested structure
        for key, value in row_dict.items():
            # Skip empty/null values and trial_name
            if pd.isna(value) or value == "" or value is None or key == "trial_name":
                continue
            
            # Convert string numbers to proper types
            value = str(value).strip() if isinstance(value, str) else value
            
            # Trial design fields
            if key == "trial_sample_size":
                trial_design_data["trial_sample_size"] = int(float(value))
            elif key == "trial_duration_weeks":
                trial_design_data["trial_duration_weeks"] = int(float(value))
            elif key == "number_of_arms":
                trial_design_data["number_of_arms"] = int(float(value))
            elif key == "phase":
                trial_design_data["phase"] = value
            elif key == "indication":
                trial_design_data["indication"] = value
            elif key == "randomization_ratio":
                trial_design_data["randomization_ratio"] = value
            
            # Endpoint fields
            elif key == "endpoint_type":
                endpoints_data["endpoint_type"] = value
            elif key == "primary_endpoint_name":
                endpoints_data["primary_endpoint_name"] = value
            
            # Enrollment fields
            elif key == "age_mean":
                enrollment_data["age_mean"] = float(value)
            elif key == "baseline_mmse":
                enrollment_data["baseline_mmse"] = float(value)
            elif key == "baseline_moca":
                enrollment_data["baseline_moca"] = float(value)
            elif key == "cdr_baseline":
                enrollment_data["cdr_baseline"] = float(value)
            
            # Biomarker enrichment strategy
            elif key == "biomarker_enrichment_strategy":
                pass  # Handle separately below
            
            # Biomarker fields (0 or 1)
            elif key in [
                "apoe_e4_carrier", "apoe_e4_homozygous",
                "ptau217_high", "csf_abeta42_40_ratio_low", "csf_ptau_elevated",
                "amyloid_pet_positive", "tau_pet_positive", "hippocampal_atrophy_binary"
            ]:
                biomarkers_data[key] = int(float(value))
            
            # Biomarker continuous fields
            elif key in [
                "ptau217_continuous", "csf_abeta42_40_ratio_continuous",
                "hippocampal_atrophy_mri"
            ]:
                biomarkers_data[key] = float(value)
        
        # Check required fields
        if not trial_design_data.get("trial_sample_size"):
            raise ValueError("Missing required field: trial_sample_size")
        if not trial_design_data.get("trial_duration_weeks"):
            raise ValueError("Missing required field: trial_duration_weeks")
        if not endpoints_data.get("endpoint_type"):
            raise ValueError("Missing required field: endpoint_type")
        if not endpoints_data.get("primary_endpoint_name"):
            raise ValueError("Missing required field: primary_endpoint_name")
        if "age_mean" not in enrollment_data:
            raise ValueError("Missing required field: age_mean")
        
        # Build request
        request = PredictionRequest(
            trial_design=trial_design_data,
            endpoints=endpoints_data,
            biomarkers=biomarkers_data if biomarkers_data else {},
            enrollment=enrollment_data,
            biomarker_enrichment_strategy=row_dict.get("biomarker_enrichment_strategy"),
        )
        
        # Convert to input dict and predict
        input_dict = build_input_dict(request)
        raw_prediction = predict_trial(input_dict)
        
        # Check if prediction had error
        if "error" in raw_prediction:
            return BatchPredictionRowResult(
                row_number=row_number,
                trial_name=trial_name,
                success=False,
                error_message=raw_prediction.get("error"),
            )
        
        # Convert prediction output
        response = convert_prediction_output(raw_prediction)
        
        # Build successful result
        return BatchPredictionRowResult(
            row_number=row_number,
            trial_name=trial_name,
            success=True,
            trial_success_probability=response.trial_success_probability,
            risk_tier=response.risk_tier,
            biomarker_explanation=response.biomarker_explanation,
            confidence_flag=response.confidence_flag,
            top_drivers=response.top_drivers,
        )
    
    except ValueError as e:
        return BatchPredictionRowResult(
            row_number=row_number,
            trial_name=trial_name,
            success=False,
            error_message=str(e),
            error_fields=error_fields if error_fields else None,
        )
    except Exception as e:
        return BatchPredictionRowResult(
            row_number=row_number,
            trial_name=trial_name,
            success=False,
            error_message=f"Unexpected error: {str(e)}",
        )


# ============================================================================
# BATCH PREDICTION ENDPOINT
# ============================================================================

@app.post(
    "/predict_batch",
    response_model=BatchPredictionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Batch Predictions"],
    summary="Batch predict CNS trial success from CSV",
    responses={
        200: {
            "description": "Batch predictions completed (with per-row success/failure)",
            "model": BatchPredictionResponse,
        },
        400: {
            "description": "Invalid file format or CSV structure",
            "model": ErrorResponse,
        },
    },
)
async def predict_batch(
    file: UploadFile = File(..., description="CSV file with trial data (one trial per row)"),
    return_csv: Optional[bool] = False,
    api_key_info: Dict[str, str] = Depends(verify_api_key),
):
    """
    Predict trial success for multiple trials from CSV file.
    
    Requires: x-api-key header with valid API key
    
    Accepts a CSV file with one trial per row. Columns should match JSON input fields.
    Each row is validated independently; invalid rows are skipped with error messages.
    
    CSV columns expected:
    - trial_sample_size (required, integer)
    - trial_duration_weeks (required, integer)
    - endpoint_type (required: 'objective', 'subjective', or 'mixed')
    - primary_endpoint_name (required, string)
    - age_mean (required, float)
    - baseline_mmse, baseline_moca, cdr_baseline (optional, float)
    - apoe_e4_carrier, ptau217_high, amyloid_pet_positive, etc. (optional, 0 or 1)
    - phase, indication, randomization_ratio (optional)
    - biomarker_enrichment_strategy (optional)
    - trial_name (optional, for identification in results)
    
    Args:
        file: Uploaded CSV file
        return_csv: If True, return results as downloadable CSV. If False, return JSON (default)
    
    Returns:
        BatchPredictionResponse: Results for all rows, or CSV file
    
    Example CSV:
        ```
        trial_name,trial_sample_size,trial_duration_weeks,endpoint_type,primary_endpoint_name,age_mean,baseline_mmse,apoe_e4_carrier,ptau217_high,amyloid_pet_positive,biomarker_enrichment_strategy
        TRIAL-001,200,52,objective,CDR-SB,72.5,22,1,1,1,at_positive
        TRIAL-002,150,26,objective,ADAS-Cog,70.0,24,0,1,1,at_positive
        TRIAL-003,300,52,subjective,ADCOMS,73.0,20,1,1,0,cognitive_only
        ```
    """
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be CSV format (.csv)"
        )
    
    try:
        # Read CSV file
        contents = await file.read()
        df = pd.read_csv(BytesIO(contents))
        
        # Validate CSV has rows
        if len(df) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file is empty"
            )
        
        # Process each row
        results = []
        for idx, row in df.iterrows():
            row_dict = row.to_dict()
            result = process_batch_row(row_dict, idx + 2)  # +2 for 1-indexing and header row
            results.append(result)
        
        # Count successes/failures
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        response = BatchPredictionResponse(
            total_rows=len(results),
            successful=successful,
            failed=failed,
            results=results,
            generated_timestamp=datetime.utcnow().isoformat() + "Z",
        )
        
        # Track usage for this API key (count successful predictions)
        for _ in range(successful):
            APIKeyManager.increment_usage(api_key_info["api_key"])
        logger.info(f"Batch usage tracked: {successful} predictions for API key tier={api_key_info['tier']}")
        
        # Return as CSV if requested
        if return_csv:
            # Build CSV output
            csv_buffer = BytesIO()
            output_data = []
            
            for result in results:
                row_data = {
                    "row_number": result.row_number,
                    "trial_name": result.trial_name or "",
                    "success": result.success,
                    "trial_success_probability": result.trial_success_probability or "",
                    "risk_tier": result.risk_tier or "",
                    "confidence_flag": result.confidence_flag or "",
                    "error_message": result.error_message or "",
                }
                output_data.append(row_data)
            
            output_df = pd.DataFrame(output_data)
            output_df.to_csv(csv_buffer, index=False)
            csv_content = csv_buffer.getvalue()
            
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=predictions.csv"}
            )
        
        return response
    
    except pd.errors.ParserError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CSV format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing batch prediction: {str(e)}"
        )


# ============================================================================
# BATCH PREDICTION CSV DOWNLOAD HELPER (POST)
# ============================================================================

@app.post(
    "/predict_batch_csv",
    status_code=status.HTTP_200_OK,
    tags=["Batch Predictions"],
    summary="Batch predict and download as CSV",
    responses={
        200: {
            "description": "CSV file with predictions",
        },
    },
)
async def predict_batch_csv(file: UploadFile = File(...)):
    """
    Batch predict and return results as downloadable CSV file.
    
    Alias for POST /predict_batch?return_csv=true
    
    Args:
        file: Uploaded CSV file with trial data
    
    Returns:
        FileResponse: CSV file with predictions
    """
    return await predict_batch(file, return_csv=True)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Detailed health check",
)
async def health():
    """
    Detailed health check endpoint.
    
    Returns:
        HealthResponse: Detailed status information
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
    )


@app.get(
    "/api-key/status",
    tags=["Auth"],
    summary="Get current API key usage status",
)
async def api_key_status(api_key: str = Depends(get_api_key_from_headers)):
    """
    Return API key usage limits and status.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing x-api-key header or Authorization Bearer token",
        )

    is_valid, tier, name = APIKeyManager.validate_key(api_key)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
        )

    stats = APIKeyManager.get_usage_stats(api_key)
    return {
        "api_key": api_key[:10] + "...",
        "tier": tier,
        "name": name,
        "usage": stats,
    }


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions."""
    logger.error(f"ValueError: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "ValidationError",
            "message": str(exc),
            "status_code": 400,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "status_code": 500,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        },
    )


# ============================================================================
# ADMIN ENDPOINTS (API KEY MANAGEMENT)
# ============================================================================

@app.get(
    "/admin/api-keys/usage/{api_key}",
    tags=["Admin"],
    summary="Get API key usage statistics",
)
async def get_api_usage(api_key: str):
    """
    Get usage statistics for an API key.
    
    Args:
        api_key: The API key to check
    
    Returns:
        Dict with usage info: tier, current_month, usage_count, limit, remaining
    
    Example:
        GET /admin/api-keys/usage/demo_tier1_key_12345
    """
    stats = APIKeyManager.get_usage_stats(api_key)
    if "error" in stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=stats["error"]
        )
    return stats


@app.get(
    "/admin/api-keys/list",
    tags=["Admin"],
    summary="List all API keys",
)
async def list_api_keys():
    """
    List all API keys with their usage information.
    
    Returns:
        List of API key info dicts
    
    Example:
        GET /admin/api-keys/list
    """
    keys = APIKeyManager.list_all_keys()
    return {
        "total_keys": len(keys),
        "keys": keys,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


@app.post(
    "/admin/api-keys/create",
    tags=["Admin"],
    summary="Create new API key",
)
async def create_api_key(
    api_key: str,
    tier: str,
    name: str,
    org: str = "Custom",
):
    """
    Create a new API key (admin operation).
    
    Args:
        api_key: The API key string to create
        tier: "tier_1" (limited) or "tier_2" (unlimited)
        name: Name/description for this key
        org: Organization name
    
    Returns:
        Success message
    
    Example:
        POST /admin/api-keys/create?api_key=custom_key_xyz&tier=tier_2&name=Customer%20ABC&org=ABC%20Corp
    """
    if tier not in ["tier_1", "tier_2"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="tier must be 'tier_1' or 'tier_2'"
        )
    
    tier_enum = KeyTier.TIER_2 if tier == "tier_2" else KeyTier.TIER_1
    success = APIKeyManager.add_api_key(api_key, tier_enum, name, org)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="API key already exists"
        )
    
    logger.info(f"New API key created: {api_key[:10]}... (tier={tier}, org={org})")
    return {
        "message": "API key created successfully",
        "api_key": api_key[:10] + "...",
        "tier": tier,
        "name": name,
        "org": org,
    }


@app.post(
    "/admin/api-keys/deactivate/{api_key}",
    tags=["Admin"],
    summary="Deactivate API key",
)
async def deactivate_api_key(api_key: str):
    """
    Deactivate an API key (admin operation).
    
    Args:
        api_key: The API key to deactivate
    
    Returns:
        Success message
    
    Example:
        POST /admin/api-keys/deactivate/demo_tier1_key_12345
    """
    success = APIKeyManager.deactivate_api_key(api_key)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )
    
    logger.info(f"API key deactivated: {api_key[:10]}...")
    return {"message": "API key deactivated successfully", "api_key": api_key[:10] + "..."}


# ============================================================================
# APPLICATION STARTUP/SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Log application startup and settings."""
    logger.info("=" * 80)
    logger.info("Genivra CNS Risk Engine API Starting Up")
    logger.info("=" * 80)
    logger.info(f"Environment: {settings.environment.value}")
    logger.info(f"API Version: {settings.app_version}")
    logger.info(f"API Host: {settings.host}:{settings.port}")
    logger.info(f"API Docs: http://{settings.host}:{settings.port}/docs")
    logger.info(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    logger.info(f"Deployment Platform: {settings.deployment_platform.value}")
    logger.info(f"CORS Origins: {settings.cors_allowed_origins}")
    logger.info(f"Tier 1 Limit: {settings.tier_1_monthly_limit}/month")
    logger.info(f"Tier 2 Limit: {'Unlimited' if settings.tier_2_monthly_limit == 0 else settings.tier_2_monthly_limit}/month")
    logger.info("=" * 80)
    
    # Print settings summary to console
    print_settings_summary()


@app.on_event("shutdown")
async def shutdown_event():
    """Log application shutdown."""
    logger.info("Genivra CNS Risk Engine API Shutting Down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
