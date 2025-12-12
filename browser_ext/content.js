// content.js

// Ensure we run only after the page is fully loaded
const init = async () => {
  if (document.readyState === 'loading') {
    await new Promise(resolve => window.addEventListener('load', resolve));
  }

  // Get the user's UUID
  const storage = await chrome.storage.local.get('user_uuid');
  const uuid = storage.user_uuid;

  if (!uuid) {
    console.warn('InteractGen: No User UUID found. Please complete onboarding.');
    return;
  }

  // Start the "Eyes" and "Hands"
  analyzePage(uuid);

  // Start the "Whisperer"
  connectWebSocket(uuid);
};

// --- The Eyes & Hands ---
async function analyzePage(uuid) {
  try {
    const textContent = document.body.innerText.substring(0, 5000);
    const currentUrl = window.location.href;

    const response = await fetch('http://localhost:8000/analyze', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        uuid: uuid,
        url: currentUrl,
        content: textContent
      })
    });

    if (!response.ok) {
      throw new Error(`Analysis failed: ${response.status}`);
    }

    const data = await response.json();
    applyDOMManipulations(data);

  } catch (error) {
    console.error('InteractGen Analysis Error:', error);
  }
}

function applyDOMManipulations(data) {
  // Hide selectors
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

  // Highlight selectors
  if (data.highlight_selectors && Array.isArray(data.highlight_selectors)) {
    data.highlight_selectors.forEach(selector => {
      try {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => el.classList.add('interactgen-highlight'));
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
    console.log('InteractGen: WebSocket connected');
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
    console.log('InteractGen: WebSocket disconnected. Reconnecting in 5s...');
    setTimeout(() => connectWebSocket(uuid), reconnectInterval);
  };

  socket.onerror = (error) => {
    console.error('InteractGen: WebSocket error:', error);
    socket.close(); // Ensure onclose triggers
  };
}

// --- Toast Notification ---
function showToast(message) {
  let container = document.getElementById('interactgen-toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'interactgen-toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = 'interactgen-toast';
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

// Start everything
init();
