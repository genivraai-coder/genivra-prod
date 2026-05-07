"""
API Key Authentication Module
Handles API key validation, tier management, and usage tracking.
Modular design allows replacement with database backend.
"""

from datetime import datetime
from typing import Dict, Optional, Tuple
from enum import Enum
import threading
import os


class KeyTier(Enum):
    """API Key Tier Levels"""
    TIER_1 = "tier_1"      # Limited requests (100/month)
    TIER_2 = "tier_2"      # Unlimited requests


class APIKeyManager:
    """
    Manages API key validation, tier assignment, and usage tracking.
    """

    # =========================
    # ENV CONTROL (IMPORTANT FIX)
    # =========================
    ENV = os.getenv("ENV", "dev")

    # In-memory API Key Database
    API_KEYS: Dict[str, Dict] = {
        "demo_tier1_key_12345": {
            "tier": KeyTier.TIER_1,
            "name": "Demo Account - Tier 1",
            "org": "Genivra Demo",
            "created": "2026-02-01",
            "active": True
        },
        "demo_tier2_key_67890": {
            "tier": KeyTier.TIER_2,
            "name": "Demo Account - Tier 2 (Unlimited)",
            "org": "Genivra Premium",
            "created": "2026-02-01",
            "active": True
        },

        # ADD YOUR NGROK / NEW DEV KEY HERE
        "YOUR_NEW_NGROK_API_KEY": {
            "tier": KeyTier.TIER_2,
            "name": "Ngrok Dev Key",
            "org": "Genivra Dev",
            "created": "2026-05-06",
            "active": True
        }
    }

    # Rate limits
    TIER_LIMITS: Dict[KeyTier, Optional[int]] = {
        KeyTier.TIER_1: 100,
        KeyTier.TIER_2: None,
    }

    USAGE_TRACKER: Dict[str, Dict[str, int]] = {}
    _lock = threading.Lock()

    @staticmethod
    def get_current_month_year() -> str:
        return datetime.now().strftime("%Y-%m")

    @staticmethod
    def validate_key(api_key: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        VALIDATION LOGIC (FIXED FOR DEV MODE)
        """

        # =========================
        # DEV BYPASS (FIX FOR YOU)
        # =========================
        if APIKeyManager.ENV == "dev":
            return True, "dev", "Development Mode"

        if not api_key or not isinstance(api_key, str):
            return False, None, None

        if api_key not in APIKeyManager.API_KEYS:
            return False, None, None

        key_info = APIKeyManager.API_KEYS[api_key]

        if not key_info.get("active", False):
            return False, None, None

        tier = key_info.get("tier")
        name = key_info.get("name", "Unknown")

        return True, tier.value, name

    @staticmethod
    def check_rate_limit(api_key: str) -> Tuple[bool, str]:
        with APIKeyManager._lock:

            if APIKeyManager.ENV == "dev":
                return True, "dev mode (no rate limits)"

            if api_key not in APIKeyManager.API_KEYS:
                return False, "Invalid API key"

            key_info = APIKeyManager.API_KEYS[api_key]
            tier = key_info.get("tier")

            month_year = APIKeyManager.get_current_month_year()
            usage = APIKeyManager.USAGE_TRACKER.get(api_key, {}).get(month_year, 0)

            limit = APIKeyManager.TIER_LIMITS.get(tier)

            if limit is None:
                return True, "Unlimited requests"

            if usage >= limit:
                return False, f"Rate limit exceeded: {usage}/{limit}"

            return True, f"{usage}/{limit} used"

    @staticmethod
    def increment_usage(api_key: str) -> None:
        if APIKeyManager.ENV == "dev":
            return

        with APIKeyManager._lock:
            month_year = APIKeyManager.get_current_month_year()

            if api_key not in APIKeyManager.USAGE_TRACKER:
                APIKeyManager.USAGE_TRACKER[api_key] = {}

            APIKeyManager.USAGE_TRACKER[api_key][month_year] = \
                APIKeyManager.USAGE_TRACKER[api_key].get(month_year, 0) + 1

    @staticmethod
    def get_usage_stats(api_key: str) -> Dict:
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
        with APIKeyManager._lock:
            if api_key in APIKeyManager.API_KEYS:
                return False

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
        with APIKeyManager._lock:
            if api_key not in APIKeyManager.API_KEYS:
                return False

            APIKeyManager.API_KEYS[api_key]["active"] = False
            return True