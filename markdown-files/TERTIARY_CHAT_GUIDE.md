# Tertiary Chat Layer - Proactive Tutor Guide

## Overview

The **Tertiary Chat Layer** is the "background tutor" that runs alongside the main Judge Engine. It:

1. **Detects knowledge gaps** between user skill level and page complexity
2. **Generates proactive nudges** to help users navigate appropriately
3. **Handles chat queries** with context-aware responses
4. **Pushes messages** via WebSocket in real-time

## 🧠 How It Works

### Knowledge Gap Detection

The system analyzes:
- **Page complexity** (beginner/intermediate/advanced/expert)
- **User technical level** (from profile)
- **Page content** (tutorials, documentation, forms, etc.)
- **Concepts present** (React, backend, DevOps, security, etc.)

When there's a mismatch, it generates a helpful nudge.

## 📊 Nudge Types

### 1. **Simplify** (Page too advanced)
- **Trigger**: Page is 2+ levels above user
- **Example**: Beginner on Advanced React
- **Nudge**: "👋 This page looks pretty advanced. Want me to find something more beginner-friendly?"

### 2. **Encourage** (Slight challenge)
- **Trigger**: Page is 1 level above user
- **Example**: Intermediate on Advanced content
- **Nudge**: "💡 Great choice! This is a good next step for your intermediate level."

### 3. **Suggest Advanced** (Page too basic)
- **Trigger**: Page is 2+ levels below user
- **Example**: Expert on Beginner tutorial
- **Nudge**: "⚡ You might want to skip to the advanced sections - this intro is probably too basic for you."

### 4. **Skip Basics** (Expert on tutorial)
- **Trigger**: Expert/Advanced user on tutorial page
- **Nudge**: "💫 Expert tip: Feel free to jump past the basics here!"

### 5. **Form Help** (Beginner on forms)
- **Trigger**: Beginner user encounters a form
- **Nudge**: "📝 Take your time with this form. I can help if you get stuck!"

## 🔌 WebSocket Integration

### Message Format

Proactive nudges are sent via WebSocket:

```json
{
  "type": "proactive_nudge",
  "message": "👋 This page looks pretty advanced...",
  "priority": "normal",
  "timestamp": "2025-12-12T10:30:00Z",
  "dismissible": true
}
```

### Priority Levels
- `low`: Can be ignored/queued
- `normal`: Show as notification
- `high`: Require attention

## 🚀 Usage in Your Code

### 1. Automatic Integration (Already Setup)

The `/analyze` endpoint automatically:
1. Analyzes the page with Judge Engine
2. Checks if user is connected via WebSocket
3. Generates and sends proactive nudge in background

```python
# This happens automatically in main.py
background_tasks.add_task(
    analyze_and_nudge,
    connection_manager,
    user_id,
    html_content,
    user_profile,
    page_url
)
```

### 2. Manual Nudge Generation

```python
from tertiary_chat import generate_proactive_nudge

nudge = await generate_proactive_nudge(
    html_summary=html_content,
    user_profile={
        "username": "Alice",
        "technical_level": "beginner",
        "personality_type": "visual"
    },
    page_url="https://example.com/page"
)

if nudge:
    print(f"Nudge: {nudge}")
```

### 3. Handle Chat Queries

```python
from tertiary_chat import handle_chat_query

response = await handle_chat_query(
    user_message="How do I fill out this form?",
    user_profile={
        "username": "Bob",
        "technical_level": "intermediate"
    },
    page_context={
        "url": "https://example.com/form",
        "type": "form"
    }
)
```

### 4. Direct WebSocket Push

```python
from tertiary_chat import push_nudge_to_websocket

success = await push_nudge_to_websocket(
    connection_manager=connection_manager,
    client_id="user-123",
    nudge_message="💡 Tip: This button submits the form",
    priority="normal"
)
```

## 🎯 User Profiles

### Required Fields
```python
{
    "username": "Alice",           # Display name
    "technical_level": "beginner", # beginner/intermediate/advanced/expert
    "personality_type": "visual"   # Optional: visual/analytical/cautious/etc.
}
```

### Technical Levels
- **Beginner**: New to programming/topic
- **Intermediate**: Comfortable with basics
- **Advanced**: Deep knowledge, building complex systems
- **Expert**: Industry professional, contributor-level

## 📱 Browser Extension Integration

### Connecting to WebSocket

```javascript
// In your Chrome extension
const userId = "user-123"; // From authentication
const ws = new WebSocket(`ws://localhost:8000/chat/${userId}`);

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === "proactive_nudge") {
    // Show notification to user
    showNotification(data.message, data.priority);
  }
};
```

### Sending Queries

```javascript
// User asks a question
ws.send(JSON.stringify({
  type: "query",
  message: "What does this button do?",
  page_context: {
    url: window.location.href,
    type: "form"
  }
}));
```

## 🧪 Testing

Run the test suite:

```bash
uv run test_tertiary.py
```

This tests:
1. Page complexity detection
2. Nudge generation for various scenarios
3. Fallback templates

## ⚙️ Configuration

### Adjusting Thresholds

In `tertiary_chat.py`, modify:

```python
# Gap detection (lines ~120-140)
if gap >= 2:  # Change threshold
    needs_nudge = True
    nudge_type = "simplify"
```

### Customizing LLM Behavior

Edit the system prompt in `generate_nudge_with_llm()`:

```python
system_prompt = f"""You are a friendly, proactive tutor...
# Customize tone, style, length here
"""
```

### Fallback Templates

Modify templates in `generate_fallback_nudge()` when Gemini API is unavailable:

```python
templates = {
    "simplify": f"👋 Hey {username}, custom message here...",
    # Add more templates
}
```

## 🔄 Workflow

```
User visits page
       ↓
/analyze endpoint called
       ↓
Judge Engine analyzes (main decision)
       ↓
[Background Task]
       ↓
Tertiary Chat detects complexity
       ↓
Knowledge gap found?
       ↓
Generate personalized nudge (Gemini)
       ↓
Push to WebSocket (if connected)
       ↓
User sees helpful tip!
```

## 💡 Best Practices

### 1. **Don't Over-Nudge**
- Only send nudges when there's a genuine knowledge gap
- Respect user's dismissals (track in profile)

### 2. **Personalize**
- Use username in messages
- Adjust tone based on personality_type
- Consider past interactions

### 3. **Be Timely**
- Send nudges right when page loads
- Don't delay - user context is fresh

### 4. **Provide Value**
- Nudges should be actionable
- Include specific suggestions
- Link to resources when relevant

## 🐛 Troubleshooting

### No nudges appearing?
1. Check WebSocket connection: `GET /connections`
2. Verify user profile has `technical_level`
3. Check logs for complexity detection results

### Nudges too frequent?
- Increase gap threshold (gap >= 3)
- Add cooldown timer per user
- Track dismissals

### LLM failures?
- Fallback templates are used automatically
- Check Gemini API quota
- Verify `GEMINI_API_KEY` in .env

## 📚 Example Scenarios

### Scenario 1: Beginner Learning to Code
**Page**: "Advanced React Hooks Tutorial"  
**User Level**: beginner  
**Nudge**: "👋 React Hooks assume you know components. Want me to find a simpler intro first?"

### Scenario 2: Expert on Basic Tutorial
**Page**: "HTML Basics for Beginners"  
**User Level**: expert  
**Nudge**: "⚡ Expert tip: You can skip straight to the projects section!"

### Scenario 3: Form Assistance
**Page**: Payment form  
**User Level**: beginner  
**Nudge**: "📝 Take your time filling this out. I'll help if you need it!"

## 🔮 Future Enhancements

- [ ] Track nudge effectiveness (did user click suggested link?)
- [ ] Learn from user dismissals
- [ ] Multi-language support
- [ ] Voice-based nudges
- [ ] Context-aware timing (wait until user scrolls to complex section)
- [ ] Integration with user's learning history

---

**Made with ❤️ for better web navigation**
