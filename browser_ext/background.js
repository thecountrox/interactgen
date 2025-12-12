chrome.runtime.onInstalled.addListener(async (details) => {
  if (details.reason === 'install') {
    // Generate a random UUID for the user
    const uuid = self.crypto.randomUUID();
    
    // Save to storage
    await chrome.storage.local.set({ user_uuid: uuid });
    console.log('Generated and saved user UUID:', uuid);

    // Open the onboarding page
    chrome.tabs.create({ url: chrome.runtime.getURL("onboarding.html") });
  }
});
