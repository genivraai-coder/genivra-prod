"""
API Key Authentication Module
Handles API key validation, tier management, and usage tracking.
Modular design allows replacement with database backend.
"""

from datetime import datetime
from typing import Dict, Optional, Tuple
from enum import Enum
import threading


class KeyTier(Enum):
    """API Key Tier Levels"""
    TIER_1 = "tier_1"      # Limited requests (100/month)
    TIER_2 = "tier_2"      # Unlimited requests


class APIKeyManager:
    """
    Manages API key validation, tier assignment, and usage tracking.
    
    IMPORTANT: This is an in-memory implementation. For production:
    1. Replace API_KEYS dict with database queries (e.g., PostgreSQL)
    2. Replace USAGE_TRACKER with Redis or database
    3. Add persistence for monthly usage stats
    4. Consider adding webhook notifications for limits
    """
    
    # In-memory API Key Database
    # Format: {api_key: {"tier": KeyTier, "name": str, "org": str, "created": str, "active": bool}}
    API_KEYS: Dict[str, Dict] = {
        # Demo keys for testing
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
    }
    
    # Rate Limits per Tier (requests per month)
    TIER_LIMITS: Dict[KeyTier, Optional[int]] = {
        KeyTier.TIER_1: 100,      # 100 requests/month
        KeyTier.TIER_2: None,     # Unlimited
    }
    
    # In-memory Usage Tracker
    # Format: {api_key: {month_year: request_count}}
    # Example: {"demo_tier1_key_12345": {"2026-02": 45}}
    USAGE_TRACKER: Dict[str, Dict[str, int]] = {}
    
    # Thread lock for thread-safe operations
    _lock = threading.Lock()
    
    @staticmethod
    def get_current_month_year() -> str:
        """Get current month-year format for usage tracking (YYYY-MM)"""
        return datetime.now().strftime("%Y-%m")
    
    @staticmethod
    def validate_key(api_key: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate API key and return tier information.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            Tuple of (is_valid: bool, tier: str or None, name: str or None)
            
        Example:
            is_valid, tier, name = APIKeyManager.validate_key("demo_tier1_key_12345")
            # Returns: (True, "tier_1", "Demo Account - Tier 1")
        """
        if not api_key or not isinstance(api_key, str):
            return False, None, None
        
        # Check if key exists
        if api_key not in APIKeyManager.API_KEYS:
            return False, None, None
        
        key_info = APIKeyManager.API_KEYS[api_key]
        
        # Check if key is active
        if not key_info.get("active", False):
            return False, None, None
        
        tier = key_info.get("tier")
        name = key_info.get("name", "Unknown")
        
        return True, tier.value, name
    
    @staticmethod
    def check_rate_limit(api_key: str) -> Tuple[bool, str]:
        """
        Check if API key has remaining requests in current month.
        
        Args:
            api_key: The API key to check
            
        Returns:
            Tuple of (allowed: bool, message: str)
            
        Example:
            allowed, msg = APIKeyManager.check_rate_limit("demo_tier1_key_12345")
            # Returns: (True, "45/100 requests used this month")
        """
        with APIKeyManager._lock:
            if api_key not in APIKeyManager.API_KEYS:
                return False, "Invalid API key"
            
            key_info = APIKeyManager.API_KEYS[api_key]
            tier = key_info.get("tier")
            
            # Get current month's request count
            month_year = APIKeyManager.get_current_month_year()
            usage = APIKeyManager.USAGE_TRACKER.get(api_key, {}).get(month_year, 0)
            
            # Check tier limit
            limit = APIKeyManager.TIER_LIMITS.get(tier)
            
            if limit is None:
                # Unlimited tier
                return True, f"Unlimited requests"
            
            if usage >= limit:
                return False, f"Rate limit exceeded: {usage}/{limit} requests used this month"
            
            remaining = limit - usage
            return True, f"{usage}/{limit} requests used this month ({remaining} remaining)"
    
    @staticmethod
    def increment_usage(api_key: str) -> None:
        """
        Increment request counter for API key in current month.
        
        Args:
            api_key: The API key to track
            
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
    def get_usage_stats(api_key: str) -> Dict:
        """
        Get usage statistics for an API key.
        
        Args:
            api_key: The API key to check
            
        Returns:
            Dict with usage information
            
        Example:
            stats = APIKeyManager.get_usage_stats("demo_tier1_key_12345")
            # Returns: {
            #     "api_key": "demo_tier1_key_12345",
            #     "tier": "tier_1",
            #     "current_month": "2026-02",
            #     "current_usage": 45,
            #     "limit": 100,
            #     "remaining": 55
            # }
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
            
        Example:
            success = APIKeyManager.add_api_key(
                "custom_key_xyz",
                KeyTier.TIER_2,
                "Customer ABC",
                "ABC Corp"
            )
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
        
        Args:
            api_key: The API key to deactivate
            
        Returns:
            True if deactivated, False if key not found
        """
        with APIKeyManager._lock:
            if api_key not in APIKeyManager.API_KEYS:
                return False
            
            APIKeyManager.API_KEYS[api_key]["active"] = False
            return True
    
    @staticmethod
    def list_all_keys() -> list:
        """
        List all API keys with their info (admin operation).
        
        Returns:
            List of API key info dicts
        """
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
        """
        Reset monthly usage (call this at month end).
        In production, would be scheduled job or database cleanup.
        """
        with APIKeyManager._lock:
            # Clear current month's usage
            month_year = APIKeyManager.get_current_month_year()
            for key in APIKeyManager.USAGE_TRACKER:
                if month_year in APIKeyManager.USAGE_TRACKER[key]:
                    del APIKeyManager.USAGE_TRACKER[key][month_year]


# ========== FUTURE: DATABASE BACKEND TEMPLATE ==========
"""
For production with database:

class APIKeyManagerDB:
    \"\"\"Database-backed API Key Manager (future implementation)\"\"\"
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def validate_key(self, api_key: str) -> Tuple[bool, Optional[str], Optional[str]]:
        # Query: SELECT tier, name FROM api_keys WHERE key = ? AND active = True
        # Return (is_valid, tier, name)
        pass
    
    def check_rate_limit(self, api_key: str) -> Tuple[bool, str]:
        # Query: SELECT tier FROM api_keys WHERE key = ?
        # Query: SELECT COUNT(*) FROM usage_log WHERE key = ? AND month = ?
        # Check limit from TIER_LIMITS
        pass
    
    def increment_usage(self, api_key: str) -> None:
        # INSERT INTO usage_log (key, month, count) VALUES (?, ?, 1)
        # ON DUPLICATE UPDATE count = count + 1
        pass

# In main.py, swap:
# from API.auth import APIKeyManager
# with:
# from API.auth import APIKeyManagerDB
# and init: key_manager = APIKeyManagerDB(get_db())
"""
