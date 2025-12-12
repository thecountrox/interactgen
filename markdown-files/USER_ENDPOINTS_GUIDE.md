# User Management Endpoints

This document describes the user management endpoints for the InteractGen Browser Automation Agent.

## Overview

The user management endpoints provide functionality for:
- **Onboarding** new users with profiles
- **Retrieving** user profile information
- **Updating** user preferences and settings
- **Deleting** user accounts

All user data is stored in Supabase with proper validation and error handling.

---

## Endpoints

### 1. Onboard User

**POST** `/user/onboard`

Create a new user profile with username and preferences.

#### Request Body

```json
{
  "username": "johndoe",
  "personality_type": "analytical",
  "technical_level": "intermediate"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `username` | string | Yes | Username (3-50 characters, must be unique) |
| `personality_type` | string | No | User personality type: `analytical`, `creative`, `pragmatic`, `social` (default: `analytical`) |
| `technical_level` | string | No | Technical proficiency: `beginner`, `intermediate`, `advanced`, `expert` (default: `intermediate`) |

#### Response

**Status Code:** `201 Created`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "johndoe",
  "personality_type": "analytical",
  "technical_level": "intermediate",
  "created_at": "2025-12-12T10:30:00Z",
  "updated_at": "2025-12-12T10:30:00Z"
}
```

#### Error Responses

| Status Code | Description |
|-------------|-------------|
| `400 Bad Request` | Invalid `technical_level` value |
| `409 Conflict` | Username already exists |
| `500 Internal Server Error` | Database or server error |

#### Example (cURL)

```bash
curl -X POST http://localhost:8000/user/onboard \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "personality_type": "creative",
    "technical_level": "advanced"
  }'
```

#### Example (Python)

```python
import requests

response = requests.post(
    "http://localhost:8000/user/onboard",
    json={
        "username": "johndoe",
        "personality_type": "analytical",
        "technical_level": "intermediate"
    }
)

if response.status_code == 201:
    user = response.json()
    print(f"User created with ID: {user['id']}")
```

#### Example (JavaScript)

```javascript
const response = await fetch('http://localhost:8000/user/onboard', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    username: 'johndoe',
    personality_type: 'analytical',
    technical_level: 'intermediate'
  })
});

const user = await response.json();
console.log(`User created with ID: ${user.id}`);
```

---

### 2. Get User Profile

**GET** `/user/{user_id}`

Retrieve complete user profile information by user ID.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | UUID | The unique user identifier |

#### Response

**Status Code:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "johndoe",
  "personality_type": "analytical",
  "technical_level": "intermediate",
  "created_at": "2025-12-12T10:30:00Z",
  "updated_at": "2025-12-12T10:30:00Z"
}
```

#### Error Responses

| Status Code | Description |
|-------------|-------------|
| `404 Not Found` | User profile not found |
| `500 Internal Server Error` | Database or server error |

#### Example (cURL)

```bash
curl -X GET http://localhost:8000/user/550e8400-e29b-41d4-a716-446655440000
```

#### Example (Python)

```python
import requests

user_id = "550e8400-e29b-41d4-a716-446655440000"
response = requests.get(f"http://localhost:8000/user/{user_id}")

if response.status_code == 200:
    user = response.json()
    print(f"Username: {user['username']}")
    print(f"Technical Level: {user['technical_level']}")
```

---

### 3. Update User Preferences

**PUT** `/user/{user_id}/preferences`

Update user preferences and profile settings. Supports partial updates (only provide fields you want to update).

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | UUID | The unique user identifier |

#### Request Body

```json
{
  "personality_type": "creative",
  "technical_level": "advanced"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `personality_type` | string | No | User personality type: `analytical`, `creative`, `pragmatic`, `social` |
| `technical_level` | string | No | Technical proficiency: `beginner`, `intermediate`, `advanced`, `expert` |

**Note:** You can provide one or both fields. Only provided fields will be updated.

#### Response

**Status Code:** `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "johndoe",
  "personality_type": "creative",
  "technical_level": "advanced",
  "created_at": "2025-12-12T10:30:00Z",
  "updated_at": "2025-12-12T10:35:00Z"
}
```

#### Error Responses

| Status Code | Description |
|-------------|-------------|
| `400 Bad Request` | Invalid `technical_level` value or no fields provided |
| `404 Not Found` | User profile not found |
| `500 Internal Server Error` | Database or server error |

#### Example (cURL)

```bash
curl -X PUT http://localhost:8000/user/550e8400-e29b-41d4-a716-446655440000/preferences \
  -H "Content-Type: application/json" \
  -d '{
    "technical_level": "expert"
  }'
```

#### Example (Python)

```python
import requests

user_id = "550e8400-e29b-41d4-a716-446655440000"
response = requests.put(
    f"http://localhost:8000/user/{user_id}/preferences",
    json={
        "technical_level": "expert",
        "personality_type": "pragmatic"
    }
)

if response.status_code == 200:
    user = response.json()
    print(f"Updated technical level to: {user['technical_level']}")
```

---

### 4. Delete User

**DELETE** `/user/{user_id}`

Delete a user profile and all associated data. This action cascades to delete all user memories.

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `user_id` | UUID | The unique user identifier |

#### Response

**Status Code:** `204 No Content`

No response body is returned on success.

#### Error Responses

| Status Code | Description |
|-------------|-------------|
| `404 Not Found` | User profile not found |
| `500 Internal Server Error` | Database or server error |

#### Example (cURL)

```bash
curl -X DELETE http://localhost:8000/user/550e8400-e29b-41d4-a716-446655440000
```

#### Example (Python)

```python
import requests

user_id = "550e8400-e29b-41d4-a716-446655440000"
response = requests.delete(f"http://localhost:8000/user/{user_id}")

if response.status_code == 204:
    print("User deleted successfully")
```

---

## Data Models

### UserProfile

```typescript
{
  id: string (UUID),
  username: string,
  personality_type: string | null,
  technical_level: string,
  created_at: string (ISO 8601 datetime),
  updated_at: string (ISO 8601 datetime)
}
```

### Valid Values

#### Personality Types
- `analytical` - Logical, data-driven, methodical
- `creative` - Innovative, exploratory, experimental
- `pragmatic` - Practical, goal-oriented, efficient
- `social` - Collaborative, communicative, team-focused

#### Technical Levels
- `beginner` - New to web development/automation
- `intermediate` - Some experience with web technologies
- `advanced` - Experienced developer
- `expert` - Professional/senior developer

---

## Integration with Browser Extension

### Onboarding Flow

```javascript
// In browser extension's onboarding.js
async function onboardUser(username, preferences) {
  try {
    const response = await fetch('http://localhost:8000/user/onboard', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username,
        personality_type: preferences.personalityType,
        technical_level: preferences.technicalLevel
      })
    });
    
    if (response.ok) {
      const user = await response.json();
      // Store user ID in chrome.storage
      await chrome.storage.local.set({ userId: user.id });
      return user;
    } else {
      const error = await response.json();
      throw new Error(error.detail);
    }
  } catch (error) {
    console.error('Onboarding failed:', error);
    throw error;
  }
}
```

### Retrieving User Context

```javascript
// Get stored user ID and fetch full profile
async function getUserContext() {
  const { userId } = await chrome.storage.local.get('userId');
  
  if (!userId) {
    // User not onboarded yet
    return null;
  }
  
  const response = await fetch(`http://localhost:8000/user/${userId}`);
  
  if (response.ok) {
    return await response.json();
  }
  
  return null;
}
```

### Updating Preferences

```javascript
// Update user preferences from settings panel
async function updateUserPreferences(userId, preferences) {
  const response = await fetch(`http://localhost:8000/user/${userId}/preferences`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(preferences)
  });
  
  if (response.ok) {
    const updatedUser = await response.json();
    console.log('Preferences updated:', updatedUser);
    return updatedUser;
  } else {
    throw new Error('Failed to update preferences');
  }
}
```

---

## Testing

### Manual Testing

Run the manual test script to verify all endpoints:

```bash
# Make sure the server is running
python main.py

# In another terminal
python test_user_manual.py
```

### Automated Testing

Run the pytest test suite:

```bash
# Install dependencies
pip install pytest httpx pytest-asyncio

# Run tests
pytest tests/test_user_endpoints.py -v
```

---

## Database Schema

The user endpoints interact with the `profiles` table in Supabase:

```sql
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT NOT NULL UNIQUE,
    personality_type TEXT,
    technical_level TEXT CHECK (technical_level IN ('beginner', 'intermediate', 'advanced', 'expert')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_profiles_username ON profiles(username);
```

The `updated_at` field is automatically updated via a database trigger.

---

## Error Handling Best Practices

### Client-Side Error Handling

```javascript
async function createUser(username, preferences) {
  try {
    const response = await fetch('http://localhost:8000/user/onboard', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, ...preferences })
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      // Handle specific error codes
      switch (response.status) {
        case 400:
          alert('Invalid input. Please check your technical level.');
          break;
        case 409:
          alert('Username already taken. Please choose another.');
          break;
        case 500:
          alert('Server error. Please try again later.');
          break;
        default:
          alert(`Error: ${data.detail}`);
      }
      return null;
    }
    
    return data;
  } catch (error) {
    console.error('Network error:', error);
    alert('Unable to connect to server. Please check your connection.');
    return null;
  }
}
```

---

## Security Considerations

1. **Authentication**: Currently, endpoints do not require authentication. For production, implement proper authentication (JWT tokens, API keys, etc.)

2. **Rate Limiting**: Consider adding rate limiting to prevent abuse:
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   
   @app.post("/user/onboard")
   @limiter.limit("5/minute")
   async def onboard_user(request: Request, ...):
       # ...
   ```

3. **Input Validation**: All inputs are validated using Pydantic models with length constraints and enum checks.

4. **SQL Injection**: Protected by using Supabase's parameterized queries.

5. **Data Privacy**: User data should be handled according to GDPR/privacy regulations. Consider adding:
   - Data export functionality
   - Consent management
   - Audit logging

---

## Future Enhancements

- [ ] Add email verification during onboarding
- [ ] Implement password-based authentication
- [ ] Add user avatar upload
- [ ] Support for multiple profiles per account
- [ ] Advanced search/filtering of users (admin endpoint)
- [ ] User activity logs
- [ ] Bulk user operations
- [ ] OAuth integration (Google, GitHub, etc.)

---

## Support

For issues or questions:
- Check the main [README.md](../README.md)
- Review [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)
- Open an issue on GitHub
