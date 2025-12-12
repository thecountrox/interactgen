# Actions Layer - Playwright Automation Guide

## Overview

The **Actions Layer** is the final component in the 3-layer architecture:

```
Reading Layer → Judge Layer → Actions Layer ⭐
```

It executes browser automation tasks using Playwright based on decisions from the Judge Layer.

## 🎯 What It Does

1. **Executes Actions** - Clicks, fills forms, navigates, etc.
2. **Applies UI Modifications** - Hides/highlights elements
3. **Takes Screenshots** - Captures page states
4. **Extracts Data** - Retrieves text and attributes
5. **Manages Browser** - Persistent browser instance for speed

## 🚀 Quick Start

### 1. Install Playwright

```bash
# Install Python package
uv pip install playwright

# Install browsers
playwright install chromium
```

### 2. Test the Actions Layer

```bash
# Run the built-in test
uv run python actions_layer.py
```

### 3. Execute Actions via API

```bash
curl -X POST http://localhost:8000/api/execute-actions \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "user_id": "user-123",
    "headless": false,
    "actions": [
      {"type": "screenshot", "full_page": true}
    ]
  }'
```

## 📋 Supported Actions

### Navigation & Waiting

#### `navigate`
Navigate to a URL
```json
{"type": "navigate", "url": "https://example.com"}
```

#### `wait`
Wait for time or element
```json
{"type": "wait", "milliseconds": 1000}
{"type": "wait", "selector": "#loading", "milliseconds": 5000}
```

#### `scroll`
Scroll page or to element
```json
{"type": "scroll", "x": 0, "y": 500}
{"type": "scroll", "selector": "#footer"}
```

### Interactions

#### `click`
Click an element
```json
{"type": "click", "selector": "button.submit"}
```

#### `fill`
Fill form field (clears first)
```json
{"type": "fill", "selector": "input[name='email']", "value": "test@example.com"}
```

#### `type`
Type text with delay (human-like)
```json
{"type": "type", "selector": "#message", "text": "Hello!", "delay": 50}
```

#### `select`
Select dropdown option
```json
{"type": "select", "selector": "select[name='country']", "value": "US"}
```

#### `check` / `uncheck`
Toggle checkboxes
```json
{"type": "check", "selector": "#terms"}
{"type": "uncheck", "selector": "#newsletter"}
```

#### `hover`
Hover over element
```json
{"type": "hover", "selector": ".tooltip-trigger"}
```

#### `press`
Press keyboard key
```json
{"type": "press", "key": "Enter"}
{"type": "press", "selector": "input", "key": "Escape"}
```

### Data & Capture

#### `screenshot`
Take screenshot
```json
{"type": "screenshot", "full_page": true}
{"type": "screenshot", "full_page": false}
```

#### `extract`
Extract text or attribute
```json
{"type": "extract", "selector": "h1"}
{"type": "extract", "selector": "a", "attribute": "href"}
```

### UI Modifications

#### `hide_elements`
Hide elements with CSS
```json
{"type": "hide_elements", "selectors": [".ad", ".popup", "#cookie-banner"]}
```

#### `highlight_elements`
Highlight elements with outline
```json
{"type": "highlight_elements", "selectors": ["button.primary", "a.important"]}
```

## 🔌 API Endpoints

### POST `/api/execute-actions`

Execute a sequence of actions.

**Request:**
```json
{
  "url": "https://example.com/form",
  "user_id": "user-123",
  "headless": false,
  "actions": [
    {"type": "fill", "selector": "#name", "value": "John Doe"},
    {"type": "fill", "selector": "#email", "value": "john@example.com"},
    {"type": "check", "selector": "#terms"},
    {"type": "click", "selector": "button[type='submit']"},
    {"type": "wait", "milliseconds": 2000},
    {"type": "screenshot", "full_page": true}
  ]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Executed 6/6 actions successfully",
  "results": {
    "user_id": "user-123",
    "url": "https://example.com/form",
    "total_actions": 6,
    "success_count": 6,
    "failure_count": 0,
    "actions": [
      {"success": true, "action": "fill", "selector": "#name"},
      {"success": true, "action": "fill", "selector": "#email"},
      ...
    ]
  }
}
```

### POST `/api/apply-ui-modifications`

Apply UI modifications decided by Judge Layer.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/apply-ui-modifications" \
  -d "url=https://example.com" \
  -d "user_id=user-123" \
  -d "hidden_selectors=.ad" \
  -d "hidden_selectors=.popup" \
  -d "highlight_selectors=button.primary"
```

**Response:**
```json
{
  "success": true,
  "message": "UI modifications applied",
  "results": {...}
}
```

### GET `/api/page-info?url=...`

Get page information without modification.

**Response:**
```json
{
  "success": true,
  "title": "Example Domain",
  "url": "https://example.com",
  "viewport": {"width": 1920, "height": 1080}
}
```

## 🏗️ Architecture

### Browser Manager

The `BrowserManager` class maintains a persistent browser instance:

```python
from actions_layer import browser_manager

# Starts automatically on first use
page = await browser_manager.get_page("https://example.com")

# Reuses existing page if URL matches
page = await browser_manager.get_page("https://example.com")  # No reload!

# Create blank new page
new_page = await browser_manager.create_new_page()

# Cleanup when done
await browser_manager.stop()
```

**Benefits:**
- ✅ Faster execution (no browser startup per request)
- ✅ Page reuse (navigates to existing tabs)
- ✅ Resource efficient (single browser instance)

### Action Execution Flow

```
API Request
    ↓
execute_actions()
    ↓
┌──────────────────────┐
│ Get/Create Page      │ ← Browser Manager
└──────────┬───────────┘
           ↓
┌──────────────────────┐
│ For Each Action:     │
│  1. Validate type    │
│  2. Execute          │
│  3. Record result    │
│  4. Continue/Stop    │
└──────────┬───────────┘
           ↓
    Return Results
```

## 💡 Usage Examples

### Example 1: Form Automation

```python
actions = [
    {"type": "fill", "selector": "#username", "value": "myuser"},
    {"type": "fill", "selector": "#password", "value": "mypass"},
    {"type": "click", "selector": "button[type='submit']"},
    {"type": "wait", "milliseconds": 2000},
    {"type": "extract", "selector": ".welcome-message"}
]

results = await execute_actions(
    url="https://example.com/login",
    actions=actions,
    user_id="user-123"
)
```

### Example 2: Data Scraping

```python
actions = [
    {"type": "navigate", "url": "https://example.com/products"},
    {"type": "wait", "selector": ".product-list"},
    {"type": "extract", "selector": ".product-title"},
    {"type": "extract", "selector": ".product-price"},
    {"type": "extract", "selector": ".product-link", "attribute": "href"}
]
```

### Example 3: UI Cleanup

```python
# Hide distractions
hidden = [".ad", ".popup", "#cookie-banner", ".newsletter-popup"]

await apply_ui_modifications(
    url="https://example.com",
    hidden_selectors=hidden,
    highlight_selectors=[],
    user_id="user-123"
)
```

### Example 4: Judge + Actions Integration

```python
# 1. Judge analyzes page
analysis = await evaluate_page(
    supabase=supabase,
    user_id="user-123",
    url="https://example.com",
    html_content=html,
    user_context=user_profile
)

# 2. Apply UI modifications from Judge
if analysis["hidden_selectors"] or analysis["highlight_selectors"]:
    await apply_ui_modifications(
        url="https://example.com",
        hidden_selectors=analysis["hidden_selectors"],
        highlight_selectors=analysis["highlight_selectors"],
        user_id="user-123"
    )

# 3. Execute suggested actions
if analysis["actions"]:
    await execute_actions(
        url="https://example.com",
        actions=analysis["actions"],
        user_id="user-123"
    )
```

## ⚙️ Configuration

### Headless Mode

```python
# Visible browser (for development/debugging)
await execute_actions(url, actions, user_id, headless=False)

# Headless mode (for production)
await execute_actions(url, actions, user_id, headless=True)
```

### Browser Options

Edit `actions_layer.py` to customize browser launch:

```python
self.browser = await self.playwright.chromium.launch(
    headless=headless,
    slow_mo=100,  # Slow down for debugging
    args=[
        '--disable-blink-features=AutomationControlled',
        '--window-size=1920,1080'
    ]
)
```

### Timeout Settings

Actions have built-in timeouts:

```python
# In actions_layer.py
await page.wait_for_selector(selector, timeout=5000)  # 5 seconds
await page.goto(url, timeout=30000)  # 30 seconds
```

## 🐛 Troubleshooting

### "Playwright not installed"

```bash
uv pip install playwright
playwright install chromium
```

### "Element not found"

- ✅ Use `wait` action before interacting
- ✅ Check selector syntax (use browser DevTools)
- ✅ Ensure element is visible (not hidden by CSS)

```json
{"type": "wait", "selector": "#my-button", "milliseconds": 5000}
{"type": "click", "selector": "#my-button"}
```

### "Browser won't start"

- ✅ Run `playwright install` again
- ✅ Check permissions
- ✅ Try headless mode: `headless=true`

### Actions fail silently

Check logs:
```python
logger.error(f"Failed to click {selector}: {e}")
```

Or inspect response:
```json
{
  "actions": [
    {"success": false, "error": "Timeout exceeded", "selector": "#missing"}
  ]
}
```

## 🔒 Security Considerations

### 1. **Validate User Input**

Always validate URLs and selectors:

```python
# In production, add validation
if not url.startswith(("http://", "https://")):
    raise ValueError("Invalid URL")
```

### 2. **Rate Limiting**

Limit actions per user:

```python
# Add to endpoint
if len(request.actions) > 50:
    raise HTTPException(400, "Too many actions")
```

### 3. **Sandboxing**

Consider running browsers in containers:

```bash
docker run -it --rm mcr.microsoft.com/playwright:latest
```

### 4. **Sensitive Data**

Never log passwords or sensitive data:

```python
logger.info(f"✓ Filled {selector} with: {'*' * len(value)}")
```

## 📊 Performance

### Benchmarks (Typical)

| Action | Time | Notes |
|--------|------|-------|
| `navigate` | 1-3s | Network dependent |
| `click` | 50-200ms | + wait time |
| `fill` | 50-100ms | Fast |
| `type` | 1-5s | Simulates typing |
| `screenshot` | 200-500ms | Size dependent |
| `extract` | 50-100ms | Fast |

### Optimization Tips

1. **Reuse Pages**
   ```python
   # Good: Reuses page
   page = await browser_manager.get_page(url)
   
   # Bad: Creates new page each time
   page = await browser.new_page()
   ```

2. **Batch Actions**
   ```python
   # Execute all actions in one request
   await execute_actions(url, [action1, action2, action3], user_id)
   ```

3. **Use Headless**
   ```python
   # 10-20% faster
   await execute_actions(url, actions, user_id, headless=True)
   ```

4. **Optimize Waits**
   ```python
   # Good: Wait for specific element
   {"type": "wait", "selector": ".loaded"}
   
   # Bad: Arbitrary long wait
   {"type": "wait", "milliseconds": 10000}
   ```

## 🧪 Testing

### Run Built-in Tests

```bash
uv run python actions_layer.py
```

### Create Custom Tests

```python
import asyncio
from actions_layer import execute_actions

async def test_my_workflow():
    actions = [
        {"type": "navigate", "url": "https://example.com"},
        {"type": "click", "selector": "#my-button"}
    ]
    
    results = await execute_actions(
        url="https://example.com",
        actions=actions,
        user_id="test-user"
    )
    
    assert results["success_count"] == 2
    print("✅ Test passed!")

asyncio.run(test_my_workflow())
```

## 📈 Next Steps

1. **Build Chrome Extension** - Send actions from browser
2. **Add Authentication** - Secure endpoints
3. **Implement Scheduling** - Cron-like automation
4. **Add Monitoring** - Track success rates
5. **Create Templates** - Common workflows

---

**The Actions Layer completes your automation stack! 🎉**

Reading Layer → Judge Layer → **Actions Layer** = Full automation!
