// extension-popup.js - Wire backend endpoints and popup functionality

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
  const btn = document.querySelector('button:has(span.material-symbols-outlined:text-content("play_circle"))');
  // Fallback: select by text
  const fallbackBtn = document.querySelector('button');
  const executeBtn = btn || fallbackBtn;
  if (!executeBtn) return;

  executeBtn.addEventListener('click', async () => {
    executeBtn.disabled = true;
    executeBtn.classList.add('opacity-70');
    try {
      const url = await getActiveTabUrl();
      const payload = {
        url: url,
        user_id: uuid,
        actions: [
          // Example actions; in a real case, these would be fetched from analyze
          { type: 'highlight', selector: 'button, a[href]' },
        ],
        headless: false,
      };
      const resp = await callBackend('/api/execute-actions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (resp.ok) {
        executeBtn.textContent = 'Actions Executed ✓';
      } else {
        executeBtn.textContent = 'Failed to Execute';
      }
    } catch (e) {
      executeBtn.textContent = 'Error Running Actions';
      console.error(e);
    } finally {
      setTimeout(() => {
        executeBtn.disabled = false;
        executeBtn.classList.remove('opacity-70');
        executeBtn.innerHTML = '<span class="material-symbols-outlined text-[20px]">play_circle</span>Execute Suggested Actions';
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
      if (loader) loader.classList.add('hidden');
      if (btn) btn.classList.remove('hidden');
    } else {
      console.error('/analyze returned non-ok status', resp.status);
      if (paragraph) {
        paragraph.innerHTML = 'Error analyzing page. Status: ' + resp.status;
        paragraph.classList.remove('hidden');
      }
      if (loader) loader.classList.add('hidden');
    }
  } catch (e) {
    console.error('Analyze call failed', e);
    if (paragraph) {
      paragraph.innerHTML = 'Error: ' + e.message;
      paragraph.classList.remove('hidden');
    }
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
    if (loader) loader.classList.remove('hidden');
    if (paragraph) paragraph.classList.add('hidden');
    if (chips) chips.classList.add('hidden');
    await wireAnalysis(uuid);
  });
}

// Init
document.addEventListener('DOMContentLoaded', async () => {
  const uuid = await renderUUID();
  wireExecuteActions(uuid);
  wireAnalyzeButton(uuid);
  wireAnalysis(uuid);
});
