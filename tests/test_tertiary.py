"""
Test script for the Tertiary Chat Layer
=======================================
Tests proactive nudges and contextual assistance
"""

import asyncio
import json
from tertiary_chat import (
    detect_page_complexity,
    generate_proactive_nudge,
    generate_fallback_nudge
)

# Test HTML samples with different complexity levels
TEST_HTML_BEGINNER = """
<!DOCTYPE html>
<html>
<head><title>Introduction to HTML - Learn Web Development</title></head>
<body>
    <h1>Getting Started with HTML</h1>
    <p>Welcome to our beginner-friendly tutorial! HTML is the basic building block of websites.</p>
    <div class="tutorial">
        <h2>What is HTML?</h2>
        <p>HTML stands for HyperText Markup Language. Don't worry, it's easier than it sounds!</p>
    </div>
    <button class="next-tutorial">Continue Learning</button>
</body>
</html>
"""

TEST_HTML_ADVANCED = """
<!DOCTYPE html>
<html>
<head><title>Advanced React Patterns: Memoization and Performance Optimization</title></head>
<body>
    <h1>React Performance: Advanced Patterns</h1>
    <div class="documentation">
        <h2>Understanding useMemo and useCallback Hooks</h2>
        <p>Optimize your React components using memoization techniques to prevent unnecessary re-renders.</p>
        <pre><code>
const memoizedValue = useMemo(() => computeExpensiveValue(a, b), [a, b]);
const memoizedCallback = useCallback(() => { doSomething(a, b); }, [a, b]);
        </code></pre>
        <h2>Profiler API Internals</h2>
        <p>Deep dive into React's concurrent mode and fiber architecture...</p>
    </div>
</body>
</html>
"""

TEST_HTML_FORM = """
<!DOCTYPE html>
<html>
<head><title>Payment Form - Complete Your Purchase</title></head>
<body>
    <h1>Payment Information</h1>
    <form method="POST" action="/api/payment">
        <input type="text" name="card_number" placeholder="Card Number" />
        <input type="text" name="cvv" placeholder="CVV" />
        <input type="text" name="expiry" placeholder="MM/YY" />
        <button type="submit">Submit Payment</button>
    </form>
</body>
</html>
"""

TEST_HTML_EXPERT = """
<!DOCTYPE html>
<html>
<head><title>Kernel Development: Implementing a Custom Scheduler</title></head>
<body>
    <h1>Linux Kernel Internals</h1>
    <div class="api-documentation">
        <h2>CFS Scheduler Implementation Details</h2>
        <p>Analysis of the Completely Fair Scheduler algorithm and its time complexity optimizations.</p>
        <pre><code>
static void update_curr(struct cfs_rq *cfs_rq) {
    struct sched_entity *curr = cfs_rq->curr;
    u64 now = rq_clock_task(rq_of(cfs_rq));
    // Low-level implementation details...
}
        </code></pre>
    </div>
</body>
</html>
"""


async def test_complexity_detection():
    """Test page complexity detection"""
    print("\n" + "=" * 60)
    print("🔍 TEST 1: Page Complexity Detection")
    print("=" * 60)
    
    test_cases = [
        ("Beginner Tutorial", TEST_HTML_BEGINNER),
        ("Advanced React", TEST_HTML_ADVANCED),
        ("Payment Form", TEST_HTML_FORM),
        ("Kernel Documentation", TEST_HTML_EXPERT)
    ]
    
    for name, html in test_cases:
        print(f"\n📄 {name}:")
        result = detect_page_complexity(html)
        print(f"   Level: {result['complexity_level']}")
        print(f"   Score: {result['complexity_score']}")
        print(f"   Type: {result['page_type']}")
        print(f"   Concepts: {', '.join(result['detected_concepts']) or 'None'}")
        print(f"   Has Code: {result['has_code_examples']}")


async def test_nudge_generation():
    """Test nudge generation with different user profiles"""
    print("\n" + "=" * 60)
    print("💬 TEST 2: Proactive Nudge Generation")
    print("=" * 60)
    
    # Scenario 1: Beginner on Advanced Page (big gap)
    print("\n📊 Scenario 1: Beginner on Advanced React Page")
    print("-" * 60)
    user_profile = {
        "username": "Alice",
        "technical_level": "beginner",
        "personality_type": "visual"
    }
    
    nudge = await generate_proactive_nudge(
        html_summary=TEST_HTML_ADVANCED,
        user_profile=user_profile,
        page_url="https://example.com/advanced-react"
    )
    
    if nudge:
        print(f"✓ Generated nudge: {nudge}")
    else:
        print("ℹ️ No nudge needed")
    
    # Scenario 2: Expert on Beginner Tutorial (reverse gap)
    print("\n📊 Scenario 2: Expert on Beginner Tutorial")
    print("-" * 60)
    user_profile = {
        "username": "Bob",
        "technical_level": "expert",
        "personality_type": "analytical"
    }
    
    nudge = await generate_proactive_nudge(
        html_summary=TEST_HTML_BEGINNER,
        user_profile=user_profile,
        page_url="https://example.com/html-intro"
    )
    
    if nudge:
        print(f"✓ Generated nudge: {nudge}")
    else:
        print("ℹ️ No nudge needed")
    
    # Scenario 3: Beginner on Form Page
    print("\n📊 Scenario 3: Beginner on Payment Form")
    print("-" * 60)
    user_profile = {
        "username": "Charlie",
        "technical_level": "beginner",
        "personality_type": "cautious"
    }
    
    nudge = await generate_proactive_nudge(
        html_summary=TEST_HTML_FORM,
        user_profile=user_profile,
        page_url="https://example.com/payment"
    )
    
    if nudge:
        print(f"✓ Generated nudge: {nudge}")
    else:
        print("ℹ️ No nudge needed")
    
    # Scenario 4: Intermediate on Intermediate (no gap)
    print("\n📊 Scenario 4: Intermediate on Intermediate Content")
    print("-" * 60)
    user_profile = {
        "username": "Diana",
        "technical_level": "intermediate",
        "personality_type": "analytical"
    }
    
    nudge = await generate_proactive_nudge(
        html_summary=TEST_HTML_ADVANCED,  # Will be detected as advanced
        user_profile=user_profile,
        page_url="https://example.com/react"
    )
    
    if nudge:
        print(f"✓ Generated nudge: {nudge}")
    else:
        print("ℹ️ No nudge needed")


async def test_fallback_nudges():
    """Test fallback nudge templates"""
    print("\n" + "=" * 60)
    print("🔄 TEST 3: Fallback Nudge Templates")
    print("=" * 60)
    
    nudge_types = ["simplify", "encourage", "suggest_advanced", "skip_basics", "form_help"]
    
    for nudge_type in nudge_types:
        nudge = generate_fallback_nudge(
            user_level="beginner",
            page_level="advanced",
            nudge_type=nudge_type,
            username="TestUser"
        )
        print(f"\n{nudge_type}: {nudge}")


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 TERTIARY CHAT LAYER TEST SUITE")
    print("=" * 60)
    
    try:
        # Test 1: Complexity detection (fast, no API calls)
        await test_complexity_detection()
        
        # Test 2: Nudge generation (requires Gemini API, might hit quota)
        print("\n⚠️  Note: Nudge generation uses Gemini API and may fail if quota is exceeded")
        await test_nudge_generation()
        
        # Test 3: Fallback templates (fast, no API calls)
        await test_fallback_nudges()
        
        print("\n" + "=" * 60)
        print("✅ All tests complete!")
        print("=" * 60)
        
        print("\n📚 Integration Notes:")
        print("   • Tertiary chat is now integrated into main.py")
        print("   • Proactive nudges are sent automatically when /analyze is called")
        print("   • Users must be connected via WebSocket to receive nudges")
        print("   • Chat queries are handled via WebSocket 'query' messages")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
