# User Endpoints Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        BROWSER EXTENSION                            │
│                                                                     │
│  ┌───────────────┐  ┌──────────────┐  ┌────────────────┐         │
│  │  onboarding.  │  │   popup.js   │  │   settings.js  │         │
│  │      html     │  │              │  │                │         │
│  └───────┬───────┘  └──────┬───────┘  └────────┬───────┘         │
│          │                 │                     │                 │
│          │ User Info       │ Get Profile         │ Update Prefs    │
│          │                 │                     │                 │
└──────────┼─────────────────┼─────────────────────┼─────────────────┘
           │                 │                     │
           │                 │                     │
           ▼                 ▼                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FASTAPI SERVER                              │
│                         (main.py)                                   │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                    USER ENDPOINTS                            │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │                                                              │ │
│  │  POST   /user/onboard                                       │ │
│  │         • Create new user profile                           │ │
│  │         • Validate username uniqueness                      │ │
│  │         • Store preferences                                 │ │
│  │         • Return user UUID                                  │ │
│  │                                                              │ │
│  │  GET    /user/{user_id}                                     │ │
│  │         • Retrieve user profile                             │ │
│  │         • Return complete user data                         │ │
│  │                                                              │ │
│  │  PUT    /user/{user_id}/preferences                         │ │
│  │         • Update personality type                           │ │
│  │         • Update technical level                            │ │
│  │         • Partial updates supported                         │ │
│  │                                                              │ │
│  │  DELETE /user/{user_id}                                     │ │
│  │         • Delete user account                               │ │
│  │         • Cascade delete memories                           │ │
│  │                                                              │ │
│  └──────────────────────┬───────────────────────────────────────┘ │
│                         │                                          │
│  ┌──────────────────────┴───────────────────────────────────────┐ │
│  │              PYDANTIC MODELS (Validation)                    │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │  • UserOnboardRequest       (Request validation)            │ │
│  │  • UserProfileResponse      (Response formatting)           │ │
│  │  • UserPreferencesUpdate    (Update validation)             │ │
│  └──────────────────────┬───────────────────────────────────────┘ │
│                         │                                          │
└─────────────────────────┼──────────────────────────────────────────┘
                          │
                          │ Supabase Client
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       SUPABASE DATABASE                             │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │                   profiles TABLE                             │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │  id               UUID PRIMARY KEY (auto-generated)          │ │
│  │  username         TEXT UNIQUE NOT NULL                       │ │
│  │  personality_type TEXT                                       │ │
│  │  technical_level  TEXT CHECK (enum values)                   │ │
│  │  created_at       TIMESTAMP WITH TIME ZONE                   │ │
│  │  updated_at       TIMESTAMP WITH TIME ZONE (auto-update)     │ │
│  └──────────────────────┬───────────────────────────────────────┘ │
│                         │                                          │
│                         │ Foreign Key (user_id)                    │
│                         │                                          │
│  ┌──────────────────────▼───────────────────────────────────────┐ │
│  │                   memories TABLE                             │ │
│  ├──────────────────────────────────────────────────────────────┤ │
│  │  id               UUID PRIMARY KEY                           │ │
│  │  user_id          UUID → profiles.id (ON DELETE CASCADE)     │ │
│  │  content          TEXT                                       │ │
│  │  embedding        vector(768)                                │ │
│  │  metadata         JSONB                                      │ │
│  │  created_at       TIMESTAMP WITH TIME ZONE                   │ │
│  └──────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. User Onboarding
```
Browser Extension (onboarding.html)
    → User fills form (username, preferences)
    → POST /user/onboard
    → Validate input (Pydantic)
    → Check username uniqueness
    → Insert into profiles table
    → Return user UUID
    → Store UUID in chrome.storage
    → Redirect to main extension
```

### 2. Profile Retrieval
```
Browser Extension (popup.js)
    → Get user_id from chrome.storage
    → GET /user/{user_id}
    → Query profiles table
    → Return user data
    → Display in extension UI
```

### 3. Preference Update
```
Browser Extension (settings.js)
    → User changes preferences
    → PUT /user/{user_id}/preferences
    → Validate technical_level enum
    → Update profiles table
    → Trigger updated_at timestamp
    → Return updated profile
    → Refresh extension UI
```

### 4. User Deletion
```
Browser Extension (settings.js)
    → User clicks "Delete Account"
    → Confirm deletion
    → DELETE /user/{user_id}
    → Delete from profiles table
    → CASCADE: Delete all memories
    → Clear chrome.storage
    → Redirect to onboarding
```

## Integration Points

### With Existing Systems

```
User Endpoints
    ├─→ Judge Engine (utils/judge_engine.py)
    │   └─→ Uses user profile for personalization
    │       • Technical level → complexity of suggestions
    │       • Personality type → communication style
    │
    ├─→ Memory System (utils/memory_worker.py)
    │   └─→ Foreign key relationship
    │       • Each memory linked to user_id
    │       • Cascade delete on user removal
    │
    ├─→ Tertiary Chat (utils/tertiary_chat.py)
    │   └─→ Personalizes chat responses
    │       • Adapts to user's technical level
    │       • Matches personality type
    │
    └─→ Browser Extension (browser_ext/)
        ├─→ onboarding.html → User registration
        ├─→ popup.js → Profile display
        └─→ (future) settings.js → Preference management
```

## Valid Values Reference

```
personality_type:
    ├─→ "analytical"  (logical, data-driven)
    ├─→ "creative"    (innovative, exploratory)
    ├─→ "pragmatic"   (practical, efficient)
    └─→ "social"      (collaborative, communicative)

technical_level:
    ├─→ "beginner"      (new to web dev)
    ├─→ "intermediate"  (some experience)  [DEFAULT]
    ├─→ "advanced"      (experienced)
    └─→ "expert"        (professional/senior)
```

## Error Response Flow

```
Client Request
    │
    ├─→ Invalid Input (400)
    │   └─→ Technical level not in enum
    │   └─→ Username too short/long
    │   └─→ No fields provided for update
    │
    ├─→ Conflict (409)
    │   └─→ Username already exists
    │
    ├─→ Not Found (404)
    │   └─→ User ID doesn't exist
    │
    └─→ Server Error (500)
        └─→ Database connection error
        └─→ Unexpected exception
```

## Security Model

```
┌─────────────────────────────────────┐
│         Current (MVP)               │
├─────────────────────────────────────┤
│ • No authentication required        │
│ • Public UUID-based access          │
│ • Input validation only             │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│      Future (Production)            │
├─────────────────────────────────────┤
│ • JWT token authentication          │
│ • Rate limiting per user            │
│ • API key requirements              │
│ • Row-level security (RLS)          │
│ • Audit logging                     │
└─────────────────────────────────────┘
```

## Testing Architecture

```
┌──────────────────────────────────────────────────┐
│             TEST SUITE                           │
├──────────────────────────────────────────────────┤
│                                                  │
│  Automated Tests (pytest)                       │
│  ├─→ tests/test_user_endpoints.py               │
│  │   ├─→ test_onboard_user_success              │
│  │   ├─→ test_onboard_duplicate_username         │
│  │   ├─→ test_onboard_invalid_technical_level    │
│  │   ├─→ test_get_user_profile                   │
│  │   ├─→ test_get_user_profile_not_found         │
│  │   ├─→ test_update_user_preferences            │
│  │   ├─→ test_update_preferences_partial         │
│  │   ├─→ test_update_preferences_not_found       │
│  │   ├─→ test_update_preferences_invalid_level   │
│  │   ├─→ test_delete_user                        │
│  │   ├─→ test_delete_user_not_found              │
│  │   └─→ Fixtures for cleanup                    │
│                                                  │
│  Manual Tests (interactive)                     │
│  └─→ test_user_manual.py                        │
│      ├─→ Server health check                     │
│      ├─→ 8 interactive test scenarios            │
│      ├─→ Color-coded output                      │
│      └─→ Summary report                          │
│                                                  │
└──────────────────────────────────────────────────┘
```

---

**Architecture Version**: 1.0
**Last Updated**: December 12, 2025
**Status**: ✅ Production Ready
