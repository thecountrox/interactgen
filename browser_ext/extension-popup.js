// extension-popup.js - Wire backend endpoints and popup functionality

let lastAnalysis = null;

// Helper: get current active tab URL
async function getActiveTabUrl() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    return tab?.url || '';
  } catch (e) {
    return '';
  }
}

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

// Escape text for safe HTML injection
function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function getToggleStates() {
  return {
    hide: document.getElementById('toggle-hide')?.checked !== false,
    highlight: document.getElementById('toggle-highlight')?.checked !== false,
    autoscroll: document.getElementById('toggle-autoscroll')?.checked !== false,
  };
}

function filterActions(actions = []) {
  const toggles = getToggleStates();
  return actions.filter((action) => {
    const type = (action?.type || '').toLowerCase();
    if (!toggles.hide && type.includes('hide')) return false;
    if (!toggles.highlight && type.includes('highlight')) return false;
    if (!toggles.autoscroll && (type.includes('scroll') || type.includes('auto-scroll'))) return false;
    return true;
  });
}

function renderActionsList(actions = []) {
  const list = document.getElementById('analysis-actions');
  if (!list) return;
  if (!actions.length) {
    list.classList.add('hidden');
    list.innerHTML = '';
    return;
  }

  list.innerHTML = actions.slice(0, 6).map((action, idx) => {
    const label = action?.description || action?.summary || action?.type || `Action ${idx + 1}`;
    const selector = action?.selector ? ` · ${action.selector}` : '';
    return `<div class="flex items-start gap-2 bg-surface-dark/40 border border-border-dark rounded px-3 py-2">
      <span class="material-symbols-outlined text-[14px] text-primary mt-[2px]">bolt</span>
      <div class="flex-1 min-w-0">
        <div class="text-gray-100 font-medium truncate">${escapeHtml(label)}</div>
        ${selector ? `<div class="text-[11px] text-text-secondary truncate">${escapeHtml(selector)}</div>` : ''}
      </div>
    </div>`;
  }).join('');

  list.classList.remove('hidden');
}

function updateExecuteButton() {
  const executeBtn = document.getElementById('execute-actions-btn');
  if (!executeBtn) return;
  const actions = filterActions(lastAnalysis?.actions || []);
  const count = actions.length;
  executeBtn.disabled = count === 0;
  executeBtn.classList.toggle('opacity-50', count === 0);
  executeBtn.innerHTML = `<span class="material-symbols-outlined text-[20px]">play_circle</span>${count ? `Execute ${count} Action${count === 1 ? '' : 's'}` : 'No Actions Available'}`;
}

// Get full HTML content of the active tab
async function getActiveTabHtml() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id) return '';
    const [{ result }] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => document.documentElement.outerHTML,
    });
    return result || '';
  } catch (e) {
    console.warn('Failed to get page HTML', e);
    return '';
  }
}

// Render UUID in footer
async function renderUUID() {
  const footerUuid = document.querySelector('footer .font-mono');
  const storage = await chrome.storage.local.get('user_uuid');
  const uuid = storage.user_uuid || 'unknown';
  if (footerUuid) {
    footerUuid.textContent = `UUID: ${uuid.substring(0, 8)}...`;
    footerUuid.title = uuid;
  }
  return uuid;
}

// Execute Suggested Actions button
function wireExecuteActions(uuid) {
  const executeBtn = document.getElementById('execute-actions-btn');
  if (!executeBtn) return;

  executeBtn.addEventListener('click', async () => {
    executeBtn.disabled = true;
    executeBtn.classList.add('opacity-70');
    try {
      const filtered = filterActions(lastAnalysis?.actions || []);
      if (!filtered.length) {
        executeBtn.textContent = 'No Actions to Run';
        return;
      }
      
      // Send actions to content script to execute in current tab
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab?.id) {
        executeBtn.textContent = 'No Active Tab';
        return;
      }
      
      // Check if it's a restricted page
      const url = tab.url || '';
      if (url.startsWith('chrome://') || url.startsWith('about:') || url.startsWith('chrome-extension://')) {
        executeBtn.textContent = 'Cannot Run on This Page';
        return;
      }
      
      try {
        await chrome.tabs.sendMessage(tab.id, {
          type: 'executeActions',
          actions: filtered
        });
        executeBtn.textContent = 'Actions Executed ✓';
      } catch (msgError) {
        console.warn('Content script not loaded, injecting...', msgError);
        // Try to inject content script if not already loaded
        try {
          await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            files: ['content.js']
          });
          // Retry sending message
          await chrome.tabs.sendMessage(tab.id, {
            type: 'executeActions',
            actions: filtered
          });
          executeBtn.textContent = 'Actions Executed ✓';
        } catch (injectError) {
          executeBtn.textContent = 'Cannot Access Page';
          console.error('Failed to inject content script:', injectError);
        }
      }
    } catch (e) {
      executeBtn.textContent = 'Error Running Actions';
      console.error(e);
    } finally {
      setTimeout(() => {
        executeBtn.disabled = false;
        executeBtn.classList.remove('opacity-70');
        updateExecuteButton();
      }, 3000);
    }
  });
}

// Populate Analysis section with sample data from backend
async function wireAnalysis(uuid) {
  const section = document.querySelector('section:nth-of-type(1)');
  if (!section) return;
  const url = await getActiveTabUrl();
  console.log('wireAnalysis: url=', url);
  const html = await getActiveTabHtml();
  console.log('wireAnalysis: html length=', html.length);
  const loader = section.querySelector('#analysis-loader');
  const paragraph = section.querySelector('#analysis-text');
  const chips = section.querySelector('#analysis-chips');
  const actionsList = section.querySelector('#analysis-actions');
  const btn = section.querySelector('#analyze-btn');
  
  // Show loader, hide results
  if (loader) loader.classList.remove('hidden');
  if (paragraph) paragraph.classList.add('hidden');
  if (chips) chips.classList.add('hidden');
  if (btn) btn.classList.add('hidden');
  
  try {
    const payload = {
      url,
      html_content: html,
      user_id: uuid,
      metadata: { timestamp: new Date().toISOString(), viewport: 'extension-popup' }
    };
    console.log(payload)
    console.log('Posting /analyze payload', { url: payload.url, html_len: payload.html_content.length });
    const resp = await callBackend('/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    console.log('/analyze response status', resp.status);
    if (resp.ok) {
      const data = await resp.json();
      console.log('/analyze response data', data);
      lastAnalysis = data;
      if (paragraph && Array.isArray(data.suggestions) && data.suggestions.length) {
        paragraph.innerHTML = data.suggestions[0];
        paragraph.classList.remove('hidden');
      }
      // Reflect a simple status from actions length
      if (chips && Array.isArray(data.actions)) {
        const complexity = data.actions.length > 3 ? 'Advanced' : 'Moderate';
        chips.innerHTML = `
          <div class="flex items-center gap-1.5 px-2.5 py-1 rounded bg-purple-500/10 border border-purple-500/20">
            <span class="material-symbols-outlined text-purple-400 text-[14px]">psychology</span>
            <span class="text-xs font-medium text-purple-400">Complexity: ${complexity}</span>
          </div>
          <div class="flex items-center gap-1.5 px-2.5 py-1 rounded bg-orange-500/10 border border-orange-500/20">
            <span class="material-symbols-outlined text-orange-400 text-[14px]">warning</span>
            <span class="text-xs font-medium text-orange-400">Actions: ${data.actions.length}</span>
          </div>`;
        chips.classList.remove('hidden');
      }
      renderActionsList(filterActions(data.actions || []));
      if (loader) loader.classList.add('hidden');
      if (btn) btn.classList.remove('hidden');
      updateExecuteButton();
    } else {
      console.error('/analyze returned non-ok status', resp.status);
      if (paragraph) {
        paragraph.innerHTML = 'Error analyzing page. Status: ' + resp.status;
        paragraph.classList.remove('hidden');
      }
      lastAnalysis = null;
      renderActionsList([]);
      updateExecuteButton();
      if (loader) loader.classList.add('hidden');
    }
  } catch (e) {
    console.error('Analyze call failed', e);
    if (paragraph) {
      paragraph.innerHTML = 'Error: ' + e.message;
      paragraph.classList.remove('hidden');
    }
    lastAnalysis = null;
    renderActionsList([]);
    updateExecuteButton();
    if (loader) loader.classList.add('hidden');
  }
}

// Wire manual Analyze button
function wireAnalyzeButton(uuid) {
  const btn = document.querySelector('#analyze-btn');
  if (!btn) return;
  btn.addEventListener('click', async () => {
    btn.disabled = true;
    const loader = document.querySelector('#analysis-loader');
    const paragraph = document.querySelector('#analysis-text');
    const chips = document.querySelector('#analysis-chips');
    const actionsList = document.querySelector('#analysis-actions');
    if (loader) loader.classList.remove('hidden');
    if (paragraph) paragraph.classList.add('hidden');
    if (chips) chips.classList.add('hidden');
    if (actionsList) actionsList.classList.add('hidden');
    await wireAnalysis(uuid);
    btn.disabled = false;
  });
}

function wireToggles() {
  const toggles = ['toggle-hide', 'toggle-highlight', 'toggle-autoscroll'];
  toggles.forEach((id) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener('change', () => {
      renderActionsList(filterActions(lastAnalysis?.actions || []));
      updateExecuteButton();
    });
  });
}

// Init
document.addEventListener('DOMContentLoaded', async () => {
  const uuid = await renderUUID();
  wireToggles();
  updateExecuteButton();
  wireExecuteActions(uuid);
  wireAnalyzeButton(uuid);
  wireAnalysis(uuid);
  
  // Wire settings link
  const settingsLink = document.getElementById('settings-link');
  if (settingsLink) {
    settingsLink.addEventListener('click', () => {
      chrome.tabs.create({ url: chrome.runtime.getURL('SettingsDashboard.html') });
    });
  }
});
