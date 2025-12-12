"""
Test Supabase Profile Creation and Memory Storage
==================================================
Tests the profile creation flow and memory insertion with proper error handling.
"""

import asyncio
import os
from uuid import uuid4
from supabase import create_client, Client
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the embedding function
USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"
if USE_LOCAL_LLM:
    from ollama_api import generate_embedding
    print("🏠 Using LOCAL LLM (Ollama) for embeddings")
else:
    from gemini_api import generate_embedding
    print("☁️  Using CLOUD LLM (Gemini) for embeddings")


def get_supabase_client() -> Client:
    """Get Supabase client"""
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
    
    return create_client(url, key)


async def test_profile_creation():
    """Test creating a new user profile"""
    print("\n" + "=" * 70)
    print("🧪 TEST 1: Profile Creation")
    print("=" * 70)
    
    supabase = get_supabase_client()
    test_user_id = str(uuid4())
    
    print(f"\n📝 Test User ID: {test_user_id}")
    
    try:
        # Step 1: Check if profile exists (should not)
        print("\n1. Checking if profile exists...")
        profile_check = supabase.table("profiles").select("*").eq("id", test_user_id).execute()
        print(f"   Query result: {profile_check}")
        print(f"   Data: {profile_check.data}")
        print(f"   Data is empty: {not profile_check.data}")
        
        if profile_check.data:
            print("   ⚠️  Profile already exists (unexpected)")
            return None
        else:
            print("   ✓ No existing profile found")
        
        # Step 2: Create new profile
        print("\n2. Creating new profile...")
        profile_data = {
            "id": test_user_id,
            "username": f"test_user_{test_user_id[:8]}",
            "technical_level": "intermediate",
            "personality_type": "analytical"
        }
        print(f"   Profile data: {profile_data}")
        
        new_profile = supabase.table("profiles").insert(profile_data).execute()
        
        print(f"   Insert result: {new_profile}")
        print(f"   Insert data: {new_profile.data}")
        print(f"   Insert data type: {type(new_profile.data)}")
        print(f"   Insert data length: {len(new_profile.data) if new_profile.data else 0}")
        
        if new_profile.data:
            print(f"   ✅ Profile created successfully!")
            print(f"   Created profile: {new_profile.data[0]}")
            return test_user_id
        else:
            print(f"   ❌ Profile creation returned no data")
            print(f"   Full response: {new_profile}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print(f"   Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return None


async def test_memory_insertion(user_id: str):
    """Test inserting a memory for a user"""
    print("\n" + "=" * 70)
    print("🧪 TEST 2: Memory Insertion")
    print("=" * 70)
    
    if not user_id:
        print("⚠️  Skipping - no user ID provided")
        return False
    
    supabase = get_supabase_client()
    
    try:
        # Step 1: Generate embedding
        print("\n1. Generating embedding...")
        test_content = "User successfully logged into the application"
        print(f"   Content: {test_content}")
        
        embedding = await generate_embedding(test_content)
        
        if not embedding:
            print(f"   ❌ Failed to generate embedding")
            return False
        
        print(f"   ✓ Generated {len(embedding)}-dimensional embedding")
        print(f"   First 5 values: {embedding[:5]}")
        
        # Step 2: Check if profile exists
        print("\n2. Verifying profile exists...")
        profile_check = supabase.table("profiles").select("*").eq("id", user_id).execute()
        
        if not profile_check.data:
            print(f"   ❌ Profile does not exist for user {user_id}")
            return False
        
        print(f"   ✓ Profile exists: {profile_check.data[0].get('username', 'N/A')}")
        
        # Step 3: Insert memory
        print("\n3. Inserting memory...")
        memory_data = {
            "user_id": user_id,
            "content": test_content,
            "embedding": embedding,
            "metadata": {"action": "login", "url": "https://example.com/login"},
            "created_at": datetime.utcnow().isoformat()
        }
        print(f"   Memory data keys: {list(memory_data.keys())}")
        print(f"   User ID: {memory_data['user_id']}")
        print(f"   Content: {memory_data['content']}")
        print(f"   Metadata: {memory_data['metadata']}")
        print(f"   Embedding length: {len(memory_data['embedding'])}")
        
        result = supabase.table("memories").insert(memory_data).execute()
        
        print(f"   Insert result: {result}")
        print(f"   Insert data: {result.data}")
        print(f"   Insert data type: {type(result.data)}")
        
        if result.data:
            memory_id = result.data[0].get('id', 'unknown')
            print(f"   ✅ Memory stored successfully!")
            print(f"   Memory ID: {memory_id}")
            return True
        else:
            print(f"   ❌ Memory insertion returned no data")
            print(f"   Full response: {result}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        print(f"   Error type: {type(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_memory_retrieval(user_id: str):
    """Test retrieving memories for a user"""
    print("\n" + "=" * 70)
    print("🧪 TEST 3: Memory Retrieval")
    print("=" * 70)
    
    if not user_id:
        print("⚠️  Skipping - no user ID provided")
        return
    
    supabase = get_supabase_client()
    
    try:
        print(f"\n1. Fetching memories for user {user_id}...")
        
        result = supabase.table("memories").select("*").eq("user_id", user_id).execute()
        
        print(f"   Query result: {result}")
        print(f"   Data: {result.data}")
        print(f"   Count: {len(result.data) if result.data else 0}")
        
        if result.data:
            print(f"   ✅ Found {len(result.data)} memories")
            for i, memory in enumerate(result.data, 1):
                print(f"\n   Memory {i}:")
                print(f"      ID: {memory.get('id', 'N/A')}")
                print(f"      Content: {memory.get('content', 'N/A')[:80]}...")
                print(f"      Created: {memory.get('created_at', 'N/A')}")
                print(f"      Metadata: {memory.get('metadata', {})}")
        else:
            print(f"   ⚠️  No memories found")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()


async def test_foreign_key_constraint():
    """Test if foreign key constraint is enforced"""
    print("\n" + "=" * 70)
    print("🧪 TEST 4: Foreign Key Constraint")
    print("=" * 70)
    
    supabase = get_supabase_client()
    fake_user_id = str(uuid4())
    
    print(f"\n📝 Testing with non-existent user ID: {fake_user_id}")
    
    try:
        # Try to insert a memory without a profile
        print("\n1. Attempting to insert memory without profile...")
        
        test_content = "This should fail due to foreign key constraint"
        embedding = await generate_embedding(test_content)
        
        memory_data = {
            "user_id": fake_user_id,  # This user doesn't exist
            "content": test_content,
            "embedding": embedding,
            "metadata": {},
            "created_at": datetime.utcnow().isoformat()
        }
        
        result = supabase.table("memories").insert(memory_data).execute()
        
        if result.data:
            print(f"   ⚠️  Memory inserted despite missing profile!")
            print(f"   This suggests foreign key constraint is NOT enforced")
        else:
            print(f"   ✓ Memory insertion blocked (no data returned)")
            
    except Exception as e:
        print(f"   ✅ Memory insertion failed as expected!")
        print(f"   Error: {e}")
        print(f"   This confirms foreign key constraint is enforced")


async def cleanup_test_data(user_id: str):
    """Clean up test data"""
    print("\n" + "=" * 70)
    print("🧹 CLEANUP")
    print("=" * 70)
    
    if not user_id:
        print("⚠️  No user ID to clean up")
        return
    
    supabase = get_supabase_client()
    
    try:
        # Delete memories first (foreign key)
        print(f"\n1. Deleting memories for user {user_id}...")
        mem_result = supabase.table("memories").delete().eq("user_id", user_id).execute()
        print(f"   ✓ Deleted {len(mem_result.data) if mem_result.data else 0} memories")
        
        # Delete profile
        print(f"\n2. Deleting profile for user {user_id}...")
        prof_result = supabase.table("profiles").delete().eq("id", user_id).execute()
        print(f"   ✓ Deleted profile")
        
        print(f"\n✅ Cleanup complete!")
        
    except Exception as e:
        print(f"   ⚠️  Cleanup error: {e}")


async def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("🧪 SUPABASE PROFILE & MEMORY TEST SUITE")
    print("=" * 70)
    
    print("\n📋 This test suite will:")
    print("   1. Create a test user profile")
    print("   2. Insert a memory for that user")
    print("   3. Retrieve and verify the memory")
    print("   4. Test foreign key constraints")
    print("   5. Clean up test data")
    
    user_id = None
    
    try:
        # Test 1: Profile creation
        user_id = await test_profile_creation()
        
        if user_id:
            # Test 2: Memory insertion
            success = await test_memory_insertion(user_id)
            
            if success:
                # Test 3: Memory retrieval
                await test_memory_retrieval(user_id)
        
        # Test 4: Foreign key constraint
        await test_foreign_key_constraint()
        
        print("\n" + "=" * 70)
        print("✅ All tests complete!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if user_id:
            await cleanup_test_data(user_id)


if __name__ == "__main__":
    asyncio.run(main())
