// OnboardPage1.js - Step 1: Collect username and technique level

document.addEventListener('DOMContentLoaded', async () => {
  const usernameInput = document.getElementById('username');
  const levelButtons = document.querySelectorAll('.grid button');
  const continueBtn = document.querySelector('a[href="OnboardPage2.html"]');
  const skipBtn = document.querySelector('button');
  
  let selectedLevel = 'intermediate'; // Default selection

  // Load existing data if user comes back
  const storage = await chrome.storage.local.get('onboarding_step1');
  if (storage.onboarding_step1) {
    usernameInput.value = storage.onboarding_step1.username || '';
    selectedLevel = storage.onboarding_step1.technique_level || 'intermediate';
    updateSelectedLevel(selectedLevel);
  }

  // Handle level selection
  levelButtons.forEach((btn, index) => {
    const levels = ['beginner', 'intermediate', 'advanced', 'expert'];
    
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      selectedLevel = levels[index];
      updateSelectedLevel(selectedLevel);
    });
  });

  function updateSelectedLevel(level) {
    const levels = ['beginner', 'intermediate', 'advanced', 'expert'];
    levelButtons.forEach((btn, index) => {
      if (levels[index] === level) {
        btn.classList.add('border-2', 'border-primary', 'bg-primary/10', 'shadow-glow');
        btn.classList.remove('border', 'border-gray-200', 'dark:border-[#366348]');
        // Add checkmark
        if (!btn.querySelector('.absolute')) {
          const check = document.createElement('div');
          check.className = 'absolute top-2 right-2 text-primary';
          check.innerHTML = '<span class="material-symbols-outlined text-lg">check_circle</span>';
          btn.insertBefore(check, btn.firstChild);
        }
        // Make icon primary color
        const icon = btn.querySelector('.material-symbols-outlined:not(.text-lg)');
        icon.classList.remove('text-slate-400', 'dark:text-[#95c6a9]', 'group-hover:text-primary');
        icon.classList.add('text-primary');
        const text = btn.querySelector('span:last-child');
        text.classList.add('font-bold');
      } else {
        btn.classList.remove('border-2', 'border-primary', 'bg-primary/10', 'shadow-glow');
        btn.classList.add('border', 'border-gray-200', 'dark:border-[#366348]');
        // Remove checkmark
        const check = btn.querySelector('.absolute');
        if (check) check.remove();
        // Reset icon color
        const icon = btn.querySelector('.material-symbols-outlined:not(.text-lg)');
        icon.classList.add('text-slate-400', 'dark:text-[#95c6a9]', 'group-hover:text-primary');
        icon.classList.remove('text-primary');
        const text = btn.querySelector('span:last-child');
        text.classList.remove('font-bold');
      }
    });
  }

  // Save data and continue
  continueBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    
    const username = usernameInput.value.trim();
    
    // Save to storage
    await chrome.storage.local.set({
      onboarding_step1: {
        username: username,
        technique_level: selectedLevel
      }
    });
    
    // Navigate to next page
    window.location.href = 'OnboardPage2.html';
  });

  // Skip functionality
  skipBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    await chrome.storage.local.set({
      onboarding_step1: {
        username: '',
        technique_level: 'intermediate'
      }
    });
    window.location.href = 'OnboardPage2.html';
  });
});
