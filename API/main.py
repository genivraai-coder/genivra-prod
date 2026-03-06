"""
Genivra CNS Risk Engine API
===========================

Production FastAPI application for predicting clinical trial success
in neurological indications.

Aligned with engine/ml_engine.py v3.0.

Changes from v2.0:
    - model_version pulled from engine response (not hardcoded)
    - convert_prediction_output() updated for v3.0 top_drivers schema
    - /predict no longer raises on "error" key (engine never hard-errors)
    - Admin endpoints protected by ADMIN_API_KEY header
    - startup_event() warms the ML model before first request
    - /health returns engine status + last training metrics
    - /usage endpoint for API key self-service stats
    - Removed dead code (error_fields dict in process_batch_row)

Quick start:
    uvicorn api.main:app --reload

Demo API keys:
    Tier 1 (100 req/month) : demo_tier1_key_12345
    Tier 2 (unlimited)     : demo_tier2_key_67890

Admin key (change in .env):
    ADMIN_API_KEY=genivra_admin_secret_2026

API docs: http://localhost:8000/docs
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
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import logging
import pandas as pd

# Allow running from repo root or api/ subdirectory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine.ml_engine import predict_trial, score_trial_rule_based


# ====================================================================
# LOGGING
# ====================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ====================================================================
# SETTINGS
# ====================================================================

class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING     = "staging"
    PRODUCTION  = "production"


class DeploymentPlatform(str, Enum):
    LOCAL   = "local"
    HEROKU  = "heroku"
    RAILWAY = "railway"
    RENDER  = "render"
    VERCEL  = "vercel"
    GCP     = "gcp"
    AWS     = "aws"
    AZURE   = "azure"


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.

    All fields can be overridden by setting the corresponding env var
    (case-insensitive). Example: PORT=9000 overrides the default port.
    """

    # API
    environment:     Environment        = Field(default=Environment.DEVELOPMENT)
    app_name:        str                = Field(default="Genivra CNS Risk Engine")
    app_version:     str                = Field(default="3.0-production")
    host:            str                = Field(default="0.0.0.0")
    port:            int                = Field(default=8000)
    log_level:       str                = Field(default="INFO")

    # Auth
    admin_api_key:       str            = Field(default="genivra_admin_secret_2026",
                                                description="Key required for /admin/* endpoints")
    api_keys_override:   Optional[str]  = Field(default=None,
                                                description="Override keys: key1:tier2:name1,key2:tier1:name2")
    tier_1_monthly_limit: int           = Field(default=100)
    tier_2_monthly_limit: int           = Field(default=0)   # 0 = unlimited

    # CORS
    cors_allowed_origins:   str  = Field(default="*")
    cors_allow_credentials: bool = Field(default=True)

    # Model artifact paths (used for reference only — engine manages its own paths)
    model_artifact_dir:  str = Field(default="models/artifacts")

    # Security / docs
    require_https:   bool = Field(default=False)
    enable_api_docs: bool = Field(default=True)
    enable_redoc:    bool = Field(default=True)
    enable_openapi:  bool = Field(default=True)

    # Deployment
    deployment_platform: DeploymentPlatform = Field(default=DeploymentPlatform.LOCAL)
    database_url:        Optional[str]       = Field(default=None)

    class Config:
        env_file          = ".env"
        env_file_encoding = "utf-8"
        case_sensitive    = False
        extra             = "ignore"

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION

    @property
    def is_development(self) -> bool:
        return self.environment == Environment.DEVELOPMENT

    @property
    def cors_origins_list(self) -> List[str]:
        if self.cors_allowed_origins == "*":
            return ["*"]
        return [o.strip() for o in self.cors_allowed_origins.split(",")]

    @property
    def api_keys_dict(self) -> Dict[str, Dict]:
        """Parse API_KEYS_OVERRIDE env var into a dict."""
        if not self.api_keys_override:
            return {}
        result = {}
        for spec in self.api_keys_override.split(","):
            parts = spec.strip().split(":")
            if len(parts) >= 3:
                key  = parts[0].strip()
                tier = parts[1].strip()
                name = ":".join(parts[2:]).strip()
                result[key] = {"tier": tier, "name": name}
        return result


settings = Settings()


def _log_settings() -> None:
    logger.info("=" * 70)
    logger.info("GENIVRA CONFIGURATION")
    logger.info("=" * 70)
    logger.info(f"Environment : {settings.environment.value}")
    logger.info(f"Platform    : {settings.deployment_platform.value}")
    logger.info(f"API         : http://{settings.host}:{settings.port}")
    logger.info(f"Log level   : {settings.log_level}")
    logger.info(f"Docs        : {settings.enable_api_docs}")
    logger.info(f"Tier 1 limit: {settings.tier_1_monthly_limit}/month")
    logger.info(f"Tier 2 limit: {'Unlimited' if settings.tier_2_monthly_limit == 0 else settings.tier_2_monthly_limit}/month")
    logger.info(f"CORS        : {settings.cors_allowed_origins}")
    logger.info("=" * 70)


# ====================================================================
# API KEY MANAGEMENT
# ====================================================================

class KeyTier(str, Enum):
    TIER_1 = "tier_1"
    TIER_2 = "tier_2"


class APIKeyManager:
    """
    Thread-safe in-memory API key store with tier-based rate limiting.

    Tier 1: 100 requests/month
    Tier 2: unlimited

    NOTE: In-memory only — resets on server restart.
    FUTURE: Migrate to PostgreSQL + Redis for persistence.
    """

    # Built-in demo keys — extend via API_KEYS_OVERRIDE env var or /admin endpoints
    API_KEYS: Dict[str, Dict] = {
        "demo_tier1_key_12345": {
            "tier":    KeyTier.TIER_1,
            "name":    "Demo Key (Tier 1)",
            "org":     "Genivra",
            "created": "2026-01-01T00:00:00",
            "active":  True,
        },
        "demo_tier2_key_67890": {
            "tier":    KeyTier.TIER_2,
            "name":    "Demo Key (Tier 2)",
            "org":     "Genivra",
            "created": "2026-01-01T00:00:00",
            "active":  True,
        },
    }

    TIER_LIMITS: Dict[KeyTier, Optional[int]] = {
        KeyTier.TIER_1: 100,
        KeyTier.TIER_2: None,   # None = unlimited
    }

    # {api_key: {"YYYY-MM": count}}
    USAGE_TRACKER: Dict[str, Dict[str, int]] = {}

    _lock = threading.Lock()

    # ── Validation ──

    @staticmethod
    def validate_key(api_key: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """Return (is_valid, tier_value, name)."""
        with APIKeyManager._lock:
            info = APIKeyManager.API_KEYS.get(api_key)
            if not info or not info.get("active", True):
                return False, None, None
            tier = info["tier"]
            return True, tier.value if isinstance(tier, KeyTier) else tier, info.get("name", "Unknown")

    @staticmethod
    def check_rate_limit(api_key: str) -> Tuple[bool, str]:
        """Return (allowed, message)."""
        with APIKeyManager._lock:
            info = APIKeyManager.API_KEYS.get(api_key)
            if not info:
                return False, "Invalid API key"
            tier  = info["tier"]
            limit = APIKeyManager.TIER_LIMITS.get(tier)
            if limit is None:
                return True, "OK (unlimited)"
            month = APIKeyManager._month()
            used  = APIKeyManager.USAGE_TRACKER.get(api_key, {}).get(month, 0)
            if used >= limit:
                return False, f"Monthly limit of {limit} requests exceeded"
            return True, f"OK ({limit - used - 1} requests remaining this month)"

    @staticmethod
    def increment_usage(api_key: str) -> None:
        with APIKeyManager._lock:
            month = APIKeyManager._month()
            APIKeyManager.USAGE_TRACKER.setdefault(api_key, {})
            APIKeyManager.USAGE_TRACKER[api_key][month] = \
                APIKeyManager.USAGE_TRACKER[api_key].get(month, 0) + 1

    @staticmethod
    def get_usage_stats(api_key: str) -> Dict:
        if api_key not in APIKeyManager.API_KEYS:
            return {"error": "Invalid API key"}
        with APIKeyManager._lock:
            info  = APIKeyManager.API_KEYS[api_key]
            tier  = info["tier"]
            month = APIKeyManager._month()
            used  = APIKeyManager.USAGE_TRACKER.get(api_key, {}).get(month, 0)
            limit = APIKeyManager.TIER_LIMITS.get(tier)
            return {
                "api_key":       api_key,
                "name":          info.get("name"),
                "tier":          tier.value if isinstance(tier, KeyTier) else tier,
                "current_month": month,
                "current_usage": used,
                "limit":         limit,
                "remaining":     None if limit is None else max(0, limit - used),
            }

    # ── Admin operations ──

    @staticmethod
    def add_api_key(api_key: str, tier: KeyTier, name: str, org: str = "Custom") -> bool:
        with APIKeyManager._lock:
            if api_key in APIKeyManager.API_KEYS:
                return False
            APIKeyManager.API_KEYS[api_key] = {
                "tier":    tier,
                "name":    name,
                "org":     org,
                "created": datetime.now().isoformat(),
                "active":  True,
            }
            return True

    @staticmethod
    def deactivate_api_key(api_key: str) -> bool:
        with APIKeyManager._lock:
            if api_key not in APIKeyManager.API_KEYS:
                return False
            APIKeyManager.API_KEYS[api_key]["active"] = False
            return True

    @staticmethod
    def list_all_keys() -> List[Dict]:
        with APIKeyManager._lock:
            month = APIKeyManager._month()
            return [
                {
                    "api_key":             k,
                    "name":                v.get("name"),
                    "tier":                v["tier"].value if isinstance(v["tier"], KeyTier) else v["tier"],
                    "org":                 v.get("org"),
                    "active":              v.get("active"),
                    "created":             v.get("created"),
                    "current_month_usage": APIKeyManager.USAGE_TRACKER.get(k, {}).get(month, 0),
                }
                for k, v in APIKeyManager.API_KEYS.items()
            ]

    @staticmethod
    def _month() -> str:
        return datetime.now().strftime("%Y-%m")

    @staticmethod
    def load_from_env() -> None:
        """Import any keys from API_KEYS_OVERRIDE environment variable."""
        for key, meta in settings.api_keys_dict.items():
            tier_str = meta.get("tier", "tier_1")
            tier     = KeyTier.TIER_2 if tier_str == "tier_2" else KeyTier.TIER_1
            APIKeyManager.add_api_key(key, tier, meta.get("name", "Env Key"))


# ====================================================================
# PYDANTIC REQUEST / RESPONSE MODELS
# ====================================================================

# ── Requests ──

class BiomarkerInput(BaseModel):
    apoe_e4_carrier:                Optional[int]   = Field(default=None, description="APOE ε4 carrier (0/1)")
    apoe_e4_homozygous:             Optional[int]   = Field(default=None, description="APOE ε4 homozygous (0/1)")
    ptau217_high:                   Optional[int]   = Field(default=None, description="pTau-217 elevated (0/1)")
    ptau217_continuous:             Optional[float] = Field(default=None, description="pTau-217 continuous (pg/mL)")
    csf_abeta42_40_ratio_low:       Optional[int]   = Field(default=None, description="CSF Aβ42/40 low (0/1)")
    csf_abeta42_40_ratio_continuous:Optional[float] = Field(default=None, description="CSF Aβ42/40 continuous")
    csf_ptau_elevated:              Optional[int]   = Field(default=None, description="CSF p-tau elevated (0/1)")
    amyloid_pet_positive:           Optional[int]   = Field(default=None, description="Amyloid PET positive (0/1)")
    tau_pet_positive:               Optional[int]   = Field(default=None, description="Tau PET positive (0/1)")
    hippocampal_atrophy_mri:        Optional[float] = Field(default=None, description="Hippocampal atrophy (continuous)")
    hippocampal_atrophy_binary:     Optional[int]   = Field(default=None, description="Hippocampal atrophy (0/1)")


class TrialDesignInput(BaseModel):
    phase:                Optional[str] = Field(default="Phase II")
    indication:           Optional[str] = Field(default="Alzheimer's Disease")
    trial_sample_size:    int           = Field(..., gt=0,  description="Target enrollment n")
    trial_duration_weeks: int           = Field(..., gt=0,  description="Trial duration (weeks)")
    number_of_arms:       int           = Field(default=2, ge=1)
    randomization_ratio:  Optional[str] = Field(default="1:1")


class EndpointInput(BaseModel):
    endpoint_type:         str = Field(..., description="'objective' or 'subjective'")
    primary_endpoint_name: str = Field(..., description="e.g. 'CDR-SB', 'MMSE', 'amyloid_clearance'")


class EnrollmentInput(BaseModel):
    age_mean:       float           = Field(..., ge=0, description="Mean enrollment age")
    baseline_mmse:  Optional[float] = Field(default=None, description="Baseline MMSE (0–30)")
    baseline_moca:  Optional[float] = Field(default=None, description="Baseline MoCA (0–30)")
    cdr_baseline:   Optional[float] = Field(default=None, description="CDR at baseline (0–3)")


class PredictionRequest(BaseModel):
    trial_design:                  TrialDesignInput
    endpoints:                     EndpointInput
    biomarkers:                    BiomarkerInput
    enrollment:                    EnrollmentInput
    phase:                         Optional[str] = Field(default="Phase II")
    indication:                    Optional[str] = Field(default="Alzheimer's Disease")
    biomarker_enrichment_strategy: Optional[str] = Field(default="unspecified")

    model_config = {
        "json_schema_extra": {
            "example": {
                "phase": "Phase II",
                "indication": "Alzheimer's Disease",
                "trial_design": {
                    "trial_sample_size": 200,
                    "trial_duration_weeks": 78,
                    "number_of_arms": 2,
                    "randomization_ratio": "1:1",
                },
                "endpoints": {
                    "endpoint_type": "objective",
                    "primary_endpoint_name": "amyloid_clearance",
                },
                "biomarkers": {
                    "amyloid_pet_positive": 1,
                    "ptau217_high": 1,
                    "apoe_e4_carrier": 1,
                    "tau_pet_positive": 1,
                },
                "enrollment": {
                    "age_mean": 71.0,
                    "baseline_mmse": 22.0,
                    "cdr_baseline": 0.5,
                },
                "biomarker_enrichment_strategy": "at_positive",
            }
        }
    }


# ── Responses ──

class FeatureDriver(BaseModel):
    feature_name:     str   = Field(description="Human-readable feature label")
    coefficient:      float = Field(description="Model coefficient")
    direction:        str   = Field(description="'positive' or 'negative'")
    impact_magnitude: float = Field(description="|coefficient|")


class PredictionResponse(BaseModel):
    trial_success_probability: float            = Field(ge=0, le=1)
    risk_tier:                 str              = Field(description="LOW / MEDIUM / HIGH")
    top_drivers:               List[FeatureDriver]
    biomarker_explanation:     str
    confidence_flag:           str              = Field(description="HIGH / MEDIUM / LOW")
    missing_biomarker_count:   int
    scoring_method:            str              = Field(description="ml_model / rule_based / base_rate_only")
    model_version:             str
    base_rate:                 Optional[float]  = Field(default=None, description="Historical base rate used")
    indication_matched:        Optional[str]    = Field(default=None)
    generated_timestamp:       str


class ErrorResponse(BaseModel):
    error:     str
    detail:    str
    timestamp: str


class HealthResponse(BaseModel):
    status:         str
    version:        str
    environment:    Optional[str]  = None
    engine_ready:   Optional[bool] = None
    last_auc:       Optional[float]= None
    uptime_seconds: Optional[float]= None


class UsageResponse(BaseModel):
    api_key:       str
    name:          Optional[str]
    tier:          str
    current_month: str
    current_usage: int
    limit:         Optional[int]
    remaining:     Optional[int]


# ── Batch ──

class BatchPredictionRowResult(BaseModel):
    row_number:                int
    trial_name:                Optional[str]  = None
    success:                   bool
    trial_success_probability: Optional[float]= None
    risk_tier:                 Optional[str]  = None
    confidence_flag:           Optional[str]  = None
    scoring_method:            Optional[str]  = None
    error_message:             Optional[str]  = None


class BatchPredictionResponse(BaseModel):
    total_rows:          int
    successful:          int
    failed:              int
    results:             List[BatchPredictionRowResult]
    generated_timestamp: str


# ====================================================================
# FASTAPI APP
# ====================================================================

app = FastAPI(
    title=settings.app_name,
    description=(
        "AI-powered predictive scoring engine for neurological clinical trials. "
        "Predicts Phase II success probability using biomarker profiles, trial design "
        "parameters, and enrollment quality metrics."
    ),
    version=settings.app_version,
    docs_url="/docs"       if settings.enable_api_docs else None,
    redoc_url="/redoc"     if settings.enable_redoc    else None,
    openapi_url="/openapi.json" if settings.enable_openapi else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Module-level startup timestamp and engine state
_startup_time: Optional[datetime] = None
_engine_ready: bool = False
_last_auc:     Optional[float] = None


# ====================================================================
# AUTH DEPENDENCIES
# ====================================================================

async def verify_api_key(x_api_key: str = Header(None)) -> Dict[str, str]:
    """
    Validate x-api-key header. Raises 401 if missing/invalid, 429 if rate-limited.
    Returns dict with api_key, tier, name for use in endpoint handlers.
    """
    if not x_api_key or not x_api_key.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing x-api-key header. Include your API key as: x-api-key: <key>",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    is_valid, tier, name = APIKeyManager.validate_key(x_api_key)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    allowed, message = APIKeyManager.check_rate_limit(x_api_key)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=message,
            headers={"Retry-After": "2592000"},
        )

    return {"api_key": x_api_key, "tier": tier, "name": name}


async def verify_admin_key(x_admin_key: str = Header(None)) -> None:
    """
    Validate x-admin-key header for /admin/* endpoints.
    Raises 401 if missing or incorrect.
    """
    if not x_admin_key or x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid x-admin-key header.",
            headers={"WWW-Authenticate": "AdminKey"},
        )


# ====================================================================
# UTILITY FUNCTIONS
# ====================================================================

def build_input_dict(request: PredictionRequest) -> Dict[str, Any]:
    """
    Flatten a PredictionRequest into the dict format expected by predict_trial().
    None values are stripped — the engine handles missing fields gracefully.
    """
    raw = {
        # Top-level (phase/indication can be on root or inside trial_design)
        "phase":     request.phase or request.trial_design.phase,
        "indication":request.indication or request.trial_design.indication,

        # Trial design
        "trial_sample_size":              request.trial_design.trial_sample_size,
        "trial_duration_weeks":           request.trial_design.trial_duration_weeks,
        "number_of_arms":                 request.trial_design.number_of_arms,
        "randomization_ratio":            request.trial_design.randomization_ratio,

        # Endpoints
        "endpoint_type":                  request.endpoints.endpoint_type,
        "primary_endpoint_name":          request.endpoints.primary_endpoint_name,

        # Biomarkers
        "apoe_e4_carrier":                request.biomarkers.apoe_e4_carrier,
        "apoe_e4_homozygous":             request.biomarkers.apoe_e4_homozygous,
        "ptau217_high":                   request.biomarkers.ptau217_high,
        "ptau217_continuous":             request.biomarkers.ptau217_continuous,
        "csf_abeta42_40_ratio_low":       request.biomarkers.csf_abeta42_40_ratio_low,
        "csf_abeta42_40_ratio_continuous":request.biomarkers.csf_abeta42_40_ratio_continuous,
        "csf_ptau_elevated":              request.biomarkers.csf_ptau_elevated,
        "amyloid_pet_positive":           request.biomarkers.amyloid_pet_positive,
        "tau_pet_positive":               request.biomarkers.tau_pet_positive,
        "hippocampal_atrophy_mri":        request.biomarkers.hippocampal_atrophy_mri,
        "hippocampal_atrophy_binary":     request.biomarkers.hippocampal_atrophy_binary,

        # Enrollment
        "age_mean":      request.enrollment.age_mean,
        "baseline_mmse": request.enrollment.baseline_mmse,
        "baseline_moca": request.enrollment.baseline_moca,
        "cdr_baseline":  request.enrollment.cdr_baseline,

        # Enrichment
        "biomarker_enrichment_strategy": request.biomarker_enrichment_strategy,
    }

    # Strip None so engine applies its own defaults/fallbacks
    return {k: v for k, v in raw.items() if v is not None}


def convert_prediction_output(raw: Dict[str, Any]) -> PredictionResponse:
    """
    Convert predict_trial() output dict → PredictionResponse Pydantic model.

    Handles the v3.0 top_drivers schema:
        {rank, feature, raw_feature, coefficient, importance_score, direction}
    """
    drivers = []
    for d in raw.get("top_drivers", []):
        drivers.append(
            FeatureDriver(
                # v3.0 engine uses "feature" (human-readable) — fall back to raw_feature
                feature_name     = d.get("feature") or d.get("raw_feature") or "unknown",
                coefficient      = float(d.get("coefficient", 0.0)),
                direction        = d.get("direction", "positive"),
                impact_magnitude = float(d.get("importance_score", abs(d.get("coefficient", 0.0)))),
            )
        )

    return PredictionResponse(
        trial_success_probability = float(raw.get("trial_success_probability", 0.0)),
        risk_tier                 = raw.get("risk_tier", "UNKNOWN"),
        top_drivers               = drivers,
        biomarker_explanation     = raw.get("biomarker_explanation", ""),
        confidence_flag           = raw.get("confidence_flag", "LOW"),
        missing_biomarker_count   = int(raw.get("missing_biomarker_count", 0)),
        # Pull version and method from engine response — not hardcoded
        scoring_method            = raw.get("scoring_method", "unknown"),
        model_version             = raw.get("model_version", settings.app_version),
        base_rate                 = raw.get("base_rate"),
        indication_matched        = raw.get("indication_matched"),
        generated_timestamp       = datetime.utcnow().isoformat() + "Z",
    )


def process_batch_row(row_dict: Dict, row_number: int) -> BatchPredictionRowResult:
    """
    Process a single flat CSV row into a BatchPredictionRowResult.

    Maps flat CSV column names to the nested PredictionRequest structure,
    validates required fields, calls predict_trial(), and returns a result.
    Missing or empty cells are silently skipped (engine handles gracefully).
    """
    trial_name = row_dict.get("trial_name")

    try:
        trial_design_data: Dict[str, Any] = {}
        endpoints_data:    Dict[str, Any] = {}
        biomarkers_data:   Dict[str, Any] = {}
        enrollment_data:   Dict[str, Any] = {}
        enrichment:        Optional[str]  = None

        for key, value in row_dict.items():
            # Skip nulls, empty strings, and the identifier column
            try:
                if value is None or key == "trial_name":
                    continue
                if isinstance(value, float) and pd.isna(value):
                    continue
                if str(value).strip() == "":
                    continue
            except Exception:
                continue

            v_str = str(value).strip()

            # ── Trial design ──
            if key == "trial_sample_size":
                trial_design_data["trial_sample_size"] = int(float(v_str))
            elif key == "trial_duration_weeks":
                trial_design_data["trial_duration_weeks"] = int(float(v_str))
            elif key == "number_of_arms":
                trial_design_data["number_of_arms"] = int(float(v_str))
            elif key == "phase":
                trial_design_data["phase"] = v_str
            elif key == "indication":
                trial_design_data["indication"] = v_str
            elif key == "randomization_ratio":
                trial_design_data["randomization_ratio"] = v_str

            # ── Endpoints ──
            elif key == "endpoint_type":
                endpoints_data["endpoint_type"] = v_str
            elif key == "primary_endpoint_name":
                endpoints_data["primary_endpoint_name"] = v_str

            # ── Enrollment ──
            elif key == "age_mean":
                enrollment_data["age_mean"] = float(v_str)
            elif key == "baseline_mmse":
                enrollment_data["baseline_mmse"] = float(v_str)
            elif key == "baseline_moca":
                enrollment_data["baseline_moca"] = float(v_str)
            elif key == "cdr_baseline":
                enrollment_data["cdr_baseline"] = float(v_str)

            # ── Enrichment ──
            elif key == "biomarker_enrichment_strategy":
                enrichment = v_str

            # ── Biomarkers (binary) ──
            elif key in {
                "apoe_e4_carrier", "apoe_e4_homozygous",
                "ptau217_high", "csf_abeta42_40_ratio_low", "csf_ptau_elevated",
                "amyloid_pet_positive", "tau_pet_positive", "hippocampal_atrophy_binary",
            }:
                biomarkers_data[key] = int(float(v_str))

            # ── Biomarkers (continuous) ──
            elif key in {
                "ptau217_continuous", "csf_abeta42_40_ratio_continuous", "hippocampal_atrophy_mri",
            }:
                biomarkers_data[key] = float(v_str)

        # Required field validation
        missing_required = []
        if not trial_design_data.get("trial_sample_size"):    missing_required.append("trial_sample_size")
        if not trial_design_data.get("trial_duration_weeks"): missing_required.append("trial_duration_weeks")
        if not endpoints_data.get("endpoint_type"):           missing_required.append("endpoint_type")
        if not endpoints_data.get("primary_endpoint_name"):   missing_required.append("primary_endpoint_name")
        if "age_mean" not in enrollment_data:                 missing_required.append("age_mean")

        if missing_required:
            raise ValueError(f"Missing required columns: {', '.join(missing_required)}")

        # Build and run prediction
        request = PredictionRequest(
            trial_design                  = trial_design_data,
            endpoints                     = endpoints_data,
            biomarkers                    = biomarkers_data or {},
            enrollment                    = enrollment_data,
            biomarker_enrichment_strategy = enrichment,
        )

        input_dict = build_input_dict(request)
        raw        = predict_trial(input_dict)
        converted  = convert_prediction_output(raw)

        return BatchPredictionRowResult(
            row_number                = row_number,
            trial_name                = trial_name,
            success                   = True,
            trial_success_probability = converted.trial_success_probability,
            risk_tier                 = converted.risk_tier,
            confidence_flag           = converted.confidence_flag,
            scoring_method            = converted.scoring_method,
        )

    except Exception as exc:
        logger.warning(f"Batch row {row_number} failed: {exc}")
        return BatchPredictionRowResult(
            row_number    = row_number,
            trial_name    = trial_name,
            success       = False,
            error_message = str(exc),
        )


# ====================================================================
# HEALTH ENDPOINTS
# ====================================================================

@app.get(
    "/",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Root health check",
)
async def root():
    """Lightweight health check — returns running status and version."""
    return HealthResponse(status="running", version=settings.app_version)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Detailed health check",
)
async def health_check():
    """
    Detailed health check including engine readiness and last training AUC.
    Does not require an API key.
    """
    uptime = (datetime.utcnow() - _startup_time).total_seconds() if _startup_time else None
    return HealthResponse(
        status         = "running" if _engine_ready else "warming_up",
        version        = settings.app_version,
        environment    = settings.environment.value,
        engine_ready   = _engine_ready,
        last_auc       = _last_auc,
        uptime_seconds = uptime,
    )


# ====================================================================
# PREDICTION ENDPOINTS
# ====================================================================

@app.post(
    "/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    tags=["Predictions"],
    summary="Score a single CNS trial",
    responses={
        200: {"description": "Successful prediction", "model": PredictionResponse},
        400: {"description": "Invalid input",          "model": ErrorResponse},
        401: {"description": "Invalid API key"},
        429: {"description": "Rate limit exceeded"},
        500: {"description": "Internal server error",  "model": ErrorResponse},
    },
)
async def predict_endpoint(
    request:      PredictionRequest,
    api_key_info: Dict[str, str] = Depends(verify_api_key),
):
    """
    Predict CNS clinical trial success probability.

    Returns success probability (0–1), risk tier (LOW/MEDIUM/HIGH),
    top feature drivers, biomarker explanation, and confidence flag.

    The engine never returns an error — it falls back to rule-based scoring
    or the historical base rate if the ML model is unavailable.
    """
    try:
        input_dict = build_input_dict(request)
        raw        = predict_trial(input_dict)
        response   = convert_prediction_output(raw)

        APIKeyManager.increment_usage(api_key_info["api_key"])
        logger.info(
            f"Prediction: p={response.trial_success_probability:.1%} "
            f"tier={response.risk_tier} "
            f"method={response.scoring_method} "
            f"key_tier={api_key_info['tier']}"
        )
        return response

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Prediction endpoint error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {exc}",
        )


@app.post(
    "/predict_batch",
    response_model=Optional[BatchPredictionResponse],
    status_code=status.HTTP_200_OK,
    tags=["Predictions"],
    summary="Batch score trials from CSV",
    responses={
        200: {
            "description": "Batch complete",
            "content": {
                "application/json": {},
                "text/csv": {"schema": {"type": "string"}},
            },
        },
        400: {"description": "Invalid CSV"},
        401: {"description": "Invalid API key"},
        429: {"description": "Rate limit exceeded"},
    },
)
async def predict_batch(
    file:         UploadFile       = File(..., description="CSV file with trial rows"),
    return_csv:   bool             = False,
    api_key_info: Dict[str, str]   = Depends(verify_api_key),
):
    """
    Batch-score multiple trials from a CSV upload.

    Required CSV columns:
        trial_sample_size, trial_duration_weeks, endpoint_type,
        primary_endpoint_name, age_mean

    Optional columns:
        trial_name, phase, indication, all biomarker fields,
        baseline_mmse, baseline_moca, cdr_baseline,
        biomarker_enrichment_strategy, randomization_ratio

    Set return_csv=true to receive results as a downloadable CSV.
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a .csv file.",
        )

    try:
        contents = await file.read()
        df = pd.read_csv(BytesIO(contents))

        if len(df) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file is empty.",
            )

        results = [
            process_batch_row(row.to_dict(), idx + 2)
            for idx, row in df.iterrows()
        ]

        successful = sum(1 for r in results if r.success)
        failed     = len(results) - successful

        # Charge usage per successful prediction
        for _ in range(successful):
            APIKeyManager.increment_usage(api_key_info["api_key"])

        logger.info(
            f"Batch complete: {successful}/{len(results)} succeeded "
            f"key_tier={api_key_info['tier']}"
        )

        batch_response = BatchPredictionResponse(
            total_rows          = len(results),
            successful          = successful,
            failed              = failed,
            results             = results,
            generated_timestamp = datetime.utcnow().isoformat() + "Z",
        )

        if return_csv:
            buf = BytesIO()
            pd.DataFrame([
                {
                    "row_number":                r.row_number,
                    "trial_name":                r.trial_name or "",
                    "success":                   r.success,
                    "trial_success_probability": r.trial_success_probability or "",
                    "risk_tier":                 r.risk_tier or "",
                    "confidence_flag":           r.confidence_flag or "",
                    "scoring_method":            r.scoring_method or "",
                    "error_message":             r.error_message or "",
                }
                for r in results
            ]).to_csv(buf, index=False)
            return Response(
                content     = buf.getvalue(),
                media_type  = "text/csv",
                headers     = {"Content-Disposition": "attachment; filename=genivra_predictions.csv"},
            )

        return batch_response

    except HTTPException:
        raise
    except pd.errors.ParserError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid CSV format: {exc}")
    except Exception as exc:
        logger.error(f"Batch endpoint error: {exc}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Batch processing error: {exc}")


# ====================================================================
# SELF-SERVICE USAGE ENDPOINT
# ====================================================================

@app.get(
    "/usage",
    response_model=UsageResponse,
    tags=["Account"],
    summary="Check your API usage",
)
async def get_usage(api_key_info: Dict[str, str] = Depends(verify_api_key)):
    """Returns current-month usage stats for the authenticated API key."""
    stats = APIKeyManager.get_usage_stats(api_key_info["api_key"])
    if "error" in stats:
        raise HTTPException(status_code=404, detail=stats["error"])
    return UsageResponse(**stats)


# ====================================================================
# ADMIN ENDPOINTS  (require x-admin-key header)
# ====================================================================

@app.get(
    "/admin/api-keys",
    tags=["Admin"],
    summary="List all API keys",
    dependencies=[Depends(verify_admin_key)],
)
async def admin_list_keys():
    """List all API keys with usage. Requires x-admin-key header."""
    keys = APIKeyManager.list_all_keys()
    return {
        "total_keys": len(keys),
        "keys":       keys,
        "timestamp":  datetime.utcnow().isoformat() + "Z",
    }


@app.post(
    "/admin/api-keys",
    tags=["Admin"],
    summary="Create a new API key",
    dependencies=[Depends(verify_admin_key)],
)
async def admin_create_key(
    api_key: str,
    tier:    str,
    name:    str,
    org:     str = "Custom",
):
    """
    Create a new API key. Requires x-admin-key header.

    Params:
        api_key: The key string (you choose it — make it long and random)
        tier:    tier_1 (100 req/month) or tier_2 (unlimited)
        name:    Descriptive label
        org:     Organisation name
    """
    if tier not in ("tier_1", "tier_2"):
        raise HTTPException(status_code=400, detail="tier must be 'tier_1' or 'tier_2'")

    tier_enum = KeyTier.TIER_2 if tier == "tier_2" else KeyTier.TIER_1
    created   = APIKeyManager.add_api_key(api_key, tier_enum, name, org)

    if not created:
        raise HTTPException(status_code=409, detail="API key already exists")

    logger.info(f"Admin: created key {api_key[:10]}... tier={tier} org={org}")
    return {
        "message": "API key created",
        "api_key": api_key[:10] + "...",
        "tier":    tier,
        "name":    name,
        "org":     org,
    }


@app.delete(
    "/admin/api-keys/{api_key}",
    tags=["Admin"],
    summary="Deactivate an API key",
    dependencies=[Depends(verify_admin_key)],
)
async def admin_deactivate_key(api_key: str):
    """Deactivate an API key. Requires x-admin-key header."""
    deactivated = APIKeyManager.deactivate_api_key(api_key)
    if not deactivated:
        raise HTTPException(status_code=404, detail="API key not found")
    logger.info(f"Admin: deactivated key {api_key[:10]}...")
    return {"message": "API key deactivated", "api_key": api_key[:10] + "..."}


@app.post(
    "/admin/retrain",
    tags=["Admin"],
    summary="Retrain the ML model",
    dependencies=[Depends(verify_admin_key)],
)
async def admin_retrain():
    """
    Trigger a full model retrain on synthetic data.
    Requires x-admin-key header.
    Runs synchronously — may take 10–30s.
    """
    global _engine_ready, _last_auc
    try:
        from engine.ml_engine import train_full_pipeline
        metrics, msg = train_full_pipeline(verbose=True)
        _engine_ready = True
        _last_auc     = metrics.get("auc")
        logger.info(f"Admin retrain complete: {msg}")
        return {
            "message":  "Retrain complete",
            "metrics":  metrics,
            "timestamp":datetime.utcnow().isoformat() + "Z",
        }
    except Exception as exc:
        logger.error(f"Admin retrain failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Retrain failed: {exc}")


# ====================================================================
# STARTUP / SHUTDOWN
# ====================================================================

@app.on_event("startup")
async def startup_event():
    """
    On startup:
    1. Log configuration
    2. Load API keys from env vars
    3. Warm the ML engine (triggers auto-train if no artifacts exist)
    """
    global _startup_time, _engine_ready, _last_auc

    _startup_time = datetime.utcnow()
    _log_settings()

    # Load any keys from API_KEYS_OVERRIDE env var
    APIKeyManager.load_from_env()

    # Warm ML engine — this triggers auto-train on first deploy
    logger.info("Warming ML engine...")
    try:
        # Import the cache-warming function directly from the engine
        from engine.ml_engine import _ensure_model_ready, _load_metadata
        _ensure_model_ready()
        meta      = _load_metadata() or {}
        eval_meta = meta.get("eval_metrics", {})
        _last_auc = eval_meta.get("auc")
        _engine_ready = True
        logger.info(
            f"ML engine ready | "
            f"AUC={_last_auc:.4f if _last_auc else 'N/A'} | "
            f"trained_at={meta.get('trained_at', 'unknown')}"
        )
    except Exception as exc:
        # Non-fatal — rule-based fallback will handle predictions
        logger.warning(f"ML engine warm-up failed ({exc}). Rule-based fallback active.")
        _engine_ready = False


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Genivra CNS Risk Engine API shutting down.")


# ====================================================================
# ENTRYPOINT
# ====================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host      = settings.host,
        port      = settings.port,
        reload    = settings.is_development,
        log_level = settings.log_level.lower(),
    )
