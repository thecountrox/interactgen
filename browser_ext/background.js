chrome.runtime.onInstalled.addListener(async (details) => {
  if (details.reason === 'install') {
    // Generate a random UUID for the user
    const uuid = self.crypto.randomUUID();
    
    // Save to storage
    await chrome.storage.local.set({ user_uuid: uuid });
    console.log('Generated and saved user UUID:', uuid);

    // Open the onboarding Step 1 page (1/3 flow)
    chrome.tabs.create({ url: chrome.runtime.getURL("OnboardPage1.html") });
  }
});

// Proxy network requests to bypass page-level CORS for content scripts and popup
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type !== 'apiRequest') return;

  const baseUrl = 'http://localhost:8000';
  const { path, options = {} } = message;

  (async () => {
    try {
      const response = await fetch(`${baseUrl}${path}`, options);
      const rawText = await response.text();
      let data = rawText;
      try {
        data = JSON.parse(rawText);
      } catch (_err) {
        // Non-JSON response; keep raw text
      }

      sendResponse({
        ok: response.ok,
        status: response.status,
        data,
        headers: Object.fromEntries(response.headers.entries()),
      });
    } catch (error) {
      sendResponse({ ok: false, status: 0, error: error?.message || 'Network error' });
    }
  })();

  // Return true to indicate async response
  return true;
});
