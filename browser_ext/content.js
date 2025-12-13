// content.js

console.log('FlowState: Content script loaded');

// Listen for action execution requests from popup (set up immediately)
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log('FlowState: Message received', message);
  if (message?.type === 'executeActions' && message?.actions) {
    console.log('FlowState: Executing actions from popup', message.actions);
    showExecutionOverlay();
    applyDOMManipulations({ actions: message.actions });
    sendResponse({ success: true });
    return true;
  }
  return false;
});

// Ensure we run only after the page is fully loaded
const init = async () => {
  if (document.readyState === 'loading') {
    await new Promise(resolve => window.addEventListener('load', resolve));
  }

  // Get the user's UUID
  const storage = await chrome.storage.local.get('user_uuid');
  const uuid = storage.user_uuid;

  if (!uuid) {
    console.warn('FlowState: No User UUID found. Please complete onboarding.');
    return;
  }

  console.log('FlowState: Initialized with UUID', uuid);

  // Start the "Eyes" and "Hands"
  analyzePage(uuid);

  // Start the "Whisperer"
  connectWebSocket(uuid);
};

// --- The Eyes & Hands ---
async function analyzePage(uuid) {
  try {
    const htmlContent = document.documentElement.outerHTML.slice(0, 50000);
    const currentUrl = window.location.href;

    const response = await chrome.runtime.sendMessage({
      type: 'apiRequest',
      path: '/analyze',
      options: {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: currentUrl,
          html_content: htmlContent,
          user_id: uuid,
          metadata: {
            source: 'content-script',
            captured_at: new Date().toISOString()
          }
        })
      }
    });

    if (!response?.ok) {
      throw new Error(`Analysis failed: ${response?.status || 'unknown'}`);
    }

    applyDOMManipulations(response.data || {});

  } catch (error) {
    console.error('FlowState Analysis Error:', error);
  }
}

function applyDOMManipulations(data) {
  // Handle actions array (from popup execution)
  if (data.actions && Array.isArray(data.actions)) {
    data.actions.forEach(action => {
      const type = (action?.type || '').toLowerCase();
      
      if (type === 'hide' || type.includes('hide')) {
        const selector = action.selector || action.target;
        if (selector) {
          try {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => el.style.display = 'none');
            console.log(`✓ Hidden: ${selector} (${elements.length} elements)`);
          } catch (e) {
            console.warn(`Invalid hide selector: ${selector}`, e);
          }
        }
      }
      
      if (type === 'highlight' || type.includes('highlight')) {
        const selector = action.selector || action.target;
        if (selector) {
          try {
            const elements = document.querySelectorAll(selector);
            
            // Add highlight class to selected elements
            elements.forEach(el => {
              el.classList.add('flowstate-highlight');
            });
            
            // Dim everything else
            dimNonHighlightedElements();
            
            console.log(`✓ Highlighted: ${selector} (${elements.length} elements)`);
          } catch (e) {
            console.warn(`Invalid highlight selector: ${selector}`, e);
          }
        }
      }
      
      if (type === 'scroll' || type.includes('scroll')) {
        const selector = action.selector || action.target;
        if (selector) {
          try {
            const element = document.querySelector(selector);
            if (element) {
              element.scrollIntoView({ behavior: 'smooth', block: 'center' });
              console.log(`✓ Scrolled to: ${selector}`);
            }
          } catch (e) {
            console.warn(`Invalid scroll selector: ${selector}`, e);
          }
        } else if (action.y !== undefined) {
          window.scrollTo({ top: action.y, behavior: 'smooth' });
          console.log(`✓ Scrolled to y: ${action.y}`);
        }
      }
    });
    return;
  }
  
  // Legacy: Hide selectors
  if (data.hide_selectors && Array.isArray(data.hide_selectors)) {
    data.hide_selectors.forEach(selector => {
      try {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => el.style.display = 'none');
      } catch (e) {
        console.warn(`Invalid hide selector: ${selector}`, e);
      }
    });
  }

  // Legacy: Highlight selectors
  if (data.highlight_selectors && Array.isArray(data.highlight_selectors)) {
    data.highlight_selectors.forEach(selector => {
      try {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => el.classList.add('flowstate-highlight'));
      } catch (e) {
        console.warn(`Invalid highlight selector: ${selector}`, e);
      }
    });
  }
}

// --- The Whisperer ---
let socket = null;
let reconnectInterval = 5000;

function connectWebSocket(uuid) {
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    return;
  }

  socket = new WebSocket(`ws://localhost:8000/chat/${uuid}`);

  socket.onopen = () => {
    console.log('FlowState: WebSocket connected');
  };

  socket.onmessage = (event) => {
    try {
      // Expecting text or JSON. If it's a simple string message, display it.
      // If it's JSON, you might want to parse it. 
      // For now, assuming the message data itself is the notification text.
      const message = event.data;
      showToast(message);
    } catch (e) {
      console.error('Error handling WebSocket message:', e);
    }
  };

  socket.onclose = () => {
    console.log('FlowState: WebSocket disconnected. Reconnecting in 5s...');
    setTimeout(() => connectWebSocket(uuid), reconnectInterval);
  };

  socket.onerror = (error) => {
    console.error('FlowState: WebSocket error:', error);
    socket.close(); // Ensure onclose triggers
  };
}

// Dim all elements except highlighted ones
function dimNonHighlightedElements() {
  // Get all direct children of body
  const bodyChildren = Array.from(document.body.children);
  
  bodyChildren.forEach(child => {
    // Skip if it's a FlowState element (overlay, toast, etc)
    if (child.id && child.id.startsWith('flowstate-')) {
      return;
    }
    
    // Skip if this element or any of its children are highlighted
    const hasHighlight = child.classList.contains('flowstate-highlight') || 
                        child.querySelector('.flowstate-highlight');
    
    if (!hasHighlight) {
      child.classList.add('flowstate-dimmed');
    } else {
      // For elements that contain highlights, dim their direct children that aren't highlighted
      dimChildrenRecursively(child);
    }
  });
}

// Recursively dim children that aren't highlighted
function dimChildrenRecursively(element) {
  Array.from(element.children).forEach(child => {
    const isHighlighted = child.classList.contains('flowstate-highlight');
    const hasHighlightedChild = child.querySelector('.flowstate-highlight');
    
    if (!isHighlighted && !hasHighlightedChild) {
      child.classList.add('flowstate-dimmed');
    } else if (hasHighlightedChild) {
      dimChildrenRecursively(child);
    }
  });
}

// --- Execution Overlay Animation ---
function showExecutionOverlay() {
  let overlay = document.getElementById('flowstate-execution-overlay');
  if (!overlay) {
    overlay = document.createElement('div');
    overlay.id = 'flowstate-execution-overlay';
    document.body.appendChild(overlay);
  }

  // Trigger animation
  requestAnimationFrame(() => {
    overlay.classList.add('active');
  });

  // Auto-fade after 2.5 seconds
  setTimeout(() => {
    overlay.classList.remove('active');
    // Remove from DOM after transition
    setTimeout(() => {
      if (overlay.parentNode) {
        overlay.parentNode.removeChild(overlay);
      }
    }, 300);
  }, 2500);
}

// --- Toast Notification ---
function showToast(message) {
  let container = document.getElementById('flowstate-toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'flowstate-toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = 'flowstate-toast';
  toast.textContent = message;

  container.appendChild(toast);

  // Trigger animation
  requestAnimationFrame(() => {
    toast.classList.add('show');
  });

  // Auto-fade after 10 seconds
  setTimeout(() => {
    toast.classList.remove('show');
    // Remove from DOM after transition
    setTimeout(() => {
      if (toast.parentNode) {
        toast.parentNode.removeChild(toast);
      }
      // Cleanup container if empty
      if (container.childNodes.length === 0) {
        container.remove();
      }
    }, 300); // Match CSS transition duration
  }, 10000);
}

// Don't start automatically - only execute when user triggers actions from popup
// init();
