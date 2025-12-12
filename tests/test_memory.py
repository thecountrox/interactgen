"""
Test script for the Memory Worker
==================================
Tests background memory processing and storage
"""

import asyncio
import httpx
import json
from uuid import uuid4

BASE_URL = "http://localhost:8000"

async def test_memory_creation():
    """Test creating test memories via API"""
    print("\n" + "=" * 60)
    print("🧪 TEST 1: Creating Test Memories")
    print("=" * 60)
    
    # Create a test user ID
    test_user_id = str(uuid4())
    print(f"\n📝 Test User ID: {test_user_id}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # First, create a user profile
            print("\n1. Creating user profile in Supabase...")
            print("   (Note: This would normally be done via Supabase directly)")
            
            # Create test memories
            scenarios = ["login", "form", "search", "purchase"]
            
            for scenario in scenarios:
                print(f"\n2. Creating '{scenario}' test memory...")
                
                response = await client.post(
                    f"{BASE_URL}/memories/create-test",
                    params={
                        "user_id": test_user_id,
                        "scenario": scenario
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✓ {result['message']}")
                else:
                    print(f"   ❌ Failed: {response.status_code}")
                    print(f"      {response.text}")
            
            return test_user_id
            
        except httpx.ConnectError:
            print("❌ Cannot connect to server. Is it running on http://localhost:8000?")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None


async def test_memory_retrieval(user_id: str):
    """Test retrieving memories for a user"""
    print("\n" + "=" * 60)
    print("🔍 TEST 2: Retrieving User Memories")
    print("=" * 60)
    
    if not user_id:
        print("⚠️ Skipping - no user ID provided")
        return
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print(f"\nFetching memories for user: {user_id}")
            
            response = await client.get(
                f"{BASE_URL}/memories/{user_id}",
                params={"limit": 10}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print(f"\n📊 Memory Statistics:")
                stats = result.get("stats", {})
                print(f"   Total memories: {stats.get('total_memories', 0)}")
                
                if stats.get('oldest_memory'):
                    print(f"   Oldest: {stats['oldest_memory']}")
                if stats.get('newest_memory'):
                    print(f"   Newest: {stats['newest_memory']}")
                
                if stats.get('actions'):
                    print(f"\n   Actions breakdown:")
                    for action, count in stats['actions'].items():
                        print(f"      {action}: {count}")
                
                print(f"\n📝 Recent Memories:")
                for i, memory in enumerate(result.get("recent_memories", [])[:5], 1):
                    content = memory.get("content", "N/A")
                    created = memory.get("created_at", "N/A")
                    print(f"   {i}. {content[:80]}...")
                    print(f"      Created: {created}")
                
            else:
                print(f"❌ Failed: {response.status_code}")
                print(f"   {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")


async def test_memory_search(user_id: str):
    """Test semantic search of memories"""
    print("\n" + "=" * 60)
    print("🔎 TEST 3: Semantic Memory Search")
    print("=" * 60)
    
    if not user_id:
        print("⚠️ Skipping - no user ID provided")
        return
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Test different search queries
            queries = [
                "login and authentication",
                "filling out forms",
                "shopping and purchases"
            ]
            
            for query in queries:
                print(f"\n🔍 Searching for: '{query}'")
                
                response = await client.post(
                    f"{BASE_URL}/memories/search",
                    params={
                        "user_id": user_id,
                        "query": query,
                        "top_k": 3
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result['count'] > 0:
                        print(f"   Found {result['count']} relevant memories:")
                        for i, memory in enumerate(result['results'], 1):
                            similarity = memory.get('similarity', 0)
                            content = memory.get('content', 'N/A')
                            print(f"   {i}. [{similarity:.2f}] {content[:60]}...")
                    else:
                        print(f"   No relevant memories found")
                else:
                    print(f"   ❌ Search failed: {response.status_code}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")


async def test_analyze_with_memory():
    """Test the /analyze endpoint which triggers background memory storage"""
    print("\n" + "=" * 60)
    print("📊 TEST 4: Page Analysis with Memory Storage")
    print("=" * 60)
    
    test_user_id = str(uuid4())
    
    test_html = """
    <!DOCTYPE html>
    <html>
    <head><title>Shopping Cart</title></head>
    <body>
        <h1>Your Cart</h1>
        <div class="cart-items">
            <div class="item">Product A - $29.99</div>
            <div class="item">Product B - $49.99</div>
        </div>
        <button class="checkout-button">Proceed to Checkout</button>
    </body>
    </html>
    """
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            print(f"\n📝 Analyzing shopping cart page...")
            print(f"   User ID: {test_user_id}")
            
            response = await client.post(
                f"{BASE_URL}/analyze",
                json={
                    "url": "https://example-shop.com/cart",
                    "html_content": test_html,
                    "user_id": test_user_id,
                    "metadata": {
                        "page_type": "shopping_cart",
                        "items_in_cart": 2
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✓ Analysis complete: {result['message']}")
                print(f"   ✓ Background task queued for memory storage")
                
                # Wait a bit for background task to complete
                print("\n   ⏳ Waiting for background memory processing...")
                await asyncio.sleep(3)
                
                # Check if memory was stored
                print("\n   🔍 Checking if memory was stored...")
                memory_response = await client.get(
                    f"{BASE_URL}/memories/{test_user_id}",
                    params={"limit": 1}
                )
                
                if memory_response.status_code == 200:
                    memory_result = memory_response.json()
                    total = memory_result.get("stats", {}).get("total_memories", 0)
                    
                    if total > 0:
                        print(f"   ✅ Memory stored successfully! ({total} total memories)")
                        recent = memory_result.get("recent_memories", [])
                        if recent:
                            print(f"   Latest: {recent[0].get('content', 'N/A')}")
                    else:
                        print(f"   ⚠️ No memories found (may have failed due to API quota)")
                
            else:
                print(f"   ❌ Analysis failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 MEMORY WORKER TEST SUITE")
    print("=" * 60)
    
    print("\n⚠️  Note: These tests require:")
    print("   1. Server running (uv run main.py)")
    print("   2. Supabase configured")
    print("   3. User profile created in Supabase")
    print("   4. Gemini API key (may hit quota limits)")
    
    try:
        # Test 1: Create test memories
        user_id = await test_memory_creation()
        
        if user_id:
            # Wait a bit for memories to be processed
            print("\n⏳ Waiting for background processing...")
            await asyncio.sleep(5)
            
            # Test 2: Retrieve memories
            await test_memory_retrieval(user_id)
            
            # Test 3: Search memories
            await test_memory_search(user_id)
        
        # Test 4: Analyze endpoint with memory storage
        await test_analyze_with_memory()
        
        print("\n" + "=" * 60)
        print("✅ All tests complete!")
        print("=" * 60)
        
        print("\n📚 Next steps:")
        print("   • Check server logs for detailed processing info")
        print("   • View stored memories in Supabase dashboard")
        print("   • Try searching memories with different queries")
        print("   • Test with real user profiles")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
