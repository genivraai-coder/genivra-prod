"""
Pydantic models for API request/response validation.

Defines strict input and output schemas for the Genivra CNS Risk Engine API.
"""

from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime


# ============================================================================
# REQUEST MODELS
# ============================================================================

class BiomarkerInput(BaseModel):
    """Biomarker data for trial prediction."""
    
    # Genetic biomarkers
    apoe_e4_carrier: Optional[int] = Field(None, description="1 if ≥1 ε4 allele, 0 if none, null if unknown")
    apoe_e4_homozygous: Optional[int] = Field(None, description="1 if e4/e4, 0 otherwise, null if unknown")
    
    # Blood biomarkers (plasma)
    ptau217_high: Optional[int] = Field(None, description="1 if > 14.5 pg/mL, 0 if ≤14.5, null if not measured")
    ptau217_continuous: Optional[float] = Field(None, description="Raw p-tau217 value in pg/mL")
    
    # CSF biomarkers
    csf_abeta42_40_ratio_low: Optional[int] = Field(None, description="1 if < 0.5, 0 if ≥ 0.5, null if not available")
    csf_abeta42_40_ratio_continuous: Optional[float] = Field(None, description="Raw CSF Aβ42/Aβ40 ratio")
    csf_ptau_elevated: Optional[int] = Field(None, description="1 if > 79 pg/mL, 0 if ≤79, null if not measured")
    
    # Imaging biomarkers
    amyloid_pet_positive: Optional[int] = Field(None, description="1 if SUVR > 1.2, 0 if ≤1.2, null if not performed")
    tau_pet_positive: Optional[int] = Field(None, description="1 if SUVR > 1.3, 0 if ≤1.3, null if not performed")
    hippocampal_atrophy_mri: Optional[float] = Field(None, description="Raw hippocampal volume in mm³")
    hippocampal_atrophy_binary: Optional[int] = Field(None, description="1 if < 10th percentile, 0 otherwise, null if unknown")
    
    class Config:
        json_schema_extra = {
            "example": {
                "apoe_e4_carrier": 1,
                "ptau217_high": 1,
                "amyloid_pet_positive": 1,
                "tau_pet_positive": 0,
                "hippocampal_atrophy_binary": 1
            }
        }


class TrialDesignInput(BaseModel):
    """Trial design parameters."""
    
    phase: Optional[str] = Field(None, description="Trial phase (e.g., 'Phase II', 'Phase III')")
    indication: Optional[str] = Field(None, description="Disease indication (e.g., 'Alzheimer\'s Disease', 'ALS')")
    trial_sample_size: int = Field(..., gt=0, description="Planned sample size (must be > 0)")
    trial_duration_weeks: int = Field(..., gt=0, description="Planned trial duration in weeks (must be > 0)")
    number_of_arms: Optional[int] = Field(None, ge=1, description="Number of parallel treatment arms")
    randomization_ratio: Optional[str] = Field(None, description="Randomization ratio (e.g., '1:1', '2:1', 'open_label')")
    
    class Config:
        json_schema_extra = {
            "example": {
                "phase": "Phase II",
                "indication": "Alzheimer's Disease",
                "trial_sample_size": 200,
                "trial_duration_weeks": 52,
                "number_of_arms": 2,
                "randomization_ratio": "1:1"
            }
        }


class EndpointInput(BaseModel):
    """Endpoint specification."""
    
    endpoint_type: str = Field(..., description="'objective', 'subjective', or 'mixed'")
    primary_endpoint_name: str = Field(..., description="e.g., 'CDR-SB', 'ADAS-Cog', 'MMSE', 'amyloid_pet_suvr', 'other'")
    
    @field_validator('endpoint_type')
    @classmethod
    def validate_endpoint_type(cls, v):
        allowed = {'objective', 'subjective', 'mixed'}
        if v.lower() not in allowed:
            raise ValueError(f'endpoint_type must be one of {allowed}')
        return v.lower()
    
    class Config:
        json_schema_extra = {
            "example": {
                "endpoint_type": "objective",
                "primary_endpoint_name": "CDR-SB"
            }
        }


class EnrollmentInput(BaseModel):
    """Patient enrollment and baseline characteristics."""
    
    age_mean: float = Field(..., description="Mean baseline age of cohort (years)")
    baseline_mmse: Optional[float] = Field(None, ge=0, le=30, description="Mean MMSE at baseline (0-30)")
    baseline_moca: Optional[float] = Field(None, ge=0, le=30, description="Mean MoCA at baseline (0-30)")
    cdr_baseline: Optional[float] = Field(None, ge=0, le=18, description="Mean CDR sum-of-boxes at baseline (0-18)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "age_mean": 72.5,
                "baseline_mmse": 22.0,
                "cdr_baseline": 1.5
            }
        }


class PredictionRequest(BaseModel):
    """Complete prediction request payload."""
    
    phase: Optional[str] = None
    indication: Optional[str] = None
    trial_design: TrialDesignInput
    endpoints: EndpointInput
    biomarkers: BiomarkerInput
    enrollment: EnrollmentInput
    biomarker_enrichment_strategy: Optional[str] = Field(
        None,
        description="'amyloid_positive', 'tau_positive', 'at_positive', 'cognitive_only', 'none', 'unknown'"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "phase": "Phase II",
                "indication": "Alzheimer's Disease",
                "trial_design": {
                    "phase": "Phase II",
                    "indication": "Alzheimer's Disease",
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
                    "amyloid_pet_positive": 1,
                    "tau_pet_positive": 0
                },
                "enrollment": {
                    "age_mean": 72.5,
                    "baseline_mmse": 22.0,
                    "cdr_baseline": 1.5
                },
                "biomarker_enrichment_strategy": "at_positive"
            }
        }


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class FeatureDriver(BaseModel):
    """A single feature driver in the prediction."""
    feature_name: str
    coefficient: float
    direction: str  # "positive" or "negative"
    impact_magnitude: float  # absolute value of coefficient


class PredictionResponse(BaseModel):
    """Structured prediction output."""
    
    trial_success_probability: float = Field(..., ge=0, le=1, description="Probability of trial success (0-1)")
    risk_tier: str = Field(..., description="Risk category: 'LOW', 'MEDIUM', or 'HIGH'")
    top_drivers: List[FeatureDriver] = Field(..., description="Top 5 feature drivers")
    biomarker_explanation: str = Field(..., description="Plain-English summary of biomarker influences")
    confidence_flag: str = Field(..., description="Data completeness confidence: 'HIGH', 'MEDIUM', or 'LOW'")
    missing_biomarker_count: int = Field(default=0, ge=0, description="Number of missing required biomarkers")
    model_version: str = Field(default="v1.0", description="Model version")
    generated_timestamp: str = Field(..., description="ISO 8601 UTC timestamp")


class ErrorResponse(BaseModel):
    """Error response payload."""
    
    error: str
    message: str
    status_code: int
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


class HealthResponse(BaseModel):
    """Health check response."""
    
    status: str
    version: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")


# ============================================================================
# BATCH PREDICTION MODELS
# ============================================================================

class BatchPredictionRowResult(BaseModel):
    """Result for a single row in batch prediction."""
    
    row_number: int = Field(..., description="Row number (1-indexed) in input CSV")
    trial_name: Optional[str] = Field(None, description="Optional trial name/identifier from CSV")
    success: bool = Field(..., description="True if prediction succeeded, False if validation error")
    
    # Prediction output (null if error)
    trial_success_probability: Optional[float] = Field(None, description="Probability of success (0-1)")
    risk_tier: Optional[str] = Field(None, description="Risk tier: LOW, MEDIUM, HIGH")
    biomarker_explanation: Optional[str] = Field(None, description="Natural language explanation")
    confidence_flag: Optional[str] = Field(None, description="Data confidence: HIGH, MEDIUM, LOW")
    top_drivers: Optional[List[FeatureDriver]] = Field(None, description="Top 5 feature drivers")
    
    # Error information (null if success)
    error_message: Optional[str] = Field(None, description="Error message if validation failed")
    error_fields: Optional[Dict[str, str]] = Field(None, description="Field-specific errors")
    
    class Config:
        json_schema_extra = {
            "example": {
                "row_number": 1,
                "trial_name": "TRIAL-001",
                "success": True,
                "trial_success_probability": 0.85,
                "risk_tier": "LOW",
                "biomarker_explanation": "...",
                "confidence_flag": "HIGH",
                "top_drivers": [
                    {"feature_name": "trial_sample_size", "coefficient": 1.422, "direction": "positive", "impact_magnitude": 1.422}
                ],
                "error_message": None,
                "error_fields": None
            }
        }


class BatchPredictionResponse(BaseModel):
    """Response containing batch prediction results."""
    
    total_rows: int = Field(..., description="Total number of rows processed")
    successful: int = Field(..., description="Number of successful predictions")
    failed: int = Field(..., description="Number of failed predictions")
    results: List[BatchPredictionRowResult] = Field(..., description="Prediction results for each row")
    
    model_version: str = Field(default="v1.0", description="Model version")
    generated_timestamp: str = Field(..., description="ISO 8601 UTC timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_rows": 3,
                "successful": 2,
                "failed": 1,
                "results": [
                    {
                        "row_number": 1,
                        "trial_name": "TRIAL-001",
                        "success": True,
                        "trial_success_probability": 0.85,
                        "risk_tier": "LOW",
                        "confidence_flag": "HIGH"
                    },
                    {
                        "row_number": 2,
                        "trial_name": "TRIAL-002",
                        "success": False,
                        "error_message": "Missing required field: trial_sample_size"
                    }
                ],
                "model_version": "v1.0",
                "generated_timestamp": "2026-02-24T18:30:45.123456Z"
            }
        }
