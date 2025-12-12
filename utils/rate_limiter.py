"""
Rate Limiter for Gemini API
Ensures compliance with free tier limits when TRIAL_GEMINI_TOKEN=true
"""

import time
import asyncio
from datetime import datetime, timedelta
from collections import deque
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
TRIAL_MODE = os.getenv("TRIAL_GEMINI_TOKEN", "false").lower() == "true"

# Gemini Free Tier Limits (as of Dec 2024)
# https://ai.google.dev/pricing
FREE_TIER_LIMITS = {
    # Requests per minute
    "rpm": 15,  # 15 requests per minute
    # Requests per day
    "rpd": 1500,  # 1500 requests per day
    # Tokens per minute (for text models)
    "tpm": 32000,  # 32,000 tokens per minute
    # Minimum delay between requests (seconds)
    "min_delay": 4.0,  # 60s / 15 = 4 seconds between requests
}

class RateLimiter:
    """
    Token bucket rate limiter for Gemini API calls.
    Tracks both per-minute and per-day limits.
    """
    
    def __init__(self):
        self.enabled = TRIAL_MODE
        
        # Per-minute tracking
        self.minute_requests = deque()  # Timestamps of requests in last minute
        self.minute_limit = FREE_TIER_LIMITS["rpm"]
        
        # Per-day tracking
        self.day_requests = deque()  # Timestamps of requests in last day
        self.day_limit = FREE_TIER_LIMITS["rpd"]
        
        # Minimum delay between requests
        self.min_delay = FREE_TIER_LIMITS["min_delay"]
        self.last_request_time: Optional[float] = None
        
        print(f"🚦 Rate Limiter initialized (Trial Mode: {self.enabled})")
        if self.enabled:
            print(f"   • {self.minute_limit} requests per minute")
            print(f"   • {self.day_limit} requests per day")
            print(f"   • {self.min_delay}s minimum delay between requests")
    
    def _clean_old_requests(self):
        """Remove timestamps older than tracking windows."""
        now = time.time()
        
        # Clean minute window (keep last 60 seconds)
        minute_ago = now - 60
        while self.minute_requests and self.minute_requests[0] < minute_ago:
            self.minute_requests.popleft()
        
        # Clean day window (keep last 24 hours)
        day_ago = now - (24 * 60 * 60)
        while self.day_requests and self.day_requests[0] < day_ago:
            self.day_requests.popleft()
    
    def _get_wait_time(self) -> float:
        """
        Calculate how long to wait before next request.
        Returns 0 if request can proceed immediately.
        """
        if not self.enabled:
            return 0.0
        
        now = time.time()
        self._clean_old_requests()
        
        wait_times = []
        
        # Check minimum delay since last request
        if self.last_request_time:
            time_since_last = now - self.last_request_time
            if time_since_last < self.min_delay:
                wait_times.append(self.min_delay - time_since_last)
        
        # Check per-minute limit
        if len(self.minute_requests) >= self.minute_limit:
            # Wait until oldest request is 60 seconds old
            oldest = self.minute_requests[0]
            wait_until_minute = oldest + 60 - now
            if wait_until_minute > 0:
                wait_times.append(wait_until_minute)
        
        # Check per-day limit
        if len(self.day_requests) >= self.day_limit:
            # Wait until oldest request is 24 hours old
            oldest = self.day_requests[0]
            wait_until_day = oldest + (24 * 60 * 60) - now
            if wait_until_day > 0:
                wait_times.append(wait_until_day)
        
        return max(wait_times) if wait_times else 0.0
    
    async def acquire(self):
        """
        Acquire permission to make a request.
        Blocks until rate limits allow the request.
        """
        if not self.enabled:
            return  # No rate limiting if not in trial mode
        
        wait_time = self._get_wait_time()
        
        if wait_time > 0:
            # Log the wait
            if wait_time < 60:
                print(f"⏳ Rate limit: waiting {wait_time:.1f}s...")
            elif wait_time < 3600:
                print(f"⏳ Rate limit: waiting {wait_time/60:.1f} minutes...")
            else:
                print(f"⏳ Rate limit: waiting {wait_time/3600:.1f} hours (daily limit reached)...")
            
            await asyncio.sleep(wait_time)
        
        # Record the request
        now = time.time()
        self.minute_requests.append(now)
        self.day_requests.append(now)
        self.last_request_time = now
    
    def get_usage_stats(self) -> dict:
        """Get current usage statistics."""
        self._clean_old_requests()
        
        return {
            "trial_mode": self.enabled,
            "requests_last_minute": len(self.minute_requests),
            "minute_limit": self.minute_limit,
            "requests_last_day": len(self.day_requests),
            "day_limit": self.day_limit,
            "minute_remaining": self.minute_limit - len(self.minute_requests),
            "day_remaining": self.day_limit - len(self.day_requests),
        }
    
    def reset(self):
        """Reset all counters (for testing)."""
        self.minute_requests.clear()
        self.day_requests.clear()
        self.last_request_time = None
        print("🔄 Rate limiter reset")


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None

def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter

async def rate_limit():
    """
    Decorator/context manager for rate-limited API calls.
    Usage:
        await rate_limit()
        result = await some_api_call()
    """
    limiter = get_rate_limiter()
    await limiter.acquire()

def get_usage_stats() -> dict:
    """Get current rate limit usage statistics."""
    limiter = get_rate_limiter()
    return limiter.get_usage_stats()


if __name__ == "__main__":
    # Test the rate limiter
    async def test():
        limiter = RateLimiter()
        
        print("\n📊 Making 5 test requests...")
        for i in range(5):
            print(f"\n🔵 Request {i+1}")
            await limiter.acquire()
            print(f"✅ Request {i+1} allowed")
            
            stats = limiter.get_usage_stats()
            print(f"   Minute: {stats['requests_last_minute']}/{stats['minute_limit']}")
            print(f"   Day: {stats['requests_last_day']}/{stats['day_limit']}")
        
        print("\n✅ Test complete!")
    
    asyncio.run(test())
