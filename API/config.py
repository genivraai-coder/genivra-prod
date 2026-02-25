"""
Genivra Configuration Module

Loads configuration from environment variables with sensible defaults.
Supports multiple deployment platforms (local, Heroku, Railway, GCP, AWS, Azure).

Usage:
    from API.config import settings
    print(settings.API_KEYS)
    print(settings.LOG_LEVEL)
"""

import os
from typing import Dict, List, Optional
from enum import Enum
from pydantic_settings import BaseSettings
from pydantic import Field


class Environment(str, Enum):
    """Supported environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class DeploymentPlatform(str, Enum):
    """Supported deployment platforms"""
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
    Application settings loaded from environment variables.
    
    Environment variables override defaults.
    Use .env file for local development.
    
    Example:
        ENVIRONMENT=production PORT=8000 python -m uvicorn API.main:app
    """

    # ========================================================================
    # API Configuration
    # ========================================================================
    
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Execution environment"
    )
    
    port: int = Field(default=8000, description="API port")
    host: str = Field(default="127.0.0.1", description="API host")
    log_level: str = Field(default="INFO", description="Logging level")
    
    app_name: str = Field(
        default="Genivra CNS Risk Engine API",
        description="Application name"
    )
    app_version: str = Field(default="1.0.0", description="Application version")
    
    # ========================================================================
    # API Key & Authentication Configuration
    # ========================================================================
    
    # Demo keys included by default, can be overridden
    api_keys_override: str = Field(
        default="",
        description="Override API keys (format: key1:tier2:name1,key2:tier1:name2)"
    )
    
    tier_1_monthly_limit: int = Field(
        default=100,
        description="Tier 1 monthly request limit"
    )
    
    tier_2_monthly_limit: int = Field(
        default=0,
        description="Tier 2 monthly request limit (0=unlimited)"
    )
    
    # ========================================================================
    # CORS Configuration
    # ========================================================================
    
    cors_allowed_origins: str = Field(
        default="*",
        description="Comma-separated list of allowed origins"
    )
    
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests"
    )
    
    # ========================================================================
    # Model Configuration
    # ========================================================================
    
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
    
    # ========================================================================
    # Security Configuration
    # ========================================================================
    
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
    
    # ========================================================================
    # Monitoring & Logging
    # ========================================================================
    
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
    
    # ========================================================================
    # Deployment Configuration
    # ========================================================================
    
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
        
        Returns:
            Dict mapping API key to {tier, name}
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
    """
    Print current settings to console (for debugging).
    Omits sensitive information.
    """
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
