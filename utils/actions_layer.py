"""
Actions Layer - Playwright Browser Automation
==============================================
Executes actions decided by the Judge Layer

Architecture Flow:
1. Browser Extension captures page context
2. Judge Layer analyzes and decides actions
3. Actions Layer executes via Playwright ⭐ YOU ARE HERE
"""

from playwright.async_api import async_playwright, Browser, Page, BrowserContext, Playwright
from typing import List, Dict, Optional, Any, Literal
import asyncio
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

# ============================================================================
# Browser Manager
# ============================================================================

class BrowserManager:
    """Manages persistent Playwright browser instances"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.playwright: Optional[Playwright] = None
        self._lock = asyncio.Lock()
        
    async def start(self, headless: bool = False):
        """Initialize Playwright and browser"""
        async with self._lock:
            if self.browser:
                return
                
            logger.info("🚀 Starting Playwright browser...")
            self.playwright = await async_playwright().start()
            
            self.browser = await self.playwright.chromium.launch(
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox'
                ]
            )
            
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                java_script_enabled=True,
                bypass_csp=True
            )
            
            logger.info("✓ Playwright browser started successfully")
        
    async def stop(self):
        """Clean up browser resources"""
        async with self._lock:
            if self.context:
                await self.context.close()
                self.context = None
            if self.browser:
                await self.browser.close()
                self.browser = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            logger.info("✓ Playwright browser stopped")
        
    async def get_page(self, url: str) -> Page:
        """Get or create a page for the given URL"""
        await self.start()
        
        if not self.context:
            raise RuntimeError("Browser context not initialized")
        
        # Check if page with URL already exists
        pages = self.context.pages
        for page in pages:
            if page.url == url:
                logger.info(f"📄 Reusing existing page for {url}")
                return page
                
        # Create new page
        logger.info(f"📄 Creating new page for {url}")
        page = await self.context.new_page()
        
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            logger.info(f"✓ Navigated to {url}")
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            # Return page anyway, might be useful for debugging
        
        return page
    
    async def create_new_page(self) -> Page:
        """Create a blank new page"""
        await self.start()
        
        if not self.context:
            raise RuntimeError("Browser context not initialized")
        
        page = await self.context.new_page()
        logger.info("📄 Created blank new page")
        return page

# Global browser manager instance
browser_manager = BrowserManager()


# ============================================================================
# Action Type Definitions
# ============================================================================

ActionType = Literal[
    "click",
    "fill",
    "type",
    "select",
    "check",
    "uncheck",
    "navigate",
    "scroll",
    "wait",
    "screenshot",
    "extract",
    "hover",
    "press",
    "hide_elements",
    "highlight_elements"
]


# ============================================================================
# Core Action Executors
# ============================================================================

async def execute_click(page: Page, selector: str, **kwargs) -> Dict:
    """Click an element"""
    try:
        await page.wait_for_selector(selector, timeout=5000, state='visible')
        await page.click(selector)
        logger.info(f"✓ Clicked: {selector}")
        return {"success": True, "action": "click", "selector": selector}
    except Exception as e:
        logger.error(f"Failed to click {selector}: {e}")
        return {"success": False, "error": str(e), "action": "click", "selector": selector}


async def execute_fill(page: Page, selector: str, value: str, **kwargs) -> Dict:
    """Fill a form field"""
    try:
        await page.wait_for_selector(selector, timeout=5000, state='visible')
        await page.fill(selector, value)
        logger.info(f"✓ Filled {selector} with: {value[:50]}...")
        return {"success": True, "action": "fill", "selector": selector, "value": value}
    except Exception as e:
        logger.error(f"Failed to fill {selector}: {e}")
        return {"success": False, "error": str(e), "action": "fill", "selector": selector}


async def execute_type(page: Page, selector: str, text: str, delay: int = 50, **kwargs) -> Dict:
    """Type text with delay (simulates human typing)"""
    try:
        await page.wait_for_selector(selector, timeout=5000, state='visible')
        await page.type(selector, text, delay=delay)
        logger.info(f"✓ Typed into {selector}: {text[:50]}...")
        return {"success": True, "action": "type", "selector": selector, "text": text}
    except Exception as e:
        logger.error(f"Failed to type into {selector}: {e}")
        return {"success": False, "error": str(e), "action": "type", "selector": selector}


async def execute_select(page: Page, selector: str, value: str, **kwargs) -> Dict:
    """Select option from dropdown"""
    try:
        await page.wait_for_selector(selector, timeout=5000, state='visible')
        await page.select_option(selector, value)
        logger.info(f"✓ Selected {value} in {selector}")
        return {"success": True, "action": "select", "selector": selector, "value": value}
    except Exception as e:
        logger.error(f"Failed to select option in {selector}: {e}")
        return {"success": False, "error": str(e), "action": "select", "selector": selector}


async def execute_check(page: Page, selector: str, **kwargs) -> Dict:
    """Check a checkbox"""
    try:
        await page.wait_for_selector(selector, timeout=5000, state='visible')
        await page.check(selector)
        logger.info(f"✓ Checked: {selector}")
        return {"success": True, "action": "check", "selector": selector}
    except Exception as e:
        logger.error(f"Failed to check {selector}: {e}")
        return {"success": False, "error": str(e), "action": "check", "selector": selector}


async def execute_uncheck(page: Page, selector: str, **kwargs) -> Dict:
    """Uncheck a checkbox"""
    try:
        await page.wait_for_selector(selector, timeout=5000, state='visible')
        await page.uncheck(selector)
        logger.info(f"✓ Unchecked: {selector}")
        return {"success": True, "action": "uncheck", "selector": selector}
    except Exception as e:
        logger.error(f"Failed to uncheck {selector}: {e}")
        return {"success": False, "error": str(e), "action": "uncheck", "selector": selector}


async def execute_navigate(page: Page, url: str, **kwargs) -> Dict:
    """Navigate to a URL"""
    try:
        await page.goto(url, wait_until='domcontentloaded', timeout=30000)
        logger.info(f"✓ Navigated to: {url}")
        return {"success": True, "action": "navigate", "url": url}
    except Exception as e:
        logger.error(f"Failed to navigate to {url}: {e}")
        return {"success": False, "error": str(e), "action": "navigate", "url": url}


async def execute_scroll(page: Page, selector: Optional[str] = None, x: int = 0, y: int = 0, **kwargs) -> Dict:
    """Scroll page or element"""
    try:
        if selector:
            await page.wait_for_selector(selector, timeout=5000)
            element = await page.query_selector(selector)
            if element:
                await element.scroll_into_view_if_needed()
                logger.info(f"✓ Scrolled to element: {selector}")
        else:
            await page.evaluate(f"window.scrollTo({x}, {y})")
            logger.info(f"✓ Scrolled page to ({x}, {y})")
        
        return {"success": True, "action": "scroll", "selector": selector, "x": x, "y": y}
    except Exception as e:
        logger.error(f"Failed to scroll: {e}")
        return {"success": False, "error": str(e), "action": "scroll"}


async def execute_wait(page: Page, milliseconds: int = 1000, selector: Optional[str] = None, **kwargs) -> Dict:
    """Wait for time or selector"""
    try:
        if selector:
            await page.wait_for_selector(selector, timeout=milliseconds)
            logger.info(f"✓ Waited for selector: {selector}")
        else:
            await asyncio.sleep(milliseconds / 1000)
            logger.info(f"✓ Waited {milliseconds}ms")
        
        return {"success": True, "action": "wait", "milliseconds": milliseconds, "selector": selector}
    except Exception as e:
        logger.error(f"Failed to wait: {e}")
        return {"success": False, "error": str(e), "action": "wait"}


async def execute_screenshot(page: Page, full_page: bool = False, **kwargs) -> Dict:
    """Take a screenshot"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        
        await page.screenshot(path=filename, full_page=full_page)
        logger.info(f"✓ Screenshot saved: {filename}")
        
        return {"success": True, "action": "screenshot", "filename": filename}
    except Exception as e:
        logger.error(f"Failed to take screenshot: {e}")
        return {"success": False, "error": str(e), "action": "screenshot"}


async def execute_extract(page: Page, selector: str, attribute: Optional[str] = None, **kwargs) -> Dict:
    """Extract text or attribute from element"""
    try:
        await page.wait_for_selector(selector, timeout=5000)
        
        if attribute:
            value = await page.get_attribute(selector, attribute)
        else:
            value = await page.text_content(selector)
        
        logger.info(f"✓ Extracted from {selector}: {value[:50] if value else 'None'}...")
        return {"success": True, "action": "extract", "selector": selector, "value": value}
    except Exception as e:
        logger.error(f"Failed to extract from {selector}: {e}")
        return {"success": False, "error": str(e), "action": "extract", "selector": selector}


async def execute_hover(page: Page, selector: str, **kwargs) -> Dict:
    """Hover over an element"""
    try:
        await page.wait_for_selector(selector, timeout=5000, state='visible')
        await page.hover(selector)
        logger.info(f"✓ Hovered over: {selector}")
        return {"success": True, "action": "hover", "selector": selector}
    except Exception as e:
        logger.error(f"Failed to hover over {selector}: {e}")
        return {"success": False, "error": str(e), "action": "hover", "selector": selector}


async def execute_press(page: Page, key: str, selector: Optional[str] = None, **kwargs) -> Dict:
    """Press a keyboard key"""
    try:
        if selector:
            await page.press(selector, key)
            logger.info(f"✓ Pressed {key} in {selector}")
        else:
            await page.keyboard.press(key)
            logger.info(f"✓ Pressed {key}")
        
        return {"success": True, "action": "press", "key": key, "selector": selector}
    except Exception as e:
        logger.error(f"Failed to press {key}: {e}")
        return {"success": False, "error": str(e), "action": "press", "key": key}


async def execute_hide_elements(page: Page, selectors: List[str], **kwargs) -> Dict:
    """Hide elements using CSS"""
    try:
        for selector in selectors:
            await page.add_style_tag(content=f"{selector} {{ display: none !important; }}")
        
        logger.info(f"✓ Hidden {len(selectors)} element(s)")
        return {"success": True, "action": "hide_elements", "selectors": selectors}
    except Exception as e:
        logger.error(f"Failed to hide elements: {e}")
        return {"success": False, "error": str(e), "action": "hide_elements"}


async def execute_highlight_elements(page: Page, selectors: List[str], **kwargs) -> Dict:
    """Highlight elements using CSS"""
    try:
        for selector in selectors:
            await page.add_style_tag(
                content=f"{selector} {{ outline: 3px solid #ff6b6b !important; outline-offset: 2px; }}"
            )
        
        logger.info(f"✓ Highlighted {len(selectors)} element(s)")
        return {"success": True, "action": "highlight_elements", "selectors": selectors}
    except Exception as e:
        logger.error(f"Failed to highlight elements: {e}")
        return {"success": False, "error": str(e), "action": "highlight_elements"}


# ============================================================================
# Action Dispatcher
# ============================================================================

ACTION_MAP = {
    "click": execute_click,
    "fill": execute_fill,
    "type": execute_type,
    "select": execute_select,
    "check": execute_check,
    "uncheck": execute_uncheck,
    "navigate": execute_navigate,
    "scroll": execute_scroll,
    "wait": execute_wait,
    "screenshot": execute_screenshot,
    "extract": execute_extract,
    "hover": execute_hover,
    "press": execute_press,
    "hide_elements": execute_hide_elements,
    "highlight_elements": execute_highlight_elements,
}


async def execute_single_action(page: Page, action: Dict[str, Any]) -> Dict:
    """
    Execute a single action
    
    Args:
        page: Playwright page object
        action: Action dictionary with 'type' and parameters
        
    Returns:
        Result dictionary with success status
    """
    action_type = action.get("type")
    
    if not action_type:
        return {"success": False, "error": "Missing action type"}
    
    executor = ACTION_MAP.get(action_type)
    
    if not executor:
        return {"success": False, "error": f"Unknown action type: {action_type}"}
    
    # Execute action with all parameters
    return await executor(page, **action)


# ============================================================================
# Main Action Execution
# ============================================================================

async def execute_actions(
    url: str,
    actions: List[Dict[str, Any]],
    user_id: str,
    headless: bool = False
) -> Dict[str, Any]:
    """
    Execute a list of actions from the Judge Layer
    
    Args:
        url: Target page URL
        actions: List of action dictionaries
        user_id: User ID for logging
        headless: Run browser in headless mode
        
    Returns:
        Execution results with status for each action
        
    Example actions:
        [
            {"type": "click", "selector": "#submit-btn"},
            {"type": "fill", "selector": "input[name='email']", "value": "test@example.com"},
            {"type": "screenshot", "full_page": True}
        ]
    """
    logger.info(f"🎬 Starting action execution for user {user_id}")
    logger.info(f"   URL: {url}")
    logger.info(f"   Actions: {len(actions)}")
    
    results = {
        "user_id": user_id,
        "url": url,
        "timestamp": datetime.utcnow().isoformat(),
        "total_actions": len(actions),
        "actions": [],
        "success_count": 0,
        "failure_count": 0,
    }
    
    page = None
    
    try:
        # Get or create page
        page = await browser_manager.get_page(url)
        
        # Execute each action sequentially
        for i, action in enumerate(actions, 1):
            logger.info(f"📋 Executing action {i}/{len(actions)}: {action.get('type')}")
            
            result = await execute_single_action(page, action)
            results["actions"].append(result)
            
            if result.get("success"):
                results["success_count"] += 1
            else:
                results["failure_count"] += 1
                
                # Stop on critical errors unless configured otherwise
                if action.get("critical", False):
                    logger.error(f"❌ Critical action failed, stopping execution")
                    break
            
            # Small delay between actions for stability
            await asyncio.sleep(0.1)
        
        logger.info(f"✅ Action execution complete: {results['success_count']} success, {results['failure_count']} failed")
        
    except Exception as e:
        logger.error(f"❌ Fatal error during action execution: {e}")
        results["error"] = str(e)
        results["fatal_error"] = True
        
    return results


async def apply_ui_modifications(
    url: str,
    hidden_selectors: List[str],
    highlight_selectors: List[str],
    user_id: str
) -> Dict[str, Any]:
    """
    Apply UI modifications (hide/highlight) decided by Judge Layer
    
    Args:
        url: Target page URL
        hidden_selectors: CSS selectors to hide
        highlight_selectors: CSS selectors to highlight
        user_id: User ID for logging
        
    Returns:
        Result dictionary
    """
    logger.info(f"🎨 Applying UI modifications for user {user_id}")
    
    actions = []
    
    if hidden_selectors:
        actions.append({
            "type": "hide_elements",
            "selectors": hidden_selectors
        })
    
    if highlight_selectors:
        actions.append({
            "type": "highlight_elements",
            "selectors": highlight_selectors
        })
    
    if not actions:
        logger.info("No UI modifications to apply")
        return {"success": True, "message": "No modifications needed"}
    
    return await execute_actions(url, actions, user_id)


# ============================================================================
# Utility Functions
# ============================================================================

async def get_page_info(url: str) -> Dict[str, Any]:
    """
    Get information about a page without modifying it
    
    Returns:
        Page information (title, url, screenshot path, etc.)
    """
    try:
        page = await browser_manager.get_page(url)
        
        title = await page.title()
        current_url = page.url
        
        return {
            "success": True,
            "title": title,
            "url": current_url,
            "viewport": page.viewport_size,
        }
    except Exception as e:
        logger.error(f"Error getting page info: {e}")
        return {"success": False, "error": str(e)}


async def close_browser():
    """Close the browser (cleanup)"""
    await browser_manager.stop()


# ============================================================================
# Lifecycle Management
# ============================================================================

async def initialize():
    """Initialize the actions layer"""
    logger.info("🎭 Initializing Actions Layer (Playwright)...")
    # Browser is started on-demand, nothing to do here
    logger.info("✓ Actions Layer ready (browser will start on first use)")


async def shutdown():
    """Shutdown the actions layer"""
    logger.info("🛑 Shutting down Actions Layer...")
    await close_browser()
    logger.info("✓ Actions Layer shutdown complete")


if __name__ == "__main__":
    # Test the actions layer
    async def test():
        print("=" * 60)
        print("🧪 Testing Actions Layer")
        print("=" * 60)
        
        # Test actions
        test_actions = [
            {"type": "navigate", "url": "https://example.com"},
            {"type": "wait", "milliseconds": 1000},
            {"type": "screenshot", "full_page": True},
        ]
        
        results = await execute_actions(
            url="https://example.com",
            actions=test_actions,
            user_id="test-user-123"
        )
        
        print("\n📊 Results:")
        print(json.dumps(results, indent=2))
        
        # Cleanup
        await shutdown()
        
        print("\n" + "=" * 60)
        print("✅ Test complete!")
        print("=" * 60)
    
    asyncio.run(test())
