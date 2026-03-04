"""
Genivra CNS Risk Engine API - Consolidated Single-File Application

Complete FastAPI application for predicting clinical trial success in neurological indications.
This file consolidates all API functionality including:
- Configuration management and environment handling
- Authentication and API key management with rate limiting
- Request/response validators (Pydantic models)
- Core prediction endpoints (single and batch)
- Administrative endpoints for API key management
- Integrated error handling and logging

Author: Genivra Team
Date: February 24, 2026
Version: 2.0 (Consolidated)

QUICK START:
    uvicorn api.main:app --reload

DEMO API KEYS:
    - Tier 1 (100 req/month): demo_tier1_key_12345
    - Tier 2 (unlimited): demo_tier2_key_67890

API DOCS: http://localhost:8000/docs
"""

# ====================================================================
# IMPORTS
# ====================================================================

import sys
import os
import threading
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from io import BytesIO

from fastapi import FastAPI, HTTPException, status, UploadFile, File, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings
import logging
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.ml_engine import predict_trial, score_trial_rule_based


# ====================================================================
# LOGGING CONFIGURATION
# ====================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ====================================================================
# CONFIGURATION: ENUMS AND SETTINGS
# ====================================================================

class Environment(str, Enum):
    """Deployment environment enum."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DeploymentPlatform(str, Enum):
    """Supported deployment platforms."""
    LOCAL = "local"
    HEROKU = "heroku"
    RAILWAY = "railway"
    RENDER = "render"
    VERCEL = "vercel"
    GCP = "gcp"
    AWS = "aws"
    AZURE = "azure"


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    Configuration is loaded from:
    1. Environment variables
    2. .env file (if present)
    3. Default values defined below
    """
    
    # ====== API Configuration ======
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Deployment environment"
    )
    
    app_name: str = Field(
        default="Genivra CNS Risk Engine",
        description="Application name"
    )
    
    app_version: str = Field(
        default="2.0-consolidated",
        description="Application version"
    )
    
    host: str = Field(
        default="0.0.0.0",
        description="Host to bind API server"
    )
    
    port: int = Field(
        default=8000,
        description="Port to bind API server"
    )
    
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    
    # ====== Authentication Configuration ======
    api_keys_override: Optional[str] = Field(
        default=None,
        description="Override API keys from environment (format: key1:tier2:name1,key2:tier1:name2)"
    )
    
    tier_1_monthly_limit: int = Field(
        default=100,
        description="Monthly request limit for Tier 1 API keys"
    )
    
    tier_2_monthly_limit: int = Field(
        default=0,  # 0 = unlimited
        description="Monthly request limit for Tier 2 API keys (0 = unlimited)"
    )
    
    # ====== CORS Configuration ======
    cors_allowed_origins: str = Field(
        default="*",
        description="CORS allowed origins (comma-separated or *)"
    )
    
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests"
    )
    
    # ====== Model Configuration ======
    model_artifact_dir: str = Field(
        default="Models/artifacts",
        description="Path to model artifacts directory"
    )
    
    feature_scaler_path: str = Field(
        default="Models/artifacts/feature_scaler.pkl",
        description="Path to feature scaler pickle file"
    )
    
    logistic_model_path: str = Field(
        default="Models/artifacts/logistic_model.pkl",
        description="Path to logistic regression model pickle file"
    )
    
    # ====== Security Configuration ======
    require_https: bool = Field(
        default=False,
        description="Require HTTPS in production"
    )
    
    enable_api_docs: bool = Field(
        default=True,
        description="Enable Swagger UI documentation"
    )
    
    enable_redoc: bool = Field(
        default=True,
        description="Enable ReDoc documentation"
    )
    
    enable_openapi: bool = Field(
        default=True,
        description="Enable OpenAPI schema generation"
    )
    
    # ====== Monitoring & Logging ======
    enable_metrics: bool = Field(
        default=True,
        description="Enable metrics collection"
    )
    
    log_predictions: bool = Field(
        default=False,
        description="Log all predictions to file"
    )
    
    predictions_log_file: str = Field(
        default="logs/predictions.log",
        description="Path to predictions log file"
    )
    
    # ====== Deployment Configuration ======
    deployment_platform: DeploymentPlatform = Field(
        default=DeploymentPlatform.LOCAL,
        description="Current deployment platform"
    )
    
    database_url: Optional[str] = Field(
        default=None,
        description="Database URL (for future migration from in-memory)"
    )
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment == Environment.PRODUCTION
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment == Environment.DEVELOPMENT
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if self.cors_allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_allowed_origins.split(",")]
    
    @property
    def api_keys_dict(self) -> Dict[str, Dict]:
        """
        Parse API keys override from environment variable.
        Format: key1:tier2:name1,key2:tier1:name2
        Returns dict mapping API key to {tier, name}
        """
        if not self.api_keys_override:
            return {}
        
        keys_dict = {}
        for key_spec in self.api_keys_override.split(","):
            parts = key_spec.strip().split(":")
            if len(parts) >= 3:
                api_key = parts[0].strip()
                tier = parts[1].strip()
                name = ":".join(parts[2:]).strip()  # Allow colons in name
                keys_dict[api_key] = {"tier": tier, "name": name}
        
        return keys_dict


# Global settings instance
settings = Settings()


def print_settings_summary():
    """Print current settings to console (for debugging). Omits sensitive information."""
    print("\n" + "=" * 70)
    print("GENIVRA CONFIGURATION SUMMARY")
    print("=" * 70)
    print(f"Environment:         {settings.environment.value}")
    print(f"Platform:            {settings.deployment_platform.value}")
    print(f"API:                 http://{settings.host}:{settings.port}")
    print(f"Log Level:           {settings.log_level}")
    print(f"API Docs:            {settings.enable_api_docs}")
    print(f"Tier 1 Limit:        {settings.tier_1_monthly_limit}/month")
    print(f"Tier 2 Limit:        {'Unlimited' if settings.tier_2_monthly_limit == 0 else settings.tier_2_monthly_limit}/month")
    print(f"CORS Origins:        {settings.cors_allowed_origins}")
    print(f"Model Path:          {settings.logistic_model_path}")
    print(f"Scaler Path:         {settings.feature_scaler_path}")
    print("=" * 70 + "\n")


# ====================================================================
# AUTHENTICATION: API KEY MANAGEMENT
# ====================================================================

class KeyTier(str, Enum):
    """API key tier levels."""
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"


class APIKeyManager:
    """
    In-memory API key manager with tier-based rate limiting.
    
    Provides:
    - API key validation
    - Rate limiting per tier (TIER_1: 100/month, TIER_2: unlimited)
    - Usage tracking by month (YYYY-MM format)
    - Admin operations to add/deactivate keys
    
    FUTURE: Replace with database backend (PostgreSQL + Redis) for production
    
    Demo Keys:
    - demo_tier1_key_12345 (Tier 1: 100 requests/month)
    - demo_tier2_key_67890 (Tier 2: unlimited)
    """
    
    # Demo API keys (in-memory)
    API_KEYS: Dict[str, Dict] = {
        "demo_tier1_key_12345": {
            "tier": KeyTier.TIER_1,
            "name": "Demo Key (Tier 1)",
            "org": "Genivra",
            "created": "2026-01-01T00:00:00",
            "active": True
        },
        "demo_tier2_key_67890": {
            "tier": KeyTier.TIER_2,
            "name": "Demo Key (Tier 2)",
            "org": "Genivra",
            "created": "2026-01-01T00:00:00",
            "active": True
        },
    }
    
    # Tier limits (requests per month)
    TIER_LIMITS: Dict[KeyTier, Optional[int]] = {
        KeyTier.TIER_1: 100,      # 100 requests per month
        KeyTier.TIER_2: None,      # None = unlimited
    }
    
    # Usage tracking: {api_key: {month_year: count}}
    USAGE_TRACKER: Dict[str, Dict[str, int]] = {}
    
    # Thread-safe access
    _lock = threading.Lock()
    
    @staticmethod
    def validate_key(api_key: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate API key and return tier and name.
        
        Args:
            api_key: The API key to validate
        
        Returns:
            Tuple of (is_valid: bool, tier: str, name: str)
        
        Example:
            is_valid, tier, name = APIKeyManager.validate_key("demo_tier1_key_12345")
        """
        with APIKeyManager._lock:
            if api_key not in APIKeyManager.API_KEYS:
                return (False, None, None)
            
            key_info = APIKeyManager.API_KEYS[api_key]
            
            # Check if active
            if not key_info.get("active", True):
                return (False, None, None)
            
            tier = key_info.get("tier")
            name = key_info.get("name", "Unknown")
            
            return (True, tier.value if tier else None, name)
    
    @staticmethod
    def check_rate_limit(api_key: str) -> Tuple[bool, str]:
        """
        Check if API key has exceeded its rate limit this month.
        
        Args:
            api_key: The API key to check
        
        Returns:
            Tuple of (allowed: bool, message: str)
        
        Example:
            allowed, message = APIKeyManager.check_rate_limit("demo_tier1_key_12345")
        """
        with APIKeyManager._lock:
            if api_key not in APIKeyManager.API_KEYS:
                return (False, "Invalid API key")
            
            key_info = APIKeyManager.API_KEYS[api_key]
            tier = key_info.get("tier")
            limit = APIKeyManager.TIER_LIMITS.get(tier)
            
            # Tier 2 has no limit
            if limit is None:
                return (True, "OK")
            
            # Check current month usage
            month_year = APIKeyManager.get_current_month_year()
            usage = APIKeyManager.USAGE_TRACKER.get(api_key, {}).get(month_year, 0)
            
            if usage >= limit:
                return (False, f"Monthly limit of {limit} requests exceeded. Reset in {month_year}")
            
            return (True, f"OK ({limit - usage - 1} requests remaining)")
    
    @staticmethod
    def increment_usage(api_key: str) -> None:
        """
        Increment usage counter for API key (call after successful prediction).
        
        Args:
            api_key: The API key that made the request
        
        Example:
            APIKeyManager.increment_usage("demo_tier1_key_12345")
        """
        with APIKeyManager._lock:
            month_year = APIKeyManager.get_current_month_year()
            
            # Initialize tracking if needed
            if api_key not in APIKeyManager.USAGE_TRACKER:
                APIKeyManager.USAGE_TRACKER[api_key] = {}
            
            # Increment counter
            APIKeyManager.USAGE_TRACKER[api_key][month_year] = \
                APIKeyManager.USAGE_TRACKER[api_key].get(month_year, 0) + 1
    
    @staticmethod
    def get_current_month_year() -> str:
        """Get current month in YYYY-MM format."""
        return datetime.now().strftime("%Y-%m")
    
    @staticmethod
    def get_usage_stats(api_key: str) -> Dict:
        """
        Get usage statistics for an API key.
        
        Returns:
            Dict with api_key, tier, current_month, current_usage, limit, remaining
        """
        if api_key not in APIKeyManager.API_KEYS:
            return {"error": "Invalid API key"}
        
        with APIKeyManager._lock:
            key_info = APIKeyManager.API_KEYS[api_key]
            tier = key_info.get("tier")
            month_year = APIKeyManager.get_current_month_year()
            usage = APIKeyManager.USAGE_TRACKER.get(api_key, {}).get(month_year, 0)
            limit = APIKeyManager.TIER_LIMITS.get(tier)
            
            return {
                "api_key": api_key,
                "name": key_info.get("name"),
                "tier": tier.value,
                "current_month": month_year,
                "current_usage": usage,
                "limit": limit,
                "remaining": None if limit is None else (limit - usage),
            }
    
    @staticmethod
    def add_api_key(api_key: str, tier: KeyTier, name: str, org: str = "Custom") -> bool:
        """
        Add a new API key (admin operation).
        
        Args:
            api_key: The API key to add
            tier: KeyTier enum value
            name: Name/description for this key
            org: Organization name
        
        Returns:
            True if added successfully, False if key already exists
        """
        with APIKeyManager._lock:
            if api_key in APIKeyManager.API_KEYS:
                return False  # Key already exists
            
            APIKeyManager.API_KEYS[api_key] = {
                "tier": tier,
                "name": name,
                "org": org,
                "created": datetime.now().isoformat(),
                "active": True
            }
            return True
    
    @staticmethod
    def deactivate_api_key(api_key: str) -> bool:
        """
        Deactivate an API key (admin operation).
        
        Returns: True if deactivated, False if key not found
        """
        with APIKeyManager._lock:
            if api_key not in APIKeyManager.API_KEYS:
                return False
            
            APIKeyManager.API_KEYS[api_key]["active"] = False
            return True
    
    @staticmethod
    def list_all_keys() -> list:
        """List all API keys with their info (admin operation)."""
        with APIKeyManager._lock:
            keys_list = []
            for key, info in APIKeyManager.API_KEYS.items():
                month_year = APIKeyManager.get_current_month_year()
                usage = APIKeyManager.USAGE_TRACKER.get(key, {}).get(month_year, 0)
                keys_list.append({
                    "api_key": key,
                    "name": info.get("name"),
                    "tier": info.get("tier").value,
                    "active": info.get("active"),
                    "created": info.get("created"),
                    "current_month_usage": usage
                })
            return keys_list
    
    @staticmethod
    def reset_monthly_usage() -> None:
        """Reset monthly usage (call this at month end)."""
        with APIKeyManager._lock:
            month_year = APIKeyManager.get_current_month_year()
            for key in APIKeyManager.USAGE_TRACKER:
                if month_year in APIKeyManager.USAGE_TRACKER[key]:
                    del APIKeyManager.USAGE_TRACKER[key][month_year]


# ====================================================================
# MODELS: PYDANTIC REQUEST/RESPONSE SCHEMAS
# ====================================================================

# ====== Request Models ======

class BiomarkerInput(BaseModel):
    """Clinical biomarker measurements and indicators."""
    
    apoe_e4_carrier: Optional[int] = Field(
        default=None,
        description="APOE ε4 carrier status (0=non-carrier, 1=carrier)"
    )
    apoe_e4_homozygous: Optional[int] = Field(
        default=None,
        description="APOE ε4 homozygous (0=no, 1=yes)"
    )
    ptau217_high: Optional[int] = Field(
        default=None,
        description="pTau-217 elevated above threshold (0=no, 1=yes)"
    )
    ptau217_continuous: Optional[float] = Field(
        default=None,
        description="pTau-217 continuous measurement (pg/mL)"
    )
    csf_abeta42_40_ratio_low: Optional[int] = Field(
        default=None,
        description="CSF Aβ42/40 ratio below threshold (0=no, 1=yes)"
    )
    csf_abeta42_40_ratio_continuous: Optional[float] = Field(
        default=None,
        description="CSF Aβ42/40 ratio continuous value"
    )
    csf_ptau_elevated: Optional[int] = Field(
        default=None,
        description="CSF p-tau elevated (0=no, 1=yes)"
    )
    amyloid_pet_positive: Optional[int] = Field(
        default=None,
        description="Amyloid PET imaging positive (0=no, 1=yes)"
    )
    tau_pet_positive: Optional[int] = Field(
        default=None,
        description="Tau PET imaging positive (0=no, 1=yes)"
    )
    hippocampal_atrophy_mri: Optional[float] = Field(
        default=None,
        description="Hippocampal atrophy continuous measurement"
    )
    hippocampal_atrophy_binary: Optional[int] = Field(
        default=None,
        description="Hippocampal atrophy present (0=no, 1=yes)"
    )


class TrialDesignInput(BaseModel):
    """Clinical trial design parameters."""
    
    phase: Optional[str] = Field(
        default="Phase II",
        description="Trial phase (Phase I, II, III, IV)"
    )
    indication: Optional[str] = Field(
        default="Alzheimer's Disease",
        description="Clinical indication"
    )
    trial_sample_size: int = Field(
        ...,
        description="Target enrollment number",
        gt=0
    )
    trial_duration_weeks: int = Field(
        ...,
        description="Trial duration in weeks",
        gt=0
    )
    number_of_arms: int = Field(
        default=2,
        description="Number of trial arms",
        ge=1
    )
    randomization_ratio: Optional[str] = Field(
        default="1:1",
        description="Randomization ratio (e.g., '1:1', '2:1')"
    )


class EndpointInput(BaseModel):
    """Primary endpoint specifications."""
    
    endpoint_type: str = Field(
        ...,
        description="Endpoint type: 'objective' (biomarker-based) or 'subjective' (cognitive scale)"
    )
    primary_endpoint_name: str = Field(
        ...,
        description="Primary endpoint name (e.g., 'CDR-SB', 'MMSE')"
    )


class EnrollmentInput(BaseModel):
    """Patient population parameters."""
    
    age_mean: float = Field(
        ...,
        description="Mean age at enrollment (years)",
        ge=0
    )
    baseline_mmse: Optional[float] = Field(
        default=None,
        description="Mean MMSE score at baseline (0-30)"
    )
    baseline_moca: Optional[float] = Field(
        default=None,
        description="Mean MoCA score at baseline (0-30)"
    )
    cdr_baseline: Optional[float] = Field(
        default=None,
        description="Mean Clinical Dementia Rating at baseline (0-3)"
    )


class PredictionRequest(BaseModel):
    """Complete trial prediction request."""
    
    trial_design: TrialDesignInput
    endpoints: EndpointInput
    biomarkers: BiomarkerInput
    enrollment: EnrollmentInput
    phase: Optional[str] = Field(
        default="Phase II",
        description="Trial phase"
    )
    indication: Optional[str] = Field(
        default="Alzheimer's Disease",
        description="Clinical indication"
    )
    biomarker_enrichment_strategy: Optional[str] = Field(
        default="unspecified",
        description="Strategy for patient enrichment"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "phase": "Phase II",
                "indication": "Alzheimer's Disease",
                "trial_design": {
                    "trial_sample_size": 150,
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
                    "age_mean": 70.0,
                    "baseline_mmse": 20.0,
                    "cdr_baseline": 1.0
                },
                "biomarker_enrichment_strategy": "at_positive"
            }
        }
    }


# ====== Response Models ======

class FeatureDriver(BaseModel):
    """Feature importance driver in prediction."""
    
    feature_name: str = Field(
        description="Name of the feature driving prediction"
    )
    coefficient: float = Field(
        description="Model coefficient for feature"
    )
    direction: str = Field(
        description="Direction of influence: 'positive' or 'negative'"
    )
    impact_magnitude: float = Field(
        description="Absolute impact magnitude (|coefficient|)"
    )


class PredictionResponse(BaseModel):
    """Prediction response with risk assessment."""
    
    trial_success_probability: float = Field(
        description="Predicted probability of trial success (0-1)",
        ge=0,
        le=1
    )
    risk_tier: str = Field(
        description="Risk category: 'HIGH', 'MEDIUM', 'LOW'"
    )
    top_drivers: List[FeatureDriver] = Field(
        description="Top 3 features driving the prediction"
    )
    biomarker_explanation: str = Field(
        description="Natural language explanation of biomarker importance"
    )
    confidence_flag: str = Field(
        description="Confidence level: 'HIGH', 'MEDIUM', 'LOW'"
    )
    missing_biomarker_count: int = Field(
        description="Number of biomarkers not provided in input"
    )
    model_version: str = Field(
        description="ML model version used for prediction"
    )
    generated_timestamp: str = Field(
        description="ISO 8601 timestamp of prediction generation"
    )


class ErrorResponse(BaseModel):
    """Standard error response."""
    
    error: str = Field(
        description="Error type/message"
    )
    detail: str = Field(
        description="Detailed error description"
    )
    timestamp: str = Field(
        description="ISO 8601 timestamp"
    )


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str = Field(
        description="API status: 'running', 'degraded', 'offline'"
    )
    version: str = Field(
        description="API version"
    )


# ====== Batch Prediction Models ======

class BatchPredictionRowResult(BaseModel):
    """Individual row result in batch prediction."""
    
    row_number: int = Field(
        description="Row number in CSV (1-indexed)"
    )
    trial_name: Optional[str] = Field(
        default=None,
        description="Trial name from 'trial_name' column"
    )
    success: bool = Field(
        description="Whether prediction succeeded for this row"
    )
    trial_success_probability: Optional[float] = Field(
        default=None,
        description="Predicted success probability (if successful)"
    )
    risk_tier: Optional[str] = Field(
        default=None,
        description="Risk tier (if successful)"
    )
    confidence_flag: Optional[str] = Field(
        default=None,
        description="Confidence level (if successful)"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message (if failed)"
    )


class BatchPredictionResponse(BaseModel):
    """Batch prediction response."""
    
    total_rows: int = Field(
        description="Total rows processed"
    )
    successful: int = Field(
        description="Number of successful predictions"
    )
    failed: int = Field(
        description="Number of failed predictions"
    )
    results: List[BatchPredictionRowResult] = Field(
        description="Results for each row"
    )
    generated_timestamp: str = Field(
        description="ISO 8601 timestamp"
    )


# ====================================================================
# FASTAPI APP SETUP
# ====================================================================

app = FastAPI(
    title=settings.app_name,
    description="AI-powered predictive scoring engine for neurological clinical trials",
    version=settings.app_version,
    docs_url="/docs" if settings.enable_api_docs else None,
    redoc_url="/redoc" if settings.enable_redoc else None,
    openapi_url="/openapi.json" if settings.enable_openapi else None,
)


# ====== CORS Middleware ======

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ====================================================================
# AUTHENTICATION DEPENDENCY
# ====================================================================

async def verify_api_key(x_api_key: str = Header(None)) -> Dict[str, str]:
    """
    Verify API key from x-api-key header.
    
    Args:
        x_api_key: API key from request header
    
    Returns:
        Dict with api_key and tier information
    
    Raises:
        HTTPException: 401 if key missing or invalid, 429 if rate limited
    """
    # Check if key is provided
    if not x_api_key:
        logger.warning("API request without x-api-key header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing x-api-key header",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Validate key format (basic check)
    if not isinstance(x_api_key, str) or len(x_api_key.strip()) == 0:
        logger.warning(f"API request with invalid key format")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Validate key exists and is active
    is_valid, tier, name = APIKeyManager.validate_key(x_api_key)
    if not is_valid:
        logger.warning(f"API request with invalid/inactive key: {x_api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Check rate limit
    allowed, message = APIKeyManager.check_rate_limit(x_api_key)
    if not allowed:
        logger.warning(f"Rate limit exceeded for key: {x_api_key[:10]}...")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=message,
            headers={"Retry-After": "2592000"},  # 30 days in seconds
        )
    
    logger.info(f"API key validated: tier={tier}, name={name}")
    return {"api_key": x_api_key, "tier": tier, "name": name}


# ====================================================================
# UTILITY FUNCTIONS
# ====================================================================

def convert_prediction_output(raw_output: dict) -> PredictionResponse:
    """
    Convert raw predict_trial() output to Pydantic PredictionResponse.
    
    Args:
        raw_output: Dictionary from predict_trial() with keys:
                   - trial_success_probability
                   - risk_tier
                   - top_drivers (list of dicts with feature, coefficient, direction, importance_score)
                   - biomarker_explanation
                   - confidence_flag
                   - missing_biomarker_count
    
    Returns:
        PredictionResponse: Validated Pydantic model
    """
    # Convert top_drivers list of dicts to FeatureDriver objects
    feature_drivers = []
    if "top_drivers" in raw_output:
        for feature_dict in raw_output["top_drivers"]:
            # Dict structure from ml_engine.get_top_features():
            # {rank, feature, coefficient, importance_score, direction}
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
        model_version="v2.0-consolidated",
        generated_timestamp=datetime.utcnow().isoformat() + "Z",
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


def process_batch_row(row_dict: Dict, row_number: int) -> BatchPredictionRowResult:
    """
    Process a single row from batch prediction CSV.
    
    Args:
        row_dict: Dictionary from pandas row
        row_number: Row number (1-indexed including header)
    
    Returns:
        BatchPredictionRowResult with prediction or error
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
        
        # Convert successful prediction
        converted = convert_prediction_output(raw_prediction)
        
        return BatchPredictionRowResult(
            row_number=row_number,
            trial_name=trial_name,
            success=True,
            trial_success_probability=converted.trial_success_probability,
            risk_tier=converted.risk_tier,
            confidence_flag=converted.confidence_flag,
        )
    
    except Exception as e:
        logger.error(f"Error processing batch row {row_number}: {str(e)}", exc_info=True)
        return BatchPredictionRowResult(
            row_number=row_number,
            trial_name=trial_name,
            success=False,
            error_message=f"Error: {str(e)}"
        )


# ====================================================================
# API ENDPOINTS
# ====================================================================

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
        
    Example:
        curl http://localhost:8000/ \\
          -H "x-api-key: demo_tier1_key_12345"
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
        401: {
            "description": "Missing or invalid API key",
        },
        429: {
            "description": "Rate limit exceeded",
        },
        500: {
            "description": "Internal server error during prediction",
            "model": ErrorResponse,
        },
    },
)
async def predict(request: PredictionRequest, api_key_info: Dict[str, str] = Depends(verify_api_key)):
    """
    Predict CNS trial success probability and risk tier.
    
    Requires: x-api-key header with valid API key
    
    Accepts structured trial design, biomarker, and enrollment data.
    Returns interpretable success probability (0-1), risk category, and driver explanation.
    
    Args:
        request: PredictionRequest with trial parameters
    
    Returns:
        PredictionResponse with probability, risk tier, feature drivers, and explanation
    
    Example:
        curl -X POST http://localhost:8000/predict \\
          -H "x-api-key: demo_tier1_key_12345" \\
          -H "Content-Type: application/json" \\
          -d '{
            "phase": "Phase II",
            "indication": "Alzheimer'\''s Disease",
            "trial_design": {
              "trial_sample_size": 150,
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
              "age_mean": 70.0,
              "baseline_mmse": 20.0,
              "cdr_baseline": 1.0
            },
            "biomarker_enrichment_strategy": "at_positive"
          }'
    """
    try:
        # Convert request to input dict
        input_dict = build_input_dict(request)
        
        # Run prediction from consolidated ML engine
        raw_prediction = predict_trial(input_dict)
        
        # Check for errors from ML engine
        if "error" in raw_prediction:
            logger.error(f"ML engine error: {raw_prediction.get('error')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=raw_prediction.get("error")
            )
        
        # Convert to response format
        response = convert_prediction_output(raw_prediction)
        
        # Track API usage
        APIKeyManager.increment_usage(api_key_info["api_key"])
        logger.info(f"Prediction completed: success_prob={response.trial_success_probability:.1%}, tier={api_key_info['tier']}")
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@app.post(
    "/predict_batch",
    response_model=Optional[BatchPredictionResponse],
    status_code=status.HTTP_200_OK,
    tags=["Batch Predictions"],
    summary="Batch predict from CSV file",
    responses={
        200: {
            "description": "Batch predictions completed",
            "content": {
                "application/json": {
                    "example": {
                        "total_rows": 3,
                        "successful": 2,
                        "failed": 1,
                        "results": [
                            {
                                "row_number": 2,
                                "trial_name": "LECANEMAB-2",
                                "success": True,
                                "trial_success_probability": 0.92,
                                "risk_tier": "LOW",
                                "confidence_flag": "HIGH"
                            }
                        ],
                        "generated_timestamp": "2026-02-24T12:34:56.789Z"
                    }
                },
                "text/csv": {
                    "schema": {"type": "string"},
                    "example": "row_number,trial_name,success,trial_success_probability,risk_tier\\n2,TRIAL-1,true,0.92,LOW"
                }
            },
        },
    },
)
async def predict_batch(
    file: UploadFile = File(...),
    return_csv: bool = False,
    api_key_info: Dict[str, str] = Depends(verify_api_key)
):
    """
    Batch predict trial success from CSV file upload.
    
    CSV Format:
        - Required columns: trial_sample_size, trial_duration_weeks, endpoint_type, primary_endpoint_name, age_mean
        - Optional columns: phase, indication, all biomarker fields, baseline_mmse, baseline_moca, cdr_baseline
        - Optional trial identification: trial_name (arbitrary text, echoed in results)
    
    Args:
        file: CSV file with trials (UTF-8 encoded)
        return_csv: If true, return results as downloadable CSV instead of JSON
        api_key_info: Required x-api-key header
    
    Returns:
        BatchPredictionResponse (JSON) or CSV file
    
    Example CSV:
        trial_name,phase,indication,trial_sample_size,trial_duration_weeks,endpoint_type,primary_endpoint_name,age_mean,apoe_e4_carrier,ptau217_high
        LECANEMAB-2,Phase II,Alzheimer's Disease,150,52,objective,CDR-SB,70.0,1,1
        HIGH-RISK,Phase II,Alzheimer's Disease,50,12,subjective,MMSE,65.0,0,0
    
    Example:
        curl -X POST http://localhost:8000/predict_batch \\
          -H "x-api-key: demo_tier1_key_12345" \\
          -F "file=@trials.csv" \\
          -F "return_csv=false"
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV (.csv) file"
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


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Detailed health check",
)
async def health_check():
    """
    Detailed health check with configuration info.
    
    Returns:
        HealthResponse: Status, version, and deployment info
    """
    return HealthResponse(
        status="running",
        version=settings.app_version,
    )


# ====================================================================
# ADMIN ENDPOINTS
# ====================================================================

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


# ====================================================================
# APPLICATION STARTUP/SHUTDOWN EVENTS
# ====================================================================

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


# ====================================================================
# APPLICATION RUN
# ====================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.is_development,
        log_level=settings.log_level.lower(),
    )
