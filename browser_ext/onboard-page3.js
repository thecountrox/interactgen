// OnboardPage3.js - Step 3: Submit all data to backend

document.addEventListener('DOMContentLoaded', async () => {
  const userIdDisplay = document.querySelector('.font-mono');
  const copyBtn = document.querySelector('button[class*="h-11"]');
  const dashboardBtn = document.querySelector('a[href="SettingsDashboard.html"]');
  const closeTabBtn = document.getElementById('close-tab');
  const statusIndicator = document.querySelector('.text-white\\/50');
  
  // Get or generate UUID
  let storage = await chrome.storage.local.get('user_uuid');
  let uuid = storage.user_uuid;
  
  if (!uuid) {
    uuid = self.crypto.randomUUID();
    await chrome.storage.local.set({ user_uuid: uuid });
  }
  
  // Display UUID
  const displayId = `FS-${uuid.substring(0, 4).toUpperCase()}-${uuid.substring(9, 11).toUpperCase()}-${uuid.substring(14, 17)}`;
  userIdDisplay.textContent = displayId;
  
  // Copy UUID functionality
  copyBtn.addEventListener('click', async () => {
    await navigator.clipboard.writeText(uuid);
    const icon = copyBtn.querySelector('.material-symbols-outlined');
    const originalIcon = icon.textContent;
    icon.textContent = 'check';
    setTimeout(() => {
      icon.textContent = originalIcon;
    }, 2000);
  });
  
  // Collect all onboarding data
  const step1 = await chrome.storage.local.get('onboarding_step1');
  const step2 = await chrome.storage.local.get('onboarding_step2');
  
  const formData = {
    uuid: uuid,
    username: step1.onboarding_step1?.username || '',
    technique_level: step1.onboarding_step1?.technique_level || 'intermediate',
    preference: step2.onboarding_step2?.preference || 'visual',
    goal: step2.onboarding_step2?.goal || 'General productivity'
  };
  
  // Submit to backend
  try {
    statusIndicator.textContent = 'Syncing...';
    
    // Save to local storage
    await chrome.storage.local.set({ user_profile: formData });
    
    // Send to backend
    const response = await chrome.runtime.sendMessage({
      type: 'apiRequest',
      path: '/user/onboard',
      options: {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      }
    });

    if (response?.ok) {
      statusIndicator.textContent = 'Connected ✓';
      statusIndicator.classList.remove('text-white/50');
      statusIndicator.classList.add('text-primary');
      
      // Clear onboarding steps from storage
      await chrome.storage.local.remove(['onboarding_step1', 'onboarding_step2']);
      
      console.log('Onboarding completed successfully');
    } else {
      statusIndicator.textContent = 'Saved Locally';
      statusIndicator.classList.add('text-yellow-500');
      console.warn('Failed to sync with server, saved locally');
    }
  } catch (error) {
    console.error('Onboarding error:', error);
    statusIndicator.textContent = 'Saved Locally';
    statusIndicator.classList.add('text-yellow-500');
  }
  
  // Close tab functionality
  closeTabBtn.addEventListener('click', () => {
    window.close();
  });
  
  // Open Dashboard page when clicked
  dashboardBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    const url = chrome.runtime.getURL('SettingsDashboard.html');
    try {
      await chrome.tabs.create({ url });
    } catch (err) {
      // Fallback: navigate current page if tabs API restricted
      window.location.href = 'SettingsDashboard.html';
    }
  });
});
