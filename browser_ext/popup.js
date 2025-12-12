document.addEventListener('DOMContentLoaded', async () => {
  const display = document.getElementById('uuid-display');
  const storage = await chrome.storage.local.get('user_uuid');
  
  if (storage.user_uuid) {
    display.textContent = 'UUID: ' + storage.user_uuid;
  } else {
    display.textContent = 'UUID not found';
  }
});
