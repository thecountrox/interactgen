#!/usr/bin/env python3
"""
Manual Test Script for User Endpoints
======================================
Run this script to manually test the user management endpoints.

Usage:
    python test_user_manual.py
"""

import requests
import uuid
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"


def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def test_onboard_user():
    """Test POST /user/onboard"""
    print_section("Test 1: Onboard New User")
    
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    
    payload = {
        "username": username,
        "personality_type": "analytical",
        "technical_level": "intermediate"
    }
    
    print(f"POST {BASE_URL}/user/onboard")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/user/onboard", json=payload)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        print("✅ User onboarded successfully!")
        return response.json()["id"]
    else:
        print("❌ Failed to onboard user")
        return None


def test_get_user_profile(user_id):
    """Test GET /user/{user_id}"""
    print_section("Test 2: Get User Profile")
    
    print(f"GET {BASE_URL}/user/{user_id}")
    
    response = requests.get(f"{BASE_URL}/user/{user_id}")
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✅ Profile retrieved successfully!")
        return True
    else:
        print("❌ Failed to retrieve profile")
        return False


def test_update_preferences(user_id):
    """Test PUT /user/{user_id}/preferences"""
    print_section("Test 3: Update User Preferences")
    
    payload = {
        "personality_type": "creative",
        "technical_level": "advanced"
    }
    
    print(f"PUT {BASE_URL}/user/{user_id}/preferences")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.put(f"{BASE_URL}/user/{user_id}/preferences", json=payload)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✅ Preferences updated successfully!")
        return True
    else:
        print("❌ Failed to update preferences")
        return False


def test_partial_update(user_id):
    """Test partial update (only one field)"""
    print_section("Test 4: Partial Preference Update")
    
    payload = {
        "technical_level": "expert"
    }
    
    print(f"PUT {BASE_URL}/user/{user_id}/preferences")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.put(f"{BASE_URL}/user/{user_id}/preferences", json=payload)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 200:
        print("✅ Partial update successful!")
        return True
    else:
        print("❌ Failed partial update")
        return False


def test_duplicate_username():
    """Test onboarding with duplicate username"""
    print_section("Test 5: Duplicate Username (Should Fail)")
    
    username = "duplicate_test_user"
    
    # Create first user
    payload = {
        "username": username,
        "personality_type": "analytical",
        "technical_level": "intermediate"
    }
    
    print(f"Creating first user with username: {username}")
    response1 = requests.post(f"{BASE_URL}/user/onboard", json=payload)
    print(f"Status Code: {response1.status_code}")
    
    if response1.status_code == 201:
        user_id = response1.json()["id"]
        
        # Try to create duplicate
        print(f"\nAttempting to create duplicate...")
        response2 = requests.post(f"{BASE_URL}/user/onboard", json=payload)
        
        print(f"Status Code: {response2.status_code}")
        print(f"Response: {json.dumps(response2.json(), indent=2)}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/user/{user_id}")
        
        if response2.status_code == 409:
            print("✅ Correctly rejected duplicate username!")
            return True
        else:
            print("❌ Should have rejected duplicate")
            return False
    else:
        print("❌ Failed to create first user")
        return False


def test_invalid_technical_level():
    """Test with invalid technical level"""
    print_section("Test 6: Invalid Technical Level (Should Fail)")
    
    payload = {
        "username": f"testuser_{uuid.uuid4().hex[:8]}",
        "personality_type": "analytical",
        "technical_level": "super_advanced"  # Invalid
    }
    
    print(f"POST {BASE_URL}/user/onboard")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    response = requests.post(f"{BASE_URL}/user/onboard", json=payload)
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 400:
        print("✅ Correctly rejected invalid technical level!")
        return True
    else:
        print("❌ Should have rejected invalid value")
        return False


def test_get_nonexistent_user():
    """Test getting a non-existent user"""
    print_section("Test 7: Get Non-Existent User (Should Fail)")
    
    fake_user_id = str(uuid.uuid4())
    
    print(f"GET {BASE_URL}/user/{fake_user_id}")
    
    response = requests.get(f"{BASE_URL}/user/{fake_user_id}")
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 404:
        print("✅ Correctly returned 404!")
        return True
    else:
        print("❌ Should have returned 404")
        return False


def test_delete_user(user_id):
    """Test DELETE /user/{user_id}"""
    print_section("Test 8: Delete User")
    
    print(f"DELETE {BASE_URL}/user/{user_id}")
    
    response = requests.delete(f"{BASE_URL}/user/{user_id}")
    
    print(f"\nStatus Code: {response.status_code}")
    
    if response.status_code == 204:
        print("✅ User deleted successfully!")
        
        # Verify deletion
        print("\nVerifying deletion...")
        verify_response = requests.get(f"{BASE_URL}/user/{user_id}")
        print(f"GET Status Code: {verify_response.status_code}")
        
        if verify_response.status_code == 404:
            print("✅ Verified: User no longer exists")
            return True
        else:
            print("❌ User still exists after deletion")
            return False
    else:
        print("❌ Failed to delete user")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  USER ENDPOINTS MANUAL TEST SUITE")
    print("  Make sure the FastAPI server is running on port 8000")
    print("=" * 60)
    
    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        print(f"\n✅ Server is running (status: {response.json()['status']})")
    except requests.exceptions.RequestException:
        print("\n❌ ERROR: Server is not running!")
        print("   Start it with: python main.py")
        return
    
    results = []
    user_id = None
    
    # Run tests
    try:
        # Test 1: Onboard user
        user_id = test_onboard_user()
        results.append(("Onboard User", user_id is not None))
        
        if user_id:
            # Test 2: Get profile
            results.append(("Get Profile", test_get_user_profile(user_id)))
            
            # Test 3: Update preferences
            results.append(("Update Preferences", test_update_preferences(user_id)))
            
            # Test 4: Partial update
            results.append(("Partial Update", test_partial_update(user_id)))
        
        # Test 5: Duplicate username
        results.append(("Duplicate Username", test_duplicate_username()))
        
        # Test 6: Invalid technical level
        results.append(("Invalid Tech Level", test_invalid_technical_level()))
        
        # Test 7: Non-existent user
        results.append(("Non-Existent User", test_get_nonexistent_user()))
        
        # Test 8: Delete user
        if user_id:
            results.append(("Delete User", test_delete_user(user_id)))
    
    except Exception as e:
        print(f"\n❌ Error during tests: {e}")
    
    # Print summary
    print_section("TEST SUMMARY")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")


if __name__ == "__main__":
    main()
