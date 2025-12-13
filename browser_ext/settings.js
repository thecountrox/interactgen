// settings.js - Wire up Settings Dashboard with real data

// Helper: call backend
async function callBackend(path, options = {}) {
  const resp = await chrome.runtime.sendMessage({
    type: 'apiRequest',
    path,
    options,
  });

  if (!resp) {
    throw new Error('No response from background script');
  }

  return {
    ok: resp.ok,
    status: resp.status,
    json: async () => resp.data,
  };
}

// Get UUID and user profile
async function loadUserProfile() {
  const storage = await chrome.storage.local.get('user_uuid');
  const uuid = storage.user_uuid || 'unknown';
  
  // Update UUID display in sidebar
  const versionEl = document.querySelector('.text-\\[10px\\].text-slate-400');
  if (versionEl) {
    versionEl.textContent = `UUID: ${uuid.substring(0, 13)}...`;
    versionEl.title = uuid;
  }
  
  // Try to load profile from backend
  try {
    const resp = await callBackend(`/user-profile/${uuid}`, {
      method: 'GET',
    });
    
    if (resp.ok) {
      const profile = await resp.json();
      
      // Update username input
      const usernameInput = document.getElementById('username-input');
      if (usernameInput) {
        usernameInput.value = profile.username || '';
      }
      
      // Update user info in sidebar
      const sidebarName = document.getElementById('sidebar-username');
      if (sidebarName) {
        sidebarName.textContent = profile.username || 'User';
      }
      
      // Update profile section greeting
      const profileGreeting = document.getElementById('profile-username-greeting');
      if (profileGreeting && profile.username) {
        profileGreeting.textContent = `, ${profile.username}`;
      }
      
      // Update tech level if available
      if (profile.tech_level) {
        const levels = { 'beginner': 0, 'intermediate': 1, 'expert': 2 };
        const radios = document.querySelectorAll('input[name="tech_level"]');
        const index = levels[profile.tech_level.toLowerCase()] || 1;
        if (radios[index]) radios[index].checked = true;
      }
      
      // Update nudges toggle if available
      if (profile.preferences?.proactive_nudges !== undefined) {
        const toggle = document.querySelector('input[type="checkbox"]');
        if (toggle) toggle.checked = profile.preferences.proactive_nudges;
      }
      
      return { uuid, username: profile.username || 'User' };
    } else {
      // Profile doesn't exist, set defaults
      const sidebarName = document.getElementById('sidebar-username');
      if (sidebarName) sidebarName.textContent = 'User';
      
      return { uuid, username: 'User' };
    }
  } catch (e) {
    console.warn('Could not load profile:', e);
    const sidebarName = document.getElementById('sidebar-username');
    if (sidebarName) sidebarName.textContent = 'User';
    
    return { uuid, username: 'User' };
  }
}

// Load memory stats
async function loadMemoryStats(uuid) {
  try {
    const resp = await callBackend(`/user-memories/${uuid}?limit=100`, {
      method: 'GET',
    });
    
    if (resp.ok) {
      const data = await resp.json();
      const memories = data.memories || [];
      
      // Update total memories count
      const totalEl = document.querySelector('.text-3xl.font-bold');
      if (totalEl) {
        totalEl.textContent = memories.length.toLocaleString();
      }
      
      // Update last active (get most recent memory timestamp)
      if (memories.length > 0) {
        const lastMemory = memories[0];
        const timestamp = new Date(lastMemory.created_at || lastMemory.timestamp);
        const timeAgo = getTimeAgo(timestamp);
        const lastActiveEl = document.querySelectorAll('.text-3xl.font-bold')[1];
        if (lastActiveEl) {
          lastActiveEl.textContent = timeAgo;
        }
      }
    }
  } catch (e) {
    console.warn('Could not load memory stats:', e);
  }
}

// Load rate limit stats
async function loadRateLimitStats(uuid) {
  try {
    const resp = await callBackend(`/usage-stats/${uuid}`, {
      method: 'GET',
    });
    
    if (resp.ok) {
      const stats = await resp.json();
      
      // Update quota display
      const quotaText = document.querySelector('.text-xs.font-semibold.inline-block.text-slate-600');
      const progressBar = document.querySelector('.bg-primary.transition-all');
      const percentText = document.querySelector('.text-xs.font-semibold.inline-block.text-primary');
      
      if (stats.daily_limit && stats.daily_count !== undefined) {
        const used = stats.daily_count;
        const limit = stats.daily_limit;
        const percent = Math.round((used / limit) * 100);
        
        if (quotaText) quotaText.textContent = `${used} / ${limit}`;
        if (progressBar) progressBar.style.width = `${percent}%`;
        if (percentText) percentText.textContent = `${percent}% Used`;
      }
    }
  } catch (e) {
    console.warn('Could not load rate limit stats:', e);
  }
}

// Helper: time ago formatter
function getTimeAgo(date) {
  const seconds = Math.floor((new Date() - date) / 1000);
  
  const intervals = {
    year: 31536000,
    month: 2592000,
    week: 604800,
    day: 86400,
    hour: 3600,
    minute: 60
  };
  
  for (const [name, secondsInInterval] of Object.entries(intervals)) {
    const interval = Math.floor(seconds / secondsInInterval);
    if (interval >= 1) {
      return `${interval}${name[0]} ago`;
    }
  }
  
  return 'just now';
}

// Wire save button
function wireSaveButton(uuid) {
  const saveBtn = document.querySelector('button.bg-primary');
  if (!saveBtn) return;
  
  saveBtn.addEventListener('click', async () => {
    saveBtn.disabled = true;
    const originalText = saveBtn.textContent;
    saveBtn.textContent = 'Saving...';
    
    try {
      // Get username
      const usernameInput = document.getElementById('username-input');
      const username = usernameInput?.value?.trim() || '';
      
      if (!username) {
        saveBtn.textContent = 'Username required';
        setTimeout(() => {
          saveBtn.disabled = false;
          saveBtn.textContent = originalText;
        }, 2000);
        return;
      }
      
      // Get tech level
      const techLevelRadio = document.querySelector('input[name="tech_level"]:checked');
      let techLevel = 'intermediate';
      if (techLevelRadio) {
        const label = techLevelRadio.parentElement.querySelector('.font-medium');
        techLevel = label?.textContent?.trim().toLowerCase() || 'intermediate';
      }
      
      // Get proactive nudges toggle
      const nudgesToggle = document.querySelector('input[type="checkbox"]');
      const proactiveNudges = nudgesToggle?.checked || false;
      
      // Make API call
      const resp = await callBackend(`/user-profile/${uuid}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          username: username,
          tech_level: techLevel,
          preferences: { 
            proactive_nudges: proactiveNudges 
          }
        }),
      });
      
      if (resp.ok) {
        saveBtn.textContent = 'Saved ✓';
        
        // Update sidebar username
        const sidebarName = document.getElementById('sidebar-username');
        if (sidebarName) {
          sidebarName.textContent = username;
        }
        
        // Update profile section greeting
        const profileGreeting = document.getElementById('profile-username-greeting');
        if (profileGreeting) {
          profileGreeting.textContent = `, ${username}`;
        }
      } else {
        const errorData = await resp.json().catch(() => ({}));
        saveBtn.textContent = errorData.detail || 'Save Failed';
      }
    } catch (e) {
      console.error('Save failed:', e);
      saveBtn.textContent = 'Error Saving';
    } finally {
      setTimeout(() => {
        saveBtn.disabled = false;
        saveBtn.textContent = originalText;
      }, 2000);
    }
  });
}

// Wire clear memories button
function wireClearMemories(uuid) {
  const clearBtn = document.querySelector('button.bg-white.dark\\:bg-red-950');
  if (!clearBtn) return;
  
  clearBtn.addEventListener('click', async () => {
    if (!confirm('Are you sure you want to delete all memories? This cannot be undone.')) {
      return;
    }
    
    clearBtn.disabled = true;
    clearBtn.textContent = 'Clearing...';
    
    try {
      const resp = await callBackend(`/user-memories/${uuid}`, {
        method: 'DELETE',
      });
      
      if (resp.ok) {
        clearBtn.textContent = 'Cleared ✓';
        await loadMemoryStats(uuid);
      } else {
        clearBtn.textContent = 'Failed';
      }
    } catch (e) {
      console.error('Clear failed:', e);
      clearBtn.textContent = 'Error';
    } finally {
      setTimeout(() => {
        clearBtn.disabled = false;
        clearBtn.textContent = 'Clear All Memories';
      }, 2000);
    }
  });
}

// Handle navigation active states
function wireNavigation() {
  const navLinks = document.querySelectorAll('aside nav a');
  const mainContent = document.querySelector('main');
  let isUserScrolling = false;
  let scrollTimeout;
  
  // Function to update active state
  function setActiveLink(activeLink) {
    navLinks.forEach(link => {
      const isActive = link === activeLink;
      
      if (isActive) {
        // Active styles
        link.className = 'flex items-center gap-3 px-3 py-3 rounded-xl bg-primary/10 text-emerald-900 dark:text-emerald-100 relative overflow-hidden';
        
        // Add indicator if not present
        if (!link.querySelector('.absolute')) {
          const indicator = document.createElement('div');
          indicator.className = 'absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-primary rounded-r-full';
          link.insertBefore(indicator, link.firstChild);
        }
        
        // Update icon color
        const icon = link.querySelector('.material-symbols-outlined');
        if (icon) {
          icon.className = 'material-symbols-outlined text-emerald-700 dark:text-primary pl-1';
        }
        
        // Update text style
        const text = link.querySelector('span:last-child');
        if (text) {
          text.className = 'text-sm font-semibold';
        }
      } else {
        // Inactive styles
        link.className = 'flex items-center gap-3 px-3 py-3 rounded-xl text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-white/5 transition-colors group';
        
        // Remove indicator if present
        const indicator = link.querySelector('.absolute');
        if (indicator) indicator.remove();
        
        // Update icon color
        const icon = link.querySelector('.material-symbols-outlined');
        if (icon) {
          icon.className = 'material-symbols-outlined group-hover:text-primary transition-colors';
        }
        
        // Update text style
        const text = link.querySelector('span:last-child');
        if (text) {
          text.className = 'text-sm font-medium';
        }
      }
    });
  }
  
  // Function to find which section is currently in view
  function getCurrentSection() {
    const sections = Array.from(navLinks).map(link => {
      const href = link.getAttribute('href');
      return {
        id: href,
        element: document.querySelector(href),
        link: link
      };
    }).filter(s => s.element);
    
    // Check if scrolled to the very bottom of the page
    const isAtBottom = mainContent.scrollHeight - mainContent.scrollTop <= mainContent.clientHeight + 10;
    
    if (isAtBottom) {
      // Return the last section (Developer)
      return sections[sections.length - 1];
    }
    
    // Get the scroll position with some offset from top
    const scrollPos = mainContent.scrollTop + 100;
    
    // Find the section that's currently most visible
    for (let i = sections.length - 1; i >= 0; i--) {
      const section = sections[i];
      if (section.element.offsetTop <= scrollPos) {
        return section;
      }
    }
    
    // Default to first section
    return sections[0];
  }
  
  // Handle scroll events to update active state
  function handleScroll() {
    if (!isUserScrolling) {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => {
        const currentSection = getCurrentSection();
        if (currentSection) {
          setActiveLink(currentSection.link);
          history.replaceState(null, null, currentSection.id);
        }
      }, 50);
    }
  }
  
  // Set initial active state based on hash or default to profile
  const currentHash = window.location.hash || '#profile';
  const initialLink = Array.from(navLinks).find(link => link.getAttribute('href') === currentHash);
  if (initialLink) {
    setActiveLink(initialLink);
  }
  
  // Handle clicks
  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const targetId = link.getAttribute('href');
      
      // Disable scroll detection temporarily during programmatic scroll
      isUserScrolling = true;
      
      // Update active state
      setActiveLink(link);
      
      // Smooth scroll to section
      const targetSection = document.querySelector(targetId);
      if (targetSection) {
        targetSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
      
      // Update URL hash without jumping
      history.pushState(null, null, targetId);
      
      // Re-enable scroll detection after scroll completes
      setTimeout(() => {
        isUserScrolling = false;
      }, 1000);
    });
  });
  
  // Listen to scroll events on main content
  if (mainContent) {
    mainContent.addEventListener('scroll', handleScroll);
  }
  
  // Handle hash changes (back/forward navigation)
  window.addEventListener('hashchange', () => {
    const hash = window.location.hash || '#profile';
    const link = Array.from(navLinks).find(l => l.getAttribute('href') === hash);
    if (link) {
      setActiveLink(link);
      const targetSection = document.querySelector(hash);
      if (targetSection) {
        targetSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }
  });
}

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
  wireNavigation();
  const { uuid, username } = await loadUserProfile();
  await loadMemoryStats(uuid);
  await loadRateLimitStats(uuid);
  wireSaveButton(uuid);
  wireClearMemories(uuid);
  
  console.log('Settings dashboard initialized with UUID:', uuid, 'Username:', username);
});
