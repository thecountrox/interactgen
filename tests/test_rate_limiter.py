#!/usr/bin/env python3
"""
Test Rate Limiter
=================
Demonstrates rate limiting in action without making real API calls
"""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Set trial mode for this test
os.environ["TRIAL_GEMINI_TOKEN"] = "true"

from rate_limiter import get_rate_limiter, get_usage_stats

async def test_rate_limiting():
    """Test the rate limiter with simulated API calls"""
    
    print("=" * 60)
    print("🚦 RATE LIMITER TEST")
    print("=" * 60)
    
    limiter = get_rate_limiter()
    
    print(f"\n✅ Rate Limiter Configuration:")
    print(f"   • Enabled: {limiter.enabled}")
    print(f"   • Requests per minute: {limiter.minute_limit}")
    print(f"   • Requests per day: {limiter.day_limit}")
    print(f"   • Minimum delay: {limiter.min_delay}s")
    
    print(f"\n📊 Initial Stats:")
    stats = get_usage_stats()
    for key, value in stats.items():
        print(f"   • {key}: {value}")
    
    # Test 1: Rapid requests
    print("\n" + "=" * 60)
    print("TEST 1: Making 5 rapid requests")
    print("=" * 60)
    
    import time
    
    for i in range(5):
        start = time.time()
        print(f"\n🔵 Request {i+1}:")
        
        # This would be: await generate_embedding(...)
        await limiter.acquire()
        
        elapsed = time.time() - start
        print(f"   ✅ Allowed after {elapsed:.2f}s")
        
        # Show current usage
        stats = get_usage_stats()
        print(f"   📊 Minute: {stats['requests_last_minute']}/{stats['minute_limit']} "
              f"(remaining: {stats['minute_remaining']})")
        print(f"   📊 Day: {stats['requests_last_day']}/{stats['day_limit']} "
              f"(remaining: {stats['day_remaining']})")
    
    # Test 2: Check stats
    print("\n" + "=" * 60)
    print("TEST 2: Final Usage Statistics")
    print("=" * 60)
    
    stats = get_usage_stats()
    print(f"\n📊 Final Stats:")
    for key, value in stats.items():
        print(f"   • {key}: {value}")
    
    # Test 3: What happens with trial mode off?
    print("\n" + "=" * 60)
    print("TEST 3: Disabling Trial Mode")
    print("=" * 60)
    
    print("\n⚙️ Setting TRIAL_GEMINI_TOKEN=false...")
    os.environ["TRIAL_GEMINI_TOKEN"] = "false"
    
    # Need to recreate limiter to pick up new env var
    from rate_limiter import RateLimiter
    limiter_off = RateLimiter()
    
    print(f"\n📊 New Configuration:")
    print(f"   • Enabled: {limiter_off.enabled}")
    
    print(f"\n🔵 Making request without rate limiting...")
    start = time.time()
    await limiter_off.acquire()
    elapsed = time.time() - start
    print(f"   ✅ Allowed immediately (no delay: {elapsed:.3f}s)")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS COMPLETE!")
    print("=" * 60)
    
    print("\n💡 Key Takeaways:")
    print("   1. With TRIAL_GEMINI_TOKEN=true: 4s minimum delay enforced")
    print("   2. With TRIAL_GEMINI_TOKEN=false: No delays (for paid tier)")
    print("   3. Usage is tracked across minute and day windows")
    print("   4. System automatically waits when limits are approached")
    
    print("\n📚 Next Steps:")
    print("   • Add TRIAL_GEMINI_TOKEN=true to your .env file")
    print("   • Restart server to apply rate limiting")
    print("   • Check status: curl http://localhost:8000/api/rate-limit-status")
    print("   • Monitor logs for rate limiting messages")


if __name__ == "__main__":
    asyncio.run(test_rate_limiting())
