// CamouFlow SPA - Application Controller
const API = '/api';
let currentPage = 'dashboard';
let logSocket = null;
let stateCache = { profiles: [], browserSettings: {}, proxies: [] };

// ========== Navigation ==========
function navigate(page) {
  currentPage = page;
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  const pageEl = document.getElementById('page-' + page);
  if (pageEl) pageEl.classList.add('active');
  const navBtn = document.querySelector(`.nav-btn[data-page="${page}"]`);
  if (navBtn) navBtn.classList.add('active');
  loadPage(page);
}
document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => navigate(btn.dataset.page));
});

// ========== Toast ==========
function toast(msg) {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = 'toast'; el.textContent = msg;
  container.appendChild(el);
  setTimeout(() => { el.remove(); }, 3000);
}

// ========== Modal ==========
function showModal(title, bodyHtml, onSave) {
  const modal = document.getElementById('modal');
  const content = document.getElementById('modal-content');
  content.innerHTML = '<h2>' + title + '</h2>' + bodyHtml +
    '<div class="modal-footer">' +
    '<button class="btn btn-ghost" onclick="closeModal()">Cancel</button>' +
    '<button class="btn btn-primary" id="modal-save">Save</button></div>';
  document.getElementById('modal-save').addEventListener('click', () => { onSave(); closeModal(); });
  modal.classList.add('show');
}
function closeModal() { document.getElementById('modal').classList.remove('show'); }
document.getElementById('modal').addEventListener('click', e => { if (e.target === e.currentTarget) closeModal(); });

// ========== HTTP helpers ==========
async function apiGet(path) { const r = await fetch(API + path); return r.json(); }
async function apiPost(path, body) { const r = await fetch(API + path, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) }); return r.json(); }
async function apiPut(path, body) { const r = await fetch(API + path, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body || {}) }); return r.json(); }
async function apiDelete(path) { const r = await fetch(API + path, { method: 'DELETE' }); return r.json(); }

// ========== Log streaming ==========
function connectLogs() {
  if (logSocket) { logSocket.close(); }
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  logSocket = new WebSocket(proto + '//' + location.host + API + '/logs/stream');
  logSocket.onmessage = (e) => {
    const output = document.getElementById('logs-output');
    if (output && currentPage === 'logs') {
      output.textContent += e.data + '\n';
      output.scrollTop = output.scrollHeight;
      // Trim if too long
      if (output.textContent.length > 50000) {
        output.textContent = output.textContent.slice(-25000);
      }
    }
  };
  logSocket.onclose = () => { setTimeout(connectLogs, 3000); };
}
connectLogs();

// ========== Page loader ==========
function loadPage(page) {
  switch(page) {
    case 'dashboard': loadDashboard(); break;
    case 'profiles': loadProfiles(); break;
    case 'browser': loadBrowser(); break;
    case 'proxies': loadProxies(); break;
    case 'logs': loadLogs(); break;
    case 'settings': loadSettings(); break;
  }
}

// ===== DASHBOARD =====
async function loadDashboard() {
  const d = await apiGet('/dashboard');
  const metrics = d.metrics || {};
  const grid = document.getElementById('stat-grid');
  const items = [
    ['Profiles', metrics.profiles || 0, 'profiles'],
    ['Running', metrics.running || 0, 'profiles'],
    ['Proxies', metrics.proxy_total || 0, 'proxies'],
  ];
  grid.innerHTML = items.map(i => `<div class="stat-card"><div class="stat-value">${i[1]}</div><div class="stat-label">${i[0]}</div></div>`).join('');
  const feed = document.getElementById('activity-feed');
  const activity = d.activity || [];
  feed.innerHTML = activity.length ? activity.map(l => `<div class="act-line">${escHtml(l)}</div>`).join('') : '<div class="act-line">No activity yet</div>';
}

// ===== PROFILES =====
async function loadProfiles() {
  stateCache.profiles = await apiGet('/profiles');
  const stages = await apiGet('/profiles/stages');
  const filter = document.getElementById('profiles-stage-filter');
  filter.innerHTML = '<button class="btn btn-sm active" data-stage="" onclick="profilesFilter(this)">All tags</button>' +
    stages.map(s => `<button class="btn btn-sm" data-stage="${escHtml(s.name)}" onclick="profilesFilter(this)">${escHtml(s.name)} (${s.count})</button>`).join('');
  renderProfilesTable(stateCache.profiles);
}
async function profilesFilter(btn) {
  document.querySelectorAll('#profiles-stage-filter .btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const stage = btn.dataset.stage;
  const data = stage ? await apiGet('/profiles?stage=' + encodeURIComponent(stage)) : await apiGet('/profiles');
  stateCache.profiles = data;
  renderProfilesTable(data);
}
function renderProfilesTable(rows) {
  const tbody = document.getElementById('profiles-table');
  tbody.innerHTML = rows.map(r => {
    const cdpInfo = r.running && r.cdp_url
      ? `<a href="${r.cdp_url}" target="_blank" class="tag" style="background:rgba(6,182,212,0.18);color:#67e8f9;text-decoration:none;cursor:pointer" title="Open CDP DevTools">CDP :${r.cdp_port}</a>` + (r.vnc_port ? ` <a href="/static/vnc_viewer.html?host=${location.hostname}&port=${r.ws_port}&profile=${encodeURIComponent(r.name)}" target="_blank" class="tag" style="background:rgba(168,85,247,0.18);color:#c084fc;text-decoration:none;cursor:pointer" title="Remote view via VNC">View</a>` : "")
      : '';
    return `<tr>
    <td><strong>${escHtml(r.name)}</strong>${cdpInfo}</td>
    <td class="id-col">${escHtml(r.id)}</td>
    <td>${escHtml(r.browser)}</td>
    <td>${escHtml(r.proxy)}</td>
    <td><span class="tag">${escHtml(r.stage)}</span></td>
    <td><span class="running-dot ${r.running ? 'on' : 'off'}"></span>${escHtml(r.status)}</td>
    <td class="btn-group">
      ${r.running ? `<button class="btn btn-sm btn-danger" onclick="profilesStop('${escJs(r.name)}')">Stop</button>` : `<button class="btn btn-sm btn-success" onclick="profilesStart('${escJs(r.name)}')">Start</button>`}
      <button class="btn btn-sm" onclick="profilesEdit('${escJs(r.name)}')">Edit</button>
      <button class="btn btn-sm btn-danger" onclick="profilesDelete('${escJs(r.name)}')">Delete</button>
    </td></tr>`;
  }).join('');
}
async function profilesCreate() { const r = await apiPost('/profiles/create'); if (r.ok) { toast('Profile created'); loadProfiles(); } }
function profilesRefresh() { loadProfiles(); }
async function profilesStart(name) { const r = await apiPost('/profiles/' + encodeURIComponent(name) + '/start'); if (r.cdp_port > 0) { toast('Starting ' + name + ' 鈥?CDP port ' + r.cdp_port + (r.headless === false ? ' (visible)' : '')); } else { toast('Starting ' + name); } setTimeout(loadProfiles, 800); }
async function profilesStop(name) { await apiPost('/profiles/' + encodeURIComponent(name) + '/stop'); toast('Stopping ' + name); setTimeout(loadProfiles, 500); }
async function profilesDelete(name) { if (confirm('Delete profile ' + name + '?')) { await apiDelete('/profiles/' + encodeURIComponent(name)); toast('Deleted ' + name); loadProfiles(); } }
async function profilesEdit(name) {
  if (!stateCache.proxyPools) {
    var pps = await apiGet('/proxies');
    stateCache.proxyPools = pps || [];
  }
  const p = await apiGet('/profiles/' + encodeURIComponent(name));
  if (!p.name) return;
  var proxyOpts = '<option value="">Direct / none</option>';
  var assignedProxy = false;
  stateCache.proxyPools.forEach(function(pool) {
    (pool.proxies || []).forEach(function(px) {
      var assigned = (px.assigned_to || '').split(',').map(function(s) { return s.trim(); });
      if (pool.name === p.proxy_pool && assigned.indexOf(p.name) >= 0) assignedProxy = true;
    });
  });
  stateCache.proxyPools.forEach(function(pool) {
    proxyOpts += '<option value="pool:' + escHtml(pool.name) + '" ' + (pool.name === p.proxy_pool && !assignedProxy ? 'selected' : '') + '>Auto from pool: ' + escHtml(pool.name) + '</option>';
    (pool.proxies || []).forEach(function(px, idx) {
      var assigned = (px.assigned_to || '').split(',').map(function(s) { return s.trim(); });
      var selected = pool.name === p.proxy_pool && assigned.indexOf(p.name) >= 0 ? 'selected' : '';
      var label = px.name || ('Proxy #' + (idx + 1));
      var meta = [px.value, px.country, px.region, px.tags].filter(Boolean).join(' / ');
      proxyOpts += '<option value="proxy:' + escHtml(pool.name) + ':' + idx + '" ' + selected + '>' + escHtml(pool.name) + ' / ' + escHtml(label) + (meta ? ' (' + escHtml(meta) + ')' : '') + '</option>';
    });
  });
  showModal('Edit Profile: ' + name, `
    <div class="form-row"><div class="form-group"><label>Name</label><input id="pe-name" value="${escHtml(p.name)}"></div>
    <div class="form-group"><label>Stage (comma separated)</label><input id="pe-stage" value="${escHtml(p.stage)}" placeholder="Warmup, Ready"></div></div>
    <div class="form-row"><div class="form-group"><label>Engine</label><select id="pe-engine"><option value="camoufox" ${p.engine==='camoufox'?'selected':''}>Camoufox</option><option value="cloakbrowser" ${p.engine==='cloakbrowser'?'selected':''}>CloakBrowser</option></select></div></div>
    <div class="card-title">Proxy</div>
    <div class="form-group"><label>Proxy</label><select id="pe-pproxy">${proxyOpts}</select></div>
    <div class="form-row"><div class="form-group"><label>Scheme</label><select id="pe-pscheme"><option value="socks5" ${(p.proxy_scheme||'socks5')!=='http'?'selected':''}>SOCKS5</option><option value="http" ${(p.proxy_scheme||'socks5')==='http'?'selected':''}>HTTP</option></select></div>
    <div class="form-group"><label>Host</label><input id="pe-phost" value="${escHtml(p.proxy_host||'')}"></div></div>
    <div class="form-row"><div class="form-group"><label>Port</label><input id="pe-pport" value="${escHtml(p.proxy_port||'')}" type="number"></div>
    <div class="form-group"><label>Username</label><input id="pe-puser" value="${escHtml(p.proxy_user||'')}"></div></div>
    <div class="form-group"><label>Password</label><input id="pe-ppass" type="password" value="${escHtml(p.proxy_password||'')}"></div>
    <div class="card-title">Browser Overrides</div>
    <div class="form-row"><div class="form-group"><label>Locale</label><input id="pe-locale" value="${escHtml(p.locale)}" placeholder="Auto-detect"></div>
    <div class="form-group"><label>Timezone</label><input id="pe-tz" value="${escHtml(p.timezone)}" placeholder="Auto-detect"></div></div>
    <div class="form-row"><div class="form-group"><label>User Agent</label><input id="pe-ua" value="${escHtml(p.user_agent)}" placeholder="Auto"></div>
    <div class="form-group"><label>WebGL Vendor</label><input id="pe-wgv" value="${escHtml(p.webgl_vendor)}" placeholder="Auto"></div></div>
    <div class="form-group"><label>CPU Cores</label><input id="pe-cpu" value="${p.hardware_concurrency||''}" placeholder="Auto" type="number"></div>
  `, async () => {
    const pickedProxy = g('pe-pproxy').split(':');
    const data = { name: g('pe-name'), stage: g('pe-stage'), engine: g('pe-engine'), proxy_scheme: g('pe-pscheme'), proxy_host: pickedProxy[0] ? '' : g('pe-phost'), proxy_port: pickedProxy[0] ? '' : g('pe-pport'), proxy_user: pickedProxy[0] ? '' : g('pe-puser'), proxy_password: pickedProxy[0] ? '' : g('pe-ppass'), proxy_pool: pickedProxy[0] ? pickedProxy[1] : '', proxy_index: pickedProxy[0] === 'proxy' ? pickedProxy[2] : '', locale: g('pe-locale'), timezone: g('pe-tz'), user_agent: g('pe-ua'), webgl_vendor: g('pe-wgv'), hardware_concurrency: g('pe-cpu') };
    await apiPut('/profiles/' + encodeURIComponent(name), data);
    toast('Profile saved'); loadProfiles();
  });
}
function profilesImportShow() {
  showModal('Import Profiles', `
    <div class="form-group"><label>Profile Lines (one per line)</label><textarea id="pi-lines" rows="6" placeholder="email:password"></textarea></div>
    <div class="form-group"><label>Parse Template</label><input id="pi-template" value="email:password" placeholder="email:password"></div>
    <div class="form-row"><div class="form-group"><label>Default Stage</label><input id="pi-stage" placeholder="Default"></div>
    <div class="form-group"><label>Proxy Pool</label><input id="pi-pool" placeholder="(none)"></div></div>
  `, async () => {
    const r = await apiPost('/profiles/import', { lines: g('pi-lines'), template: g('pi-template'), stage: g('pi-stage'), proxy_pool: g('pi-pool') });
    stateCache.proxyPools = null;  // invalidate pool cache
    toast('Imported ' + (r.added || 0) + ' profiles'); loadProfiles();
  });
}

// ===== BROWSER =====
async function loadBrowser() {
  stateCache.browserSettings = await apiGet('/browser');
  const s = stateCache.browserSettings;
  const isCloak = s.browser_engine === 'cloakbrowser';
  document.getElementById('browser-form').innerHTML = `
    <div class="form-row"><div class="form-group"><label>Browser Engine</label><select id="bs-engine">
      <option value="camoufox" ${!isCloak?'selected':''}>Camoufox</option>
      <option value="cloakbrowser" ${isCloak?'selected':''}>CloakBrowser</option>
    </select></div>
    <div class="form-group"><label>Headless Mode</label><select id="bs-headless">
      <option value="false">Standard window</option>
      <option value="true" ${s.headless===true?'selected':''}>Headless</option>
      <option value="virtual" ${s.headless==='virtual'?'selected':''}>Headless (virtual)</option>
    </select></div></div>
    <div class="form-row"><div class="form-group"><label>Humanize Cursor</label><select id="bs-humanize">
      <option value="true" ${s.humanize!==false?'selected':''}>Yes</option>
      <option value="false" ${s.humanize===false?'selected':''}>No</option>
    </select></div>
    <div class="form-group"><label>Locale</label><input id="bs-locale" value="${escHtml(s.locale||'')}" placeholder="Auto"></div></div>
    <div class="form-row"><div class="form-group"><label>Timezone</label><input id="bs-tz" value="${escHtml(s.timezone||'')}" placeholder="Auto"></div>
    <div class="form-group"><label>Persistent Context</label><select id="bs-persist">
      <option value="true" ${s.persistent_context!==false?'selected':''}>Yes</option>
      <option value="false" ${s.persistent_context===false?'selected':''}>No</option>
    </select></div></div>
    <div class="form-row"><div class="form-group"><label>Window Width</label><input id="bs-ww" value="${s.window_width||''}" placeholder="1280" type="number"></div>
    <div class="form-group"><label>Window Height</label><input id="bs-wh" value="${s.window_height||''}" placeholder="720" type="number"></div></div>
    ${!isCloak ? `
    <div class="form-row"><div class="form-group"><label>Block WebRTC</label><select id="bs-webrtc"><option value="true" ${s.block_webrtc!==false?'selected':''}>Yes</option><option value="false">No</option></select></div>
    <div class="form-group"><label>Block WebGL</label><select id="bs-webgl"><option value="true" ${s.block_webgl!==false?'selected':''}>Yes</option><option value="false">No</option></select></div></div>
    <div class="form-row"><div class="form-group"><label>Block Images</label><select id="bs-images"><option value="true" ${s.block_images===true?'selected':''}>Yes</option><option value="false" ${s.block_images!==true?'selected':''}>No</option></select></div>
    <div class="form-group"><label>Disable COOP</label><select id="bs-coop"><option value="true" ${s.disable_coop===true?'selected':''}>Yes</option><option value="false" ${s.disable_coop!==true?'selected':''}>No</option></select></div></div>
    ` : `
    <div class="form-row"><div class="form-group"><label>Platform</label><select id="bs-platform"><option value="windows" ${s.platform==='windows'?'selected':''}>Windows</option><option value="macos" ${s.platform==='macos'?'selected':''}>macOS</option><option value="linux" ${s.platform==='linux'?'selected':''}>Linux</option></select></div>
    <div class="form-group"><label>Fingerprint Seed</label><input id="bs-fpseed" value="${s.fingerprint_seed||''}" placeholder="Auto" type="number"></div></div>
    <div class="form-row"><div class="form-group"><label>User Agent</label><input id="bs-ua" value="${escHtml(s.user_agent||'')}" placeholder="Auto"></div>
    <div class="form-group"><label>GPU Vendor</label><input id="bs-gpu" value="${escHtml(s.gpu_vendor||'')}" placeholder="Auto"></div></div>
    <div class="form-row"><div class="form-group"><label>CPU Cores</label><input id="bs-hw" value="${s.hardware_concurrency||''}" placeholder="Auto" type="number"></div>
    <div class="form-group"><label>Color Scheme</label><select id="bs-cs"><option value="" ${!s.color_scheme?'selected':''}>System</option><option value="light">Light</option><option value="dark">Dark</option></select></div></div>
    `}
    <div class="card-title" style="margin-top:12px">Virtual Display (Linux)</div><div class="form-row"><div class="form-group"><label>Enable Xvfb</label><select id="bs-vd"><option value="false">No</option><option value="true" ${s.vd_enabled===true?"selected":""}>Yes</option></select></div><div class="form-group"><label>Resolution</label><input id="bs-vdres" value="${s.vd_width||1920}x${s.vd_height||1080}" placeholder="1920x1080" style="width:100px"></div></div><div class="form-row"><div class="form-group"><label>Color Depth</label><select id="bs-vddepth"><option value="24" ${s.vd_depth!==16?"selected":""}>24-bit</option><option value="16" ${s.vd_depth===16?"selected":""}>16-bit</option></select></div></div>
    <div class="form-group"><label>Extension Paths (one per line)</label><textarea id="bs-ext">${(s.extension_paths||[]).join('\n')}</textarea></div>
    <div class="form-group"><label>Launch Args (one per line)</label><textarea id="bs-la">${(s.launch_args||[]).join('\n')}</textarea></div>
  `;
}
async function browserSave() {
  const vdRes = (g('bs-vdres') || '1920x1080').split('x');
  const data = { browser_engine: g('bs-engine'), headless: g('bs-headless') === 'true' ? true : g('bs-headless') === 'virtual' ? 'virtual' : false, humanize: g('bs-humanize') === 'true', locale: g('bs-locale'), timezone: g('bs-tz'), persistent_context: g('bs-persist') === 'true', window_width: parseInt(g('bs-ww')) || 0, window_height: parseInt(g('bs-wh')) || 0, extension_paths: g('bs-ext').split('\n').filter(Boolean), launch_args: g('bs-la').split('\n').filter(Boolean), vd_enabled: g('bs-vd') === 'true', vd_width: parseInt(vdRes[0]) || 1920, vd_height: parseInt(vdRes[1]) || 1080, vd_depth: parseInt(g('bs-vddepth')) || 24 };
  const isCloak = g('bs-engine') === 'cloakbrowser';
  if (!isCloak) {
    data.block_webrtc = g('bs-webrtc') === 'true'; data.block_webgl = g('bs-webgl') === 'true';
    data.block_images = g('bs-images') === 'true'; data.disable_coop = g('bs-coop') === 'true';
  } else {
    data.platform = g('bs-platform'); data.fingerprint_seed = parseInt(g('bs-fpseed')) || 0;
    data.user_agent = g('bs-ua'); data.gpu_vendor = g('bs-gpu');
    data.hardware_concurrency = parseInt(g('bs-hw')) || 0; data.color_scheme = g('bs-cs');
  }
  await apiPut('/browser', data); toast('Browser settings saved');
}
async function browserReset() { await apiPost('/browser/reset'); toast('Browser defaults restored'); loadBrowser(); }

// ===== PROXIES =====
async function loadProxies() {
  const data = await apiGet('/proxies');
  document.getElementById('proxies-pools').innerHTML = data.length === 0
    ? '<div class="card"><div style="color:var(--text-muted);text-align:center;padding:20px">No proxy pools yet</div></div>'
    : data.map(p => `<div class="card"><div class="card-title">${escHtml(p.name)} <span style="font-weight:400;color:var(--text-muted)">(${p.count} proxies)</span></div>
      <div class="btn-group" style="margin-bottom:12px">
        <button class="btn btn-sm" onclick="proxiesImport('${escJs(p.name)}')">Import</button>
        <button class="btn btn-sm btn-danger" onclick="proxiesPoolDelete('${escJs(p.name)}')">Delete Pool</button>
      </div>
      <div class="table-wrap"><table><thead><tr><th>Name</th><th>Proxy</th><th>Country</th><th>Region</th><th>Tags</th><th>Assigned To</th><th>Actions</th></tr></thead><tbody>
      ${(p.proxies||[]).map((px,i) => `<tr><td>${escHtml(px.name||('Proxy #'+(i+1)))}</td><td><code>${escHtml(px.value||'')}</code></td><td>${escHtml(px.country||'-')}</td><td>${escHtml(px.region||'-')}</td><td>${escHtml(px.tags||'-')}</td><td>${escHtml(px.assigned_to||'-')}</td><td><button class="btn btn-sm" onclick="proxiesEdit('${escJs(p.name)}',${i})">Edit</button> <button class="btn btn-sm" style="background:rgba(168,85,247,0.15);color:#c084fc" onclick="proxiesAssignManually('${escJs(p.name)}',${i})">Assign</button> <button class="btn btn-sm btn-danger" onclick="proxiesDelete('${escJs(p.name)}',${i})">Remove</button></td></tr>`).join('')}
      </tbody></table></div></div>`).join('');
}
function proxiesPoolCreate() {
  showModal('New Proxy Pool', '<div class="form-group"><label>Pool Name</label><input id="pp-name"></div>', async () => {
    await apiPost('/proxies/pool', { name: g('pp-name') }); toast('Pool created'); loadProxies();
  });
}
async function proxiesPoolDelete(name) {
  if (confirm('Delete pool ' + name + '?')) { await apiDelete('/proxies/pool/' + encodeURIComponent(name)); toast('Pool deleted'); loadProxies(); }
}
function proxiesImport(name) {
  showModal('Import Proxies to ' + name, `
    <div class="form-group"><label>Proxy List (one per line)</label>
    <textarea id="px-lines" rows="6" placeholder="socks5://host:port:user:password"></textarea></div>
  `, async () => {
    const r = await apiPost('/proxies/pool/' + encodeURIComponent(name) + '/import', { lines: g('px-lines') });
    toast('Imported ' + (r.added||0) + ' proxies'); loadProxies();
  });
}
async function proxiesAssignManually(poolName, idx) {
  var pools = await apiGet('/proxies');
  var pool = (pools || []).find(function(p) { return p.name === poolName; });
  var px = pool && pool.proxies ? pool.proxies[idx] : null;
  if (!px) return;
  var profiles = await apiGet('/profiles');
  var opts = '<option value="">(release)</option>';
  var assigned = (px.assigned_to || '').split(',').map(function(s) { return s.trim(); });
  for (var i = 0; i < profiles.length; i++) {
    var pn = profiles[i].name;
    var sel = assigned.indexOf(pn) >= 0 ? 'selected' : '';
    opts += '<option value="' + escHtml(pn) + '" ' + sel + '>' + escHtml(pn) + '</option>';
  }
  showModal('Assign Proxy', '<div class="form-group"><label>Proxy</label><code>' + escHtml(px.value || '') + '</code></div><div class="form-group"><label>Assign To</label><select id="ap-profile" multiple size="8">' + opts + '</select></div>', async function() {
    var profs = Array.from(document.getElementById('ap-profile').selectedOptions).map(function(o) { return o.value; }).filter(Boolean);
    await apiPost('/proxies/pool/' + encodeURIComponent(poolName) + '/assign', { index: idx, profiles: profs.join(',') });
    toast(profs.length ? 'Proxy assigned to ' + profs.length + ' profile(s)' : 'Proxy released');
    loadProxies();
  });
}
async function proxiesEdit(poolName, idx) {
  var pools = await apiGet('/proxies');
  var pool = (pools || []).find(function(p) { return p.name === poolName; });
  var px = pool && pool.proxies ? pool.proxies[idx] : null;
  if (!px) return;
  showModal('Edit Proxy', '<div class="form-group"><label>Name</label><input id="px-name" value="' + escHtml(px.name || ('Proxy #' + (idx + 1))) + '"></div><div class="form-group"><label>Proxy</label><input id="px-value" value="' + escHtml(px.value || '') + '"></div><div class="form-row"><div class="form-group"><label>Country</label><input id="px-country" value="' + escHtml(px.country || '') + '"></div><div class="form-group"><label>Region</label><input id="px-region" value="' + escHtml(px.region || '') + '"></div></div><div class="form-group"><label>Tags</label><input id="px-tags" value="' + escHtml(px.tags || '') + '" placeholder="residential, mobile"></div><div class="form-group"><label>Assigned profiles (comma separated)</label><input id="px-assigned" value="' + escHtml(px.assigned_to || '') + '"></div>', async function() {
    await apiPut('/proxies/pool/' + encodeURIComponent(poolName) + '/proxies/' + idx, { name: g('px-name'), value: g('px-value'), country: g('px-country'), region: g('px-region'), tags: g('px-tags'), assigned_to: g('px-assigned') });
    toast('Proxy updated'); loadProxies();
  });
}
async function proxiesDelete(poolName, index) {
  await apiPost('/proxies/pool/' + encodeURIComponent(poolName) + '/proxies/delete', { indices: [index] });
  toast('Proxy removed'); loadProxies();
}
function proxiesRefresh() { loadProxies(); }

// ===== LOGS =====
async function loadLogs() {
  const output = document.getElementById('logs-output');
  try {
    const data = await apiGet('/logs');
    output.textContent = Array.isArray(data) ? data.join('\n') || 'No logs yet' : 'No logs yet';
  } catch(e) {
    output.textContent = 'Failed to load logs: ' + e.message;
  }
  output.scrollTop = output.scrollHeight;
}
async function logsRefresh() { loadLogs(); }
async function logsClear() { await apiPost('/logs/clear'); document.getElementById('logs-output').textContent = ''; }

// ===== SETTINGS =====
async function loadSettings() {
  const s = await apiGet('/settings');
  document.getElementById('settings-form').innerHTML = `
    <div class="form-group"><label>Data Root</label><input id="set-data-root" value="${escHtml(s.data_root||'')}" readonly></div>
    <div class="form-group"><label>UI Theme</label><select id="set-theme"><option>premium_dark</option></select></div>
    <div class="form-group"><label>Account Parse Template</label><input id="set-template" value="${escHtml(s.account_parse_template||'')}"></div>
    <div class="card-title">About</div>
    <p style="color:var(--text-secondary)">CamouFlow v2.0.0 鈥?HTML UI</p>
    <p style="color:var(--text-muted);font-size:12px">Running on <code>${location.host}</code></p>
  `;
}
async function settingsSave() {
  await apiPut('/settings', { data_root: g('set-data-root'), ui_theme: g('set-theme'), account_parse_template: g('set-template') });
  toast('Settings saved');
}

// ========== Helpers ==========
function g(id) { return document.getElementById(id)?.value || ''; }
function escHtml(s) { return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }
function escJs(s) { return String(s||'').replace(/\\/g,'\\\\').replace(/'/g,"\\'").replace(/"/g,'\\"'); }

// ========== Init ==========
loadDashboard();