document.addEventListener('DOMContentLoaded', async () => {
  const form = document.getElementById('onboarding-form');
  const statusDiv = document.getElementById('status');

  // Retrieve the UUID generated in background.js
  const storage = await chrome.storage.local.get('user_uuid');
  const uuid = storage.user_uuid;

  if (!uuid) {
    statusDiv.textContent = 'Error: User UUID not found. Please reinstall the extension.';
    statusDiv.style.color = 'red';
    return;
  }

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    statusDiv.textContent = 'Saving...';
    statusDiv.style.color = 'black';

    const formData = {
      uuid: uuid,
      technique_level: document.getElementById('technique_level').value,
      goal: document.getElementById('goal').value,
      preference: document.getElementById('preference').value
    };

    try {
      // 1. Save to local storage
      await chrome.storage.local.set({ user_profile: formData });

      // 2. Send to backend
      const response = await fetch('http://localhost:8000/user/onboard', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        statusDiv.textContent = 'Profile saved successfully! You can close this tab.';
        statusDiv.style.color = 'green';
      } else {
        statusDiv.textContent = 'Failed to sync with server. Saved locally.';
        statusDiv.style.color = 'orange';
      }
    } catch (error) {
      console.error('Onboarding error:', error);
      statusDiv.textContent = 'Error saving profile: ' + error.message;
      statusDiv.style.color = 'red';
    }
  });
});
