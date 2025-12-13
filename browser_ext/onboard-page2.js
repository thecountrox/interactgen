// OnboardPage2.js - Step 2: Collect thinking style and main goal

document.addEventListener('DOMContentLoaded', async () => {
  const styleButtons = document.querySelectorAll('.grid button');
  const goalInput = document.querySelector('input[placeholder*="Deep Work"]');
  const continueBtn = document.querySelector('a[href="OnboardPage3.html"]');
  const backBtn = document.querySelector('a[href="OnboardPage1.html"]');
  
  let selectedStyle = 'visual'; // Default selection

  // Load existing data if user comes back
  const storage = await chrome.storage.local.get('onboarding_step2');
  if (storage.onboarding_step2) {
    goalInput.value = storage.onboarding_step2.goal || '';
    selectedStyle = storage.onboarding_step2.preference || 'visual';
    updateSelectedStyle(selectedStyle);
  }

  // Handle thinking style selection
  styleButtons.forEach((btn, index) => {
    const styles = ['analytical', 'visual', 'cautious'];
    
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      selectedStyle = styles[index];
      updateSelectedStyle(selectedStyle);
    });
  });

  function updateSelectedStyle(style) {
    const styles = ['analytical', 'visual', 'cautious'];
    styleButtons.forEach((btn, index) => {
      if (styles[index] === style) {
        btn.classList.add('border-2', 'border-primary', 'shadow-[0_4px_20px_rgba(34,197,94,0.1)]');
        btn.classList.remove('border', 'border-white/5');
        // Add checkmark if not exists
        if (!btn.querySelector('.absolute')) {
          const check = document.createElement('div');
          check.className = 'absolute top-3 right-3 w-6 h-6 bg-primary rounded-full flex items-center justify-center shadow-sm';
          check.innerHTML = '<span class="material-symbols-outlined text-black text-sm font-bold">check</span>';
          btn.insertBefore(check, btn.firstChild);
        }
        // Update icon background
        const iconBg = btn.querySelector('.w-12.h-12');
        iconBg.classList.add('bg-primary/20');
        iconBg.classList.remove('bg-[#1f2e23]');
        const icon = iconBg.querySelector('.material-symbols-outlined');
        icon.classList.add('text-primary');
        icon.classList.remove('text-[#A5B4A8]');
        const text = btn.querySelector('p');
        text.classList.add('font-bold');
      } else {
        btn.classList.remove('border-2', 'border-primary', 'shadow-[0_4px_20px_rgba(34,197,94,0.1)]');
        btn.classList.add('border', 'border-white/5');
        // Remove checkmark
        const check = btn.querySelector('.absolute');
        if (check) check.remove();
        // Reset icon background
        const iconBg = btn.querySelector('.w-12.h-12');
        iconBg.classList.remove('bg-primary/20');
        iconBg.classList.add('bg-[#1f2e23]');
        const icon = iconBg.querySelector('.material-symbols-outlined');
        icon.classList.remove('text-primary');
        icon.classList.add('text-[#A5B4A8]');
        const text = btn.querySelector('p');
        text.classList.remove('font-bold');
      }
    });
  }

  // Save data and continue
  continueBtn.addEventListener('click', async (e) => {
    e.preventDefault();
    
    const goal = goalInput.value.trim();
    
    // Save to storage
    await chrome.storage.local.set({
      onboarding_step2: {
        preference: selectedStyle,
        goal: goal || 'General productivity'
      }
    });
    
    // Navigate to next page
    window.location.href = 'OnboardPage3.html';
  });
});
