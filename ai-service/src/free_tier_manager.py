"""
Free Tier Usage Manager

Keeps track of API usage to avoid exceeding free tier limits and generating bills.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class FreeTierManager:
    """
    Manages API usage to stay within free tier limits.
    
    Gemini Free Tier Limits (approximate):
    - gemini-1.5-flash: 15 requests/minute, 1,000 requests/day
    - gemini-embedding-001: 600 requests/minute
    """
    
    def __init__(self, usage_file: str = "./usage_tracker.json"):
        self.usage_file = Path(usage_file)
        self.usage_data = self._load_usage()
        
        # Free tier limits (conservative estimates)
        self.limits = {
            "gemini-2.5-flash": {
                "requests_per_minute": 15,
                "requests_per_day": 20,  # Actual free tier limit
                "tokens_per_day": 1000000
            },
            "gemini-1.5-flash": {
                "requests_per_minute": 15,
                "requests_per_day": 1000,  # Better free tier limit
                "tokens_per_day": 1000000
            },
            "gemini-embedding-001": {
                "requests_per_minute": 600,
                "requests_per_day": 10000
            }
        }
    
    def _load_usage(self) -> Dict[str, Any]:
        """Load usage data from file."""
        if self.usage_file.exists():
            try:
                with open(self.usage_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "daily": {},
            "minute": {},
            "last_reset": datetime.now().isoformat()
        }
    
    def _save_usage(self):
        """Save usage data to file."""
        try:
            with open(self.usage_file, 'w') as f:
                json.dump(self.usage_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save usage data: {e}")
    
    def _reset_if_needed(self):
        """Reset counters if time window has passed."""
        now = datetime.now()
        last_reset = datetime.fromisoformat(self.usage_data["last_reset"])
        
        # Reset daily counter if it's a new day
        if now.date() > last_reset.date():
            self.usage_data["daily"] = {}
            logger.info("Daily usage counter reset")
        
        # Reset minute counter if more than 1 minute has passed
        if now - last_reset > timedelta(minutes=1):
            self.usage_data["minute"] = {}
        
        self.usage_data["last_reset"] = now.isoformat()
    
    def can_make_request(self, model: str) -> tuple[bool, str]:
        """
        Check if a request can be made without exceeding limits.
        
        Returns:
            tuple: (can_make_request, reason_if_not)
        """
        self._reset_if_needed()
        
        if model not in self.limits:
            return False, f"Unknown model: {model}"
        
        limits = self.limits[model]
        
        # Check daily limit
        daily_count = self.usage_data["daily"].get(model, 0)
        if daily_count >= limits["requests_per_day"]:
            wait_time = 24 * 60 * 60  # 24 hours in seconds
            reset_time = datetime.now() + timedelta(seconds=wait_time)
            
            # Log detailed quota message
            logger.warning(f"=== DAILY QUOTA EXCEEDED ===")
            logger.warning(f"Model: {model}")
            logger.warning(f"Used: {daily_count}/{limits['requests_per_day']} requests")
            logger.warning(f"Reset time: {reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.warning(f"Wait time: {wait_time//3600}h {(wait_time%3600)//60}m")
            logger.warning(f"Recommendation: Use local demo or upgrade plan")
            logger.warning("==============================")
            
            return False, f"Daily limit reached ({limits['requests_per_day']}). Wait {wait_time//3600}h {(wait_time%3600)//60}m"
        
        # Check minute limit
        minute_count = self.usage_data["minute"].get(model, 0)
        if minute_count >= limits["requests_per_minute"]:
            wait_time = 60  # 1 minute in seconds
            reset_time = datetime.now() + timedelta(seconds=wait_time)
            
            # Log detailed minute limit message
            logger.warning(f"=== MINUTE QUOTA EXCEEDED ===")
            logger.warning(f"Model: {model}")
            logger.warning(f"Used: {minute_count}/{limits['requests_per_minute']} requests")
            logger.warning(f"Reset time: {reset_time.strftime('%H:%M:%S')}")
            logger.warning(f"Wait time: {wait_time} seconds")
            logger.warning("==============================")
            
            return False, f"Minute limit reached. Wait {wait_time} seconds"
        
        return True, "Request allowed"
    
    def record_request(self, model: str):
        """Record a successful API request."""
        self._reset_if_needed()
        
        self.usage_data["daily"][model] = self.usage_data["daily"].get(model, 0) + 1
        self.usage_data["minute"][model] = self.usage_data["minute"].get(model, 0) + 1
        
        self._save_usage()
        
        # Log detailed usage tracking
        daily_used = self.usage_data["daily"][model]
        daily_limit = self.limits[model]["requests_per_day"]
        minute_used = self.usage_data["minute"][model]
        minute_limit = self.limits[model]["requests_per_minute"]
        
        logger.info(f"=== USAGE TRACKED ===")
        logger.info(f"Model: {model}")
        logger.info(f"Daily: {daily_used}/{daily_limit} ({daily_used/daily_limit*100:.1f}%)")
        logger.info(f"Minute: {minute_used}/{minute_limit} ({minute_used/minute_limit*100:.1f}%)")
        logger.info(f"Daily remaining: {daily_limit - daily_used}")
        logger.info(f"Minute remaining: {minute_limit - minute_used}")
        logger.info("==================")
        
        # Warning when approaching limits
        if daily_used >= daily_limit * 0.8:  # 80% warning
            logger.warning(f"WARNING: Daily quota almost exhausted ({daily_used}/{daily_limit})")
        
        if minute_used >= minute_limit * 0.8:  # 80% warning
            logger.warning(f"WARNING: Minute quota almost exhausted ({minute_used}/{minute_limit})")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        self._reset_if_needed()
        
        stats = {
            "daily": {},
            "minute": {},
            "limits": self.limits
        }
        
        for model in self.limits:
            daily_count = self.usage_data["daily"].get(model, 0)
            minute_count = self.usage_data["minute"].get(model, 0)
            
            stats["daily"][model] = {
                "used": daily_count,
                "limit": self.limits[model]["requests_per_day"],
                "remaining": max(0, self.limits[model]["requests_per_day"] - daily_count)
            }
            
            stats["minute"][model] = {
                "used": minute_count,
                "limit": self.limits[model]["requests_per_minute"],
                "remaining": max(0, self.limits[model]["requests_per_minute"] - minute_count)
            }
        
        return stats
    
    def get_wait_time(self, model: str) -> int:
        """Get wait time in seconds before next request can be made."""
        can_make, reason = self.can_make_request(model)
        if can_make:
            return 0
        
        # Extract wait time from reason message
        if "Wait" in reason:
            try:
                parts = reason.split("Wait ")
                time_part = parts[1].split()[0]
                return int(time_part)
            except:
                pass
        
        return 60  # Default to 1 minute
