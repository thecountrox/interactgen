"""
Test script for the Judge Engine
================================
Tests the complete flow: HTML → RAG → LLM → Decisions
"""

import asyncio
import httpx
import json
from uuid import uuid4

# Test HTML samples
TEST_HTML_LOGIN = """
<!DOCTYPE html>
<html>
<head><title>Login - Example App</title></head>
<body>
    <div class="header">
        <h1>Welcome to Example App</h1>
        <nav class="navigation">
            <a href="/about">About</a>
            <a href="/features">Features</a>
            <a href="/pricing">Pricing</a>
        </nav>
    </div>
    
    <div class="main-content">
        <form id="login-form" method="POST">
            <h2>Sign In</h2>
            <input type="email" name="email" placeholder="Email" required />
            <input type="password" name="password" placeholder="Password" required />
            <button type="submit" class="primary-button">Log In</button>
            <a href="/forgot-password" class="help-text">Forgot password?</a>
        </form>
        
        <div class="advanced-settings">
            <h3>Advanced Options</h3>
            <label><input type="checkbox" /> Remember me for 30 days</label>
            <label><input type="checkbox" /> Enable 2FA</label>
            <details class="debug-panel">
                <summary>Debug Info</summary>
                <pre>API Version: 2.1.0</pre>
            </details>
        </div>
        
        <div class="tutorial">
            <h3>New to Example App?</h3>
            <p>Click here to learn how to create an account...</p>
            <button class="tutorial-button">Start Tutorial</button>
        </div>
    </div>
    
    <footer class="footer">
        <div class="ads">
            <div class="banner-ad">Advertisement</div>
        </div>
        <p>© 2025 Example App. All rights reserved.</p>
    </footer>
</body>
</html>
"""

TEST_HTML_DASHBOARD = """
<!DOCTYPE html>
<html>
<head><title>Dashboard - Example App</title></head>
<body>
    <h1>Your Dashboard</h1>
    <div class="stats">
        <div class="stat-card">Total Users: 1,234</div>
        <div class="stat-card">Revenue: $5,678</div>
    </div>
    <div class="actions">
        <button class="primary-button">Create New Project</button>
        <button class="secondary-button">View Reports</button>
    </div>
    <div class="api-documentation">
        <h2>API Endpoints</h2>
        <code>GET /api/users</code>
        <code>POST /api/projects</code>
    </div>
</body>
</html>
"""

BASE_URL = "http://localhost:8000"

async def test_analyze_endpoint():
    """Test the /analyze endpoint with sample HTML"""
    
    print("🧪 Testing Judge Engine via /analyze endpoint\n")
    print("=" * 60)
    
    # Test 1: Login page with beginner user
    print("\n📝 Test 1: Login Page (Beginner User)")
    print("-" * 60)
    
    test_user_id = str(uuid4())
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{BASE_URL}/analyze",
                json={
                    "url": "https://example.com/login",
                    "html_content": TEST_HTML_LOGIN,
                    "user_id": test_user_id,
                    "metadata": {
                        "viewport": "desktop",
                        "user_agent": "Mozilla/5.0"
                    }
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✓ Status: {result['success']}")
                print(f"✓ Message: {result['message']}")
                print(f"\n📊 Analysis Results:")
                print(f"   Summary: {result.get('suggestions', ['N/A'])[0]}")
                
                if result.get('suggestions'):
                    print(f"\n💡 Suggestions:")
                    for suggestion in result['suggestions']:
                        print(f"   • {suggestion}")
                
                if result.get('actions'):
                    print(f"\n⚡ Actions ({len(result['actions'])} total):")
                    for i, action in enumerate(result['actions'][:5], 1):  # Show first 5
                        action_type = action.get('type', 'unknown')
                        if action_type == 'hide':
                            print(f"   {i}. Hide: {action.get('selector', 'N/A')}")
                        elif action_type == 'highlight':
                            print(f"   {i}. Highlight: {action.get('selector', 'N/A')}")
                        elif action_type == 'suggestion':
                            print(f"   {i}. Suggest: {action.get('message', 'N/A')}")
                
                print(f"\n📄 Full Response:")
                print(json.dumps(result, indent=2))
            else:
                print(f"❌ Request failed with status {response.status_code}")
                print(response.text)
                
        except httpx.ConnectError:
            print("❌ Cannot connect to server. Is it running on http://localhost:8000?")
            print("   Start it with: uv run main.py")
            return
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Test complete!")


async def test_websocket():
    """Test WebSocket connection"""
    print("\n🔌 Testing WebSocket Connection\n")
    print("=" * 60)
    
    try:
        import websockets
        
        async with websockets.connect(f"ws://localhost:8000/chat/test-client") as ws:
            # Receive welcome message
            message = await ws.recv()
            print(f"📨 Received: {message}")
            
            # Send a query
            await ws.send(json.dumps({
                "type": "query",
                "message": "How do I use this page?"
            }))
            
            # Receive response
            response = await ws.recv()
            print(f"📨 Response: {response}")
            
            print("\n✓ WebSocket test successful!")
            
    except ImportError:
        print("⚠️ websockets package not installed")
        print("   Install with: uv pip install websockets")
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")


async def check_server_health():
    """Check if server is running and healthy"""
    print("🏥 Checking server health...\n")
    
    async with httpx.AsyncClient() as client:
        try:
            # Check root endpoint
            response = await client.get(f"{BASE_URL}/")
            if response.status_code == 200:
                data = response.json()
                print(f"✓ Server: {data['service']}")
                print(f"✓ Version: {data['version']}")
                print(f"✓ Status: {data['status']}")
            
            # Check health endpoint
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                health = response.json()
                print(f"✓ Supabase: {health['services']['supabase']}")
                print(f"✓ WebSocket Connections: {health['services']['websocket_connections']}")
            
            return True
            
        except httpx.ConnectError:
            print("❌ Server is not running")
            return False


async def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 JUDGE ENGINE TEST SUITE")
    print("=" * 60 + "\n")
    
    # Check if server is running
    if not await check_server_health():
        print("\n💡 Start the server with: uv run main.py")
        return
    
    print("\n")
    
    # Test the analyze endpoint
    await test_analyze_endpoint()
    
    # Test WebSocket (optional)
    # await test_websocket()
    
    print("\n" + "=" * 60)
    print("🎉 All tests complete!")
    print("=" * 60)
    print("\n📚 Next steps:")
    print("   • Visit http://localhost:8000/docs for API documentation")
    print("   • Run the SQL script in Supabase to set up the database")
    print("   • Create test user profiles in Supabase")
    print("   • Build the Chrome extension to connect to this backend")


if __name__ == "__main__":
    asyncio.run(main())
