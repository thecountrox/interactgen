"""
Tests for User Management Endpoints
====================================
Tests the /user endpoints including onboarding, profile retrieval,
preference updates, and user deletion.
"""

import pytest
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

# Test Configuration
BASE_URL = "http://localhost:8000"

# Skip tests if Supabase is not configured
SUPABASE_CONFIGURED = bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"))

pytestmark = pytest.mark.skipif(
    not SUPABASE_CONFIGURED,
    reason="Supabase not configured (set SUPABASE_URL and SUPABASE_KEY)"
)


class TestUserEndpoints:
    """Test suite for user management endpoints"""

    @pytest.fixture
    def test_username(self):
        """Generate a unique test username"""
        return f"testuser_{uuid.uuid4().hex[:8]}"

    @pytest.fixture
    async def created_user_id(self, test_username):
        """Create a test user and return their ID for cleanup"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/user/onboard",
                json={
                    "username": test_username,
                    "personality_type": "analytical",
                    "technical_level": "intermediate"
                }
            )
            
            if response.status_code == 201:
                data = response.json()
                user_id = data["id"]
                
                # Yield user ID for tests
                yield user_id
                
                # Cleanup: Delete user after test
                try:
                    await client.delete(f"{BASE_URL}/user/{user_id}")
                except:
                    pass
            else:
                yield None

    @pytest.mark.asyncio
    async def test_onboard_user_success(self, test_username):
        """Test successful user onboarding"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/user/onboard",
                json={
                    "username": test_username,
                    "personality_type": "creative",
                    "technical_level": "advanced"
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            
            # Verify response structure
            assert "id" in data
            assert data["username"] == test_username
            assert data["personality_type"] == "creative"
            assert data["technical_level"] == "advanced"
            assert "created_at" in data
            assert "updated_at" in data
            
            # Cleanup
            user_id = data["id"]
            await client.delete(f"{BASE_URL}/user/{user_id}")

    @pytest.mark.asyncio
    async def test_onboard_user_duplicate_username(self, created_user_id, test_username):
        """Test onboarding with duplicate username"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            # Try to create another user with the same username
            response = await client.post(
                f"{BASE_URL}/user/onboard",
                json={
                    "username": test_username,
                    "personality_type": "analytical",
                    "technical_level": "beginner"
                }
            )
            
            assert response.status_code == 409  # Conflict
            assert "already taken" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_onboard_user_invalid_technical_level(self, test_username):
        """Test onboarding with invalid technical level"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/user/onboard",
                json={
                    "username": test_username,
                    "personality_type": "analytical",
                    "technical_level": "invalid_level"
                }
            )
            
            assert response.status_code == 400
            assert "invalid technical_level" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_user_profile(self, created_user_id):
        """Test retrieving user profile"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/user/{created_user_id}")
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["id"] == created_user_id
            assert "username" in data
            assert "technical_level" in data
            assert "created_at" in data
            assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_get_user_profile_not_found(self):
        """Test retrieving non-existent user profile"""
        import httpx
        
        fake_user_id = str(uuid.uuid4())
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/user/{fake_user_id}")
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_update_user_preferences(self, created_user_id):
        """Test updating user preferences"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{BASE_URL}/user/{created_user_id}/preferences",
                json={
                    "personality_type": "pragmatic",
                    "technical_level": "expert"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["id"] == created_user_id
            assert data["personality_type"] == "pragmatic"
            assert data["technical_level"] == "expert"

    @pytest.mark.asyncio
    async def test_update_user_preferences_partial(self, created_user_id):
        """Test partial update of user preferences"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            # Update only technical level
            response = await client.put(
                f"{BASE_URL}/user/{created_user_id}/preferences",
                json={
                    "technical_level": "beginner"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["technical_level"] == "beginner"
            # Personality type should remain unchanged

    @pytest.mark.asyncio
    async def test_update_user_preferences_not_found(self):
        """Test updating preferences for non-existent user"""
        import httpx
        
        fake_user_id = str(uuid.uuid4())
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{BASE_URL}/user/{fake_user_id}/preferences",
                json={
                    "technical_level": "advanced"
                }
            )
            
            assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_user_preferences_invalid_level(self, created_user_id):
        """Test updating with invalid technical level"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{BASE_URL}/user/{created_user_id}/preferences",
                json={
                    "technical_level": "super_expert"
                }
            )
            
            assert response.status_code == 400
            assert "invalid technical_level" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_delete_user(self, test_username):
        """Test deleting a user"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            # First create a user
            create_response = await client.post(
                f"{BASE_URL}/user/onboard",
                json={
                    "username": test_username,
                    "personality_type": "analytical",
                    "technical_level": "intermediate"
                }
            )
            
            assert create_response.status_code == 201
            user_id = create_response.json()["id"]
            
            # Delete the user
            delete_response = await client.delete(f"{BASE_URL}/user/{user_id}")
            assert delete_response.status_code == 204
            
            # Verify user is deleted
            get_response = await client.get(f"{BASE_URL}/user/{user_id}")
            assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_user_not_found(self):
        """Test deleting non-existent user"""
        import httpx
        
        fake_user_id = str(uuid.uuid4())
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{BASE_URL}/user/{fake_user_id}")
            
            assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
