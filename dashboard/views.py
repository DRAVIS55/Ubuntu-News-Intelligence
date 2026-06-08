"""
dashboard/views.py — Serves the React-style SPA dashboard
Replaces Flask's render_template_string with Django's HttpResponse.
"""

from django.http import HttpResponse
from django.views.decorators.clickjacking import xframe_options_exempt

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>African News Intelligence Platform</title>
<style>
  :root {
    --bg: #0f1117; --surface: #1a1d27; --border: #2a2d3a;
    --text: #e8eaf0; --muted: #8891a4; --accent: #e85d20;
    --accent2: #f4a024; --green: #27c984; --red: #e84242;
    --blue: #4a9eff; --radius: 8px; --font: 'Inter', system-ui, sans-serif;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--bg); color: var(--text); font-family: var(--font); font-size: 14px; }
  a { color: var(--accent2); text-decoration: none; }
  a:hover { text-decoration: underline; }

  .shell { display: flex; min-height: 100vh; }
  .sidebar { width: 220px; background: var(--surface); border-right: 1px solid var(--border);
             padding: 24px 0; position: fixed; top: 0; left: 0; height: 100vh; overflow-y: auto; z-index: 100; }
  .main { margin-left: 220px; padding: 32px 40px; flex: 1; max-width: 1100px; }

  .logo { padding: 0 20px 24px; border-bottom: 1px solid var(--border); margin-bottom: 16px; }
  .logo-title { font-size: 13px; font-weight: 700; color: var(--accent); letter-spacing: .5px; text-transform: uppercase; }
  .logo-sub { font-size: 11px; color: var(--muted); margin-top: 2px; }
  .nav-section { padding: 8px 20px 4px; font-size: 10px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: 1px; }
  .nav-item { display: flex; align-items: center; gap: 10px; padding: 9px 20px; cursor: pointer;
              color: var(--muted); transition: all .15s; font-size: 13px; border-left: 2px solid transparent; }
  .nav-item:hover, .nav-item.active { color: var(--text); background: rgba(255,255,255,.04); border-left-color: var(--accent); }
  .nav-item .icon { font-size: 15px; }

  .card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; margin-bottom: 20px; }
  .card-title { font-size: 13px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: .5px; margin-bottom: 16px; }

  .page { display: none; }
  .page.active { display: block; }
  .page-header { margin-bottom: 28px; }
  .page-header h1 { font-size: 22px; font-weight: 700; margin-bottom: 4px; }
  .page-header p { color: var(--muted); font-size: 13px; }

  .stats-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
  .stat-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius);
               padding: 20px; text-align: center; }
  .stat-num { font-size: 28px; font-weight: 700; color: var(--accent2); }
  .stat-label { font-size: 11px; color: var(--muted); margin-top: 4px; text-transform: uppercase; letter-spacing: .5px; }

  textarea, input[type=text], select {
    background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius);
    color: var(--text); padding: 10px 14px; font-size: 13px; font-family: var(--font);
    width: 100%; outline: none; transition: border-color .15s;
  }
  textarea:focus, input:focus, select:focus { border-color: var(--accent); }
  textarea { resize: vertical; min-height: 140px; }

  .btn { display: inline-flex; align-items: center; gap: 6px; padding: 9px 18px;
         border-radius: var(--radius); font-size: 13px; font-weight: 600; cursor: pointer;
         border: none; transition: all .15s; }
  .btn-primary { background: var(--accent); color: white; }
  .btn-primary:hover { background: #d45018; }
  .btn-secondary { background: var(--border); color: var(--text); }
  .btn-secondary:hover { background: #353849; }
  .btn:disabled { opacity: .5; cursor: not-allowed; }

  .result-block { background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius);
                  padding: 18px; margin-top: 16px; white-space: pre-wrap; font-size: 13px; line-height: 1.7; }
  .headline-item { padding: 12px 16px; border: 1px solid var(--border); border-radius: 6px;
                   margin-bottom: 8px; background: var(--bg); }
  .headline-text { font-size: 15px; font-weight: 600; margin-bottom: 4px; }
  .headline-meta { font-size: 11px; color: var(--muted); }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
  .badge-high { background: rgba(232,66,66,.15); color: var(--red); }
  .badge-medium { background: rgba(244,160,36,.15); color: var(--accent2); }
  .badge-low { background: rgba(39,201,132,.15); color: var(--green); }

  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th { text-align: left; padding: 8px 12px; background: var(--bg); color: var(--muted);
       font-size: 11px; font-weight: 600; text-transform: uppercase; border-bottom: 1px solid var(--border); }
  td { padding: 10px 12px; border-bottom: 1px solid var(--border); vertical-align: top; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(255,255,255,.02); }

  .spinner { display: inline-block; width: 16px; height: 16px; border: 2px solid var(--border);
             border-top-color: var(--accent); border-radius: 50%; animation: spin .7s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .loading { display: flex; align-items: center; gap: 10px; color: var(--muted); padding: 20px 0; }

  .pattern-card { border-left: 3px solid var(--border); padding-left: 14px; margin-bottom: 16px; }
  .pattern-card.high { border-left-color: var(--red); }
  .pattern-card.medium { border-left-color: var(--accent2); }
  .pattern-card.low { border-left-color: var(--green); }

  .fuel-bar { background: var(--border); border-radius: 4px; height: 8px; margin-top: 4px; }
  .fuel-bar-fill { height: 8px; border-radius: 4px; background: var(--accent2); transition: width .5s; }

  .search-result { padding: 14px 0; border-bottom: 1px solid var(--border); }
  .search-result:last-child { border-bottom: none; }
  .search-result-title { font-weight: 600; margin-bottom: 4px; }
  .search-result-meta { font-size: 11px; color: var(--muted); margin-bottom: 6px; }
  .search-result-snippet { color: var(--muted); font-size: 12px; line-height: 1.6; }
  .similarity-pill { display: inline-block; padding: 1px 6px; border-radius: 10px;
                     background: rgba(74,158,255,.15); color: var(--blue); font-size: 11px; font-weight: 600; }
  .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 12px; }
  .label { display: block; font-size: 11px; font-weight: 600; color: var(--muted); text-transform: uppercase;
           letter-spacing: .5px; margin-bottom: 6px; }
  .tabs { display: flex; gap: 4px; border-bottom: 1px solid var(--border); margin-bottom: 20px; }
  .tab { padding: 8px 16px; cursor: pointer; font-size: 13px; color: var(--muted); border-bottom: 2px solid transparent; }
  .tab.active { color: var(--text); border-bottom-color: var(--accent); }
  .tab-content { display: none; }
  .tab-content.active { display: block; }

  .framework-badge { display: inline-block; padding: 2px 8px; border-radius: 4px;
                     background: rgba(39,201,132,.15); color: var(--green); font-size: 11px; font-weight: 600; margin-left: 8px; }
</style>
</head>
<body>
<div class="shell">

<nav class="sidebar">
  <div class="logo">
    <div class="logo-title">🌍 ANIP</div>
    <div class="logo-sub">African News Intelligence</div>
  </div>
  <div class="nav-section">Journalist Tools</div>
  <div class="nav-item active" onclick="showPage('headlines')"><span class="icon">📰</span> Headlines</div>
  <div class="nav-item" onclick="showPage('context')"><span class="icon">📚</span> Context Brief</div>
  <div class="nav-item" onclick="showPage('rewrite')"><span class="icon">✍️</span> Rewriter</div>
  <div class="nav-item" onclick="showPage('factcheck')"><span class="icon">✅</span> Fact-Check</div>
  <div class="nav-item" onclick="showPage('research')"><span class="icon">🔬</span> Research Brief</div>
  <div class="nav-section">Intelligence</div>
  <div class="nav-item" onclick="showPage('search')"><span class="icon">🔍</span> Archive Search</div>
  <div class="nav-item" onclick="showPage('patterns')"><span class="icon">📡</span> Patterns</div>
  <div class="nav-item" onclick="showPage('compare')"><span class="icon">📊</span> EAC Compare</div>
  <div class="nav-item" onclick="showPage('briefing')"><span class="icon">☀️</span> Daily Briefing</div>
  <div class="nav-section">System</div>
  <div class="nav-item" onclick="showPage('dashboard')"><span class="icon">📈</span> Dashboard</div>
</nav>

<main class="main">

  <!-- Dashboard -->
  <div id="page-dashboard" class="page active">
    <div class="page-header">
      <h1>Platform Overview <span class="framework-badge">Django</span></h1>
      <p>African News Intelligence Platform — built in Nairobi</p>
    </div>
    <div class="stats-row" id="stats-row">
      <div class="stat-card"><div class="stat-num" id="stat-articles">—</div><div class="stat-label">Articles Indexed</div></div>
      <div class="stat-card"><div class="stat-num" id="stat-vectors">—</div><div class="stat-label">Vectors Stored</div></div>
      <div class="stat-card"><div class="stat-num" id="stat-patterns">—</div><div class="stat-label">Active Patterns</div></div>
      <div class="stat-card"><div class="stat-num" id="stat-provider">—</div><div class="stat-label">LLM Provider</div></div>
    </div>
    <div class="card">
      <div class="card-title">Recent Articles</div>
      <div id="recent-articles-table"><div class="loading"><span class="spinner"></span> Loading...</div></div>
    </div>
  </div>

  <!-- Headlines -->
  <div id="page-headlines" class="page">
    <div class="page-header">
      <h1>Headline Generator</h1>
      <p>Paste an article body and generate multiple polished headline options</p>
    </div>
    <div class="card">
      <label class="label">Article Text</label>
      <textarea id="hl-text" placeholder="Paste the full article text here..."></textarea>
      <div style="margin-top:12px;display:flex;gap:10px;align-items:center">
        <button class="btn btn-primary" onclick="generateHeadlines()">Generate Headlines</button>
        <span id="hl-loading" style="display:none" class="loading"><span class="spinner"></span> Generating...</span>
      </div>
    </div>
    <div id="hl-results"></div>
  </div>

  <!-- Context Brief -->
  <div id="page-context" class="page">
    <div class="page-header">
      <h1>Context Brief</h1>
      <p>Get automatic historical context, parallels, and editorial guidance for any article</p>
    </div>
    <div class="card">
      <div class="form-row">
        <div>
          <label class="label">Article Title (optional)</label>
          <input type="text" id="ctx-title" placeholder="Article headline...">
        </div>
      </div>
      <label class="label">Article Text</label>
      <textarea id="ctx-text" placeholder="Paste article text..."></textarea>
      <div style="margin-top:12px;display:flex;gap:10px;align-items:center">
        <button class="btn btn-primary" onclick="getContext()">Generate Brief</button>
        <span id="ctx-loading" style="display:none" class="loading"><span class="spinner"></span> Analysing...</span>
      </div>
    </div>
    <div id="ctx-results"></div>
  </div>

  <!-- Rewriter -->
  <div id="page-rewrite" class="page">
    <div class="page-header">
      <h1>Article Rewriter</h1>
      <p>Improve draft articles for clarity, structure, and African context</p>
    </div>
    <div class="card">
      <div class="form-row">
        <div>
          <label class="label">Style</label>
          <select id="rw-style">
            <option value="standard">Standard — clear news writing</option>
            <option value="concise">Concise — maximum density</option>
            <option value="investigative">Investigative — evidence-led</option>
          </select>
        </div>
      </div>
      <label class="label">Draft Article</label>
      <textarea id="rw-text" placeholder="Paste your draft article..."></textarea>
      <div style="margin-top:12px;display:flex;gap:10px;align-items:center">
        <button class="btn btn-primary" onclick="rewriteArticle()">Rewrite Article</button>
        <span id="rw-loading" style="display:none" class="loading"><span class="spinner"></span> Rewriting...</span>
      </div>
    </div>
    <div id="rw-results"></div>
  </div>

  <!-- Fact Check -->
  <div id="page-factcheck" class="page">
    <div class="page-header">
      <h1>Fact-Check Assistant</h1>
      <p>Cross-reference article claims against the indexed archive</p>
    </div>
    <div class="card">
      <label class="label">Article Text</label>
      <textarea id="fc-text" placeholder="Paste article text to fact-check..."></textarea>
      <div style="margin-top:12px;display:flex;gap:10px;align-items:center">
        <button class="btn btn-primary" onclick="factCheck()">Fact-Check</button>
        <span id="fc-loading" style="display:none" class="loading"><span class="spinner"></span> Checking...</span>
      </div>
    </div>
    <div id="fc-results"></div>
  </div>

  <!-- Research Brief -->
  <div id="page-research" class="page">
    <div class="page-header">
      <h1>Research Brief</h1>
      <p>Generate a one-page research brief on any topic</p>
    </div>
    <div class="card">
      <div class="form-row">
        <div>
          <label class="label">Topic</label>
          <input type="text" id="rb-topic" placeholder="e.g. Kenya fuel subsidies, EAC integration...">
        </div>
        <div>
          <label class="label">Country Focus</label>
          <select id="rb-country">
            <option value="KE">Kenya</option>
            <option value="TZ">Tanzania</option>
            <option value="UG">Uganda</option>
            <option value="RW">Rwanda</option>
            <option value="ET">Ethiopia</option>
          </select>
        </div>
      </div>
      <div style="margin-top:12px;display:flex;gap:10px;align-items:center">
        <button class="btn btn-primary" onclick="generateResearch()">Generate Brief</button>
        <span id="rb-loading" style="display:none" class="loading"><span class="spinner"></span> Researching...</span>
      </div>
    </div>
    <div id="rb-results"></div>
  </div>

  <!-- Archive Search -->
  <div id="page-search" class="page">
    <div class="page-header">
      <h1>Archive Search</h1>
      <p>Semantically search the indexed news archive</p>
    </div>
    <div class="card">
      <div class="form-row">
        <div>
          <label class="label">Query</label>
          <input type="text" id="search-q" placeholder="Search news archive..." onkeyup="if(event.key==='Enter')doSearch()">
        </div>
        <div>
          <label class="label">Country Filter</label>
          <select id="search-country">
            <option value="">All countries</option>
            <option value="KE">Kenya</option>
            <option value="TZ">Tanzania</option>
            <option value="UG">Uganda</option>
            <option value="RW">Rwanda</option>
            <option value="ET">Ethiopia</option>
          </select>
        </div>
      </div>
      <button class="btn btn-primary" onclick="doSearch()">Search Archive</button>
    </div>
    <div id="search-results"></div>
  </div>

  <!-- Patterns -->
  <div id="page-patterns" class="page">
    <div class="page-header">
      <h1>Pattern Detection</h1>
      <p>Trends and anomalies automatically surfaced across the archive</p>
    </div>
    <div id="patterns-content"><div class="loading"><span class="spinner"></span> Loading patterns...</div></div>
  </div>

  <!-- EAC Compare -->
  <div id="page-compare" class="page">
    <div class="page-header">
      <h1>EAC Peer Comparison</h1>
      <p>Fuel prices and economic indicators across East Africa</p>
    </div>
    <div id="fuel-content"><div class="loading"><span class="spinner"></span> Loading fuel data...</div></div>
    <div class="card" style="margin-top:20px">
      <div class="card-title">Generate Article Comparison</div>
      <label class="label">Paste an article about an economic topic</label>
      <textarea id="cmp-text" placeholder="Paste article text to generate peer comparison..."></textarea>
      <div class="form-row" style="margin-top:12px">
        <div>
          <label class="label">Focus Country</label>
          <select id="cmp-country">
            <option value="KE">Kenya</option>
            <option value="TZ">Tanzania</option>
            <option value="UG">Uganda</option>
            <option value="RW">Rwanda</option>
            <option value="ET">Ethiopia</option>
          </select>
        </div>
      </div>
      <div style="display:flex;gap:10px;align-items:center">
        <button class="btn btn-primary" onclick="generateComparison()">Generate Comparison</button>
        <span id="cmp-loading" style="display:none" class="loading"><span class="spinner"></span> Fetching data...</span>
      </div>
    </div>
    <div id="cmp-results"></div>
  </div>

  <!-- Daily Briefing -->
  <div id="page-briefing" class="page">
    <div class="page-header">
      <h1>Daily Briefing</h1>
      <p>AI-generated editorial briefing for the day's top stories</p>
    </div>
    <div class="card">
      <div class="form-row">
        <div>
          <label class="label">Country</label>
          <select id="brief-country">
            <option value="KE">Kenya</option>
            <option value="TZ">Tanzania</option>
            <option value="UG">Uganda</option>
            <option value="RW">Rwanda</option>
            <option value="ET">Ethiopia</option>
          </select>
        </div>
      </div>
      <button class="btn btn-primary" onclick="getDailyBriefing()">Generate Today's Briefing</button>
    </div>
    <div id="brief-results"></div>
  </div>

</main>
</div>

<script>
const API = '/api/v1';

function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  document.getElementById('page-' + name).classList.add('active');
  event.currentTarget.classList.add('active');

  if (name === 'dashboard') loadDashboard();
  if (name === 'patterns') loadPatterns();
  if (name === 'compare') loadFuelComparison();
}

async function api(path, opts = {}) {
  const r = await fetch(API + path, {
    headers: { 'Content-Type': 'application/json', ...opts.headers },
    ...opts,
  });
  return r.json();
}

// ── Dashboard ──────────────────────────────────────────────────────────────────
async function loadDashboard() {
  try {
    const stats = await api('/admin/stats', { headers: { 'X-Admin-Token': 'dev-admin-token' } });
    if (stats.success) {
      const d = stats.data;
      document.getElementById('stat-articles').textContent = (d.articles || 0).toLocaleString();
      document.getElementById('stat-vectors').textContent = (d.vectors || 0).toLocaleString();
      document.getElementById('stat-patterns').textContent = (d.active_patterns || 0).toLocaleString();
      document.getElementById('stat-provider').textContent = d.llm_provider || '—';
    }
    const arts = await api('/articles?limit=10');
    if (arts.success && arts.data.articles.length) {
      const tbody = arts.data.articles.map(a => `
        <tr>
          <td>${a.title}</td>
          <td>${a.source_name}</td>
          <td><span class="badge badge-medium">${a.country_code || '—'}</span></td>
          <td style="color:var(--muted)">${a.published_at ? new Date(a.published_at).toLocaleDateString() : '—'}</td>
        </tr>`).join('');
      document.getElementById('recent-articles-table').innerHTML = `
        <table><thead><tr><th>Title</th><th>Source</th><th>Country</th><th>Published</th></tr></thead>
        <tbody>${tbody}</tbody></table>`;
    } else {
      document.getElementById('recent-articles-table').innerHTML = '<p style="color:var(--muted)">No articles indexed yet. Run the ingestion pipeline to get started.</p>';
    }
  } catch(e) {
    document.getElementById('recent-articles-table').innerHTML = `<p style="color:var(--red)">Error loading dashboard: ${e.message}</p>`;
  }
}

// ── Headlines ──────────────────────────────────────────────────────────────────
async function generateHeadlines() {
  const text = document.getElementById('hl-text').value.trim();
  if (!text) return;
  document.getElementById('hl-loading').style.display = 'flex';
  document.getElementById('hl-results').innerHTML = '';
  try {
    const r = await api('/articles/headlines', { method: 'POST', body: JSON.stringify({ text }) });
    document.getElementById('hl-loading').style.display = 'none';
    if (r.success) {
      document.getElementById('hl-results').innerHTML = r.data.headlines.map(h => `
        <div class="headline-item">
          <div class="headline-text">${h.text}</div>
          <div class="headline-meta">Style: <strong>${h.style}</strong> — ${h.explanation}</div>
        </div>`).join('');
    } else {
      document.getElementById('hl-results').innerHTML = `<div class="result-block" style="color:var(--red)">${r.error}</div>`;
    }
  } catch(e) {
    document.getElementById('hl-loading').style.display = 'none';
    document.getElementById('hl-results').innerHTML = `<div class="result-block" style="color:var(--red)">Error: ${e.message}</div>`;
  }
}

// ── Context Brief ──────────────────────────────────────────────────────────────
async function getContext() {
  const text = document.getElementById('ctx-text').value.trim();
  const title = document.getElementById('ctx-title').value.trim();
  if (!text) return;
  document.getElementById('ctx-loading').style.display = 'flex';
  document.getElementById('ctx-results').innerHTML = '';
  try {
    const r = await api('/articles/context', { method: 'POST', body: JSON.stringify({ text, title }) });
    document.getElementById('ctx-loading').style.display = 'none';
    if (r.success) {
      document.getElementById('ctx-results').innerHTML = `<div class="card"><div class="result-block">${r.data.brief}</div></div>`;
    }
  } catch(e) {
    document.getElementById('ctx-loading').style.display = 'none';
  }
}

// ── Rewriter ───────────────────────────────────────────────────────────────────
async function rewriteArticle() {
  const text = document.getElementById('rw-text').value.trim();
  const style = document.getElementById('rw-style').value;
  if (!text) return;
  document.getElementById('rw-loading').style.display = 'flex';
  document.getElementById('rw-results').innerHTML = '';
  try {
    const r = await api('/articles/rewrite', { method: 'POST', body: JSON.stringify({ text, style }) });
    document.getElementById('rw-loading').style.display = 'none';
    if (r.success) {
      document.getElementById('rw-results').innerHTML = `<div class="card"><div class="result-block">${r.data.rewritten}</div></div>`;
    }
  } catch(e) {
    document.getElementById('rw-loading').style.display = 'none';
  }
}

// ── Fact Check ─────────────────────────────────────────────────────────────────
async function factCheck() {
  const text = document.getElementById('fc-text').value.trim();
  if (!text) return;
  document.getElementById('fc-loading').style.display = 'flex';
  document.getElementById('fc-results').innerHTML = '';
  try {
    const r = await api('/articles/factcheck', { method: 'POST', body: JSON.stringify({ text }) });
    document.getElementById('fc-loading').style.display = 'none';
    if (r.success) {
      const claimsHtml = r.data.claims.map(c => `
        <div style="padding:10px 0;border-bottom:1px solid var(--border)">
          <div style="font-weight:600;margin-bottom:4px">${c.claim}</div>
          <div style="font-size:12px;color:var(--muted)">${c.evidence_found ? '✅ ' + c.archive_evidence.length + ' matching articles found' : '⚠️ No archive evidence found'}</div>
        </div>`).join('');
      document.getElementById('fc-results').innerHTML = `
        <div class="card">
          <div class="card-title">Claims Analysed</div>
          ${claimsHtml}
          <div style="margin-top:16px"><div class="card-title">Synthesis</div>
          <div class="result-block">${r.data.synthesis}</div></div>
        </div>`;
    }
  } catch(e) {
    document.getElementById('fc-loading').style.display = 'none';
  }
}

// ── Research Brief ─────────────────────────────────────────────────────────────
async function generateResearch() {
  const topic = document.getElementById('rb-topic').value.trim();
  const country_code = document.getElementById('rb-country').value;
  if (!topic) return;
  document.getElementById('rb-loading').style.display = 'flex';
  document.getElementById('rb-results').innerHTML = '';
  try {
    const r = await api('/articles/research', { method: 'POST', body: JSON.stringify({ topic, country_code }) });
    document.getElementById('rb-loading').style.display = 'none';
    if (r.success) {
      document.getElementById('rb-results').innerHTML = `<div class="card"><div class="result-block">${r.data.brief}</div></div>`;
    }
  } catch(e) {
    document.getElementById('rb-loading').style.display = 'none';
  }
}

// ── Archive Search ─────────────────────────────────────────────────────────────
async function doSearch() {
  const q = document.getElementById('search-q').value.trim();
  const country = document.getElementById('search-country').value;
  if (!q) return;
  document.getElementById('search-results').innerHTML = '<div class="loading"><span class="spinner"></span> Searching...</div>';
  try {
    const params = new URLSearchParams({ q, n: 15 });
    if (country) params.set('country', country);
    const r = await api('/search?' + params);
    if (r.success && r.data.results.length) {
      document.getElementById('search-results').innerHTML = `<div class="card">${r.data.results.map(res => `
        <div class="search-result">
          <div class="search-result-title">${res.title} <span class="similarity-pill">${(res.similarity * 100).toFixed(0)}%</span></div>
          <div class="search-result-meta">${res.source_name} · ${res.country_code} · ${res.published_at ? new Date(res.published_at).toLocaleDateString() : ''}</div>
          <div class="search-result-snippet">${res.snippet}</div>
        </div>`).join('')}</div>`;
    } else {
      document.getElementById('search-results').innerHTML = '<div class="card" style="color:var(--muted)">No results found. Try a different query or ingest more articles.</div>';
    }
  } catch(e) {
    document.getElementById('search-results').innerHTML = `<div class="card" style="color:var(--red)">Search error: ${e.message}</div>`;
  }
}

// ── Patterns ───────────────────────────────────────────────────────────────────
async function loadPatterns() {
  try {
    const r = await api('/patterns');
    if (r.success) {
      if (!r.data.patterns.length) {
        document.getElementById('patterns-content').innerHTML = '<div class="card" style="color:var(--muted)">No patterns detected yet. Patterns are surfaced automatically as more articles are ingested.</div>';
        return;
      }
      document.getElementById('patterns-content').innerHTML = r.data.patterns.map(p => `
        <div class="pattern-card ${p.severity}">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">
            <span class="badge badge-${p.severity}">${p.severity.toUpperCase()}</span>
            <strong>${p.title}</strong>
          </div>
          <div style="font-size:12px;color:var(--muted)">${p.pattern_type} · ${p.article_count} articles · Last seen: ${p.last_seen ? new Date(p.last_seen).toLocaleDateString() : '—'}</div>
        </div>`).join('');
    }
  } catch(e) {
    document.getElementById('patterns-content').innerHTML = `<div class="card" style="color:var(--red)">Error: ${e.message}</div>`;
  }
}

// ── Fuel Comparison ────────────────────────────────────────────────────────────
async function loadFuelComparison() {
  try {
    const r = await api('/compare/fuel');
    if (r.success) {
      const d = r.data;
      const maxPrice = Math.max(...d.comparison.map(c => c.petrol_usd_per_litre));
      document.getElementById('fuel-content').innerHTML = `
        <div class="card">
          <div class="card-title">Fuel Prices — EAC Comparison (USD/litre)</div>
          ${d.comparison.map(c => `
            <div style="margin-bottom:14px">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <span style="font-weight:600">${c.country}</span>
                <span style="font-weight:700;color:var(--accent2)">$${c.petrol_usd_per_litre} / L</span>
              </div>
              <div class="fuel-bar"><div class="fuel-bar-fill" style="width:${(c.petrol_usd_per_litre / maxPrice * 100).toFixed(0)}%"></div></div>
              <div style="font-size:11px;color:var(--muted);margin-top:2px">${c.petrol_local} ${c.currency} · Source: ${c.source}</div>
            </div>`).join('')}
          <div style="margin-top:12px;padding-top:12px;border-top:1px solid var(--border);font-size:12px;color:var(--muted)">
            EAC Average: <strong>$${d.eac_average_usd}</strong> · Kenya vs Average: <strong>${d.kenya_vs_eac_average_pct > 0 ? '+' : ''}${d.kenya_vs_eac_average_pct}%</strong>
          </div>
        </div>`;
    }
  } catch(e) {
    document.getElementById('fuel-content').innerHTML = `<div class="card" style="color:var(--red)">Error: ${e.message}</div>`;
  }
}

// ── EAC Comparison ─────────────────────────────────────────────────────────────
async function generateComparison() {
  const text = document.getElementById('cmp-text').value.trim();
  const country_code = document.getElementById('cmp-country').value;
  if (!text) return;
  document.getElementById('cmp-loading').style.display = 'flex';
  document.getElementById('cmp-results').innerHTML = '';
  try {
    const r = await api('/compare/eac', { method: 'POST', body: JSON.stringify({ text, country_code }) });
    document.getElementById('cmp-loading').style.display = 'none';
    if (r.success) {
      if (!r.data.applicable) {
        document.getElementById('cmp-results').innerHTML = `<div class="card" style="color:var(--muted)">${r.data.reason}</div>`;
      } else {
        document.getElementById('cmp-results').innerHTML = `<div class="card"><div class="result-block">${r.data.narrative || 'No narrative generated.'}</div></div>`;
      }
    }
  } catch(e) {
    document.getElementById('cmp-loading').style.display = 'none';
  }
}

// ── Daily Briefing ─────────────────────────────────────────────────────────────
async function getDailyBriefing() {
  const country_code = document.getElementById('brief-country').value;
  document.getElementById('brief-results').innerHTML = '<div class="loading"><span class="spinner"></span> Generating briefing...</div>';
  try {
    const r = await api('/briefing?country_code=' + country_code);
    if (r.success) {
      document.getElementById('brief-results').innerHTML = `
        <div class="card">
          <div class="card-title">Briefing — ${new Date().toLocaleDateString('en-GB', {weekday:'long', year:'numeric', month:'long', day:'numeric'})}</div>
          <div class="result-block">${r.data.briefing}</div>
          <div style="font-size:11px;color:var(--muted);margin-top:12px">Based on ${r.data.article_count} recent articles · Generated ${new Date(r.data.generated_at).toLocaleTimeString()}</div>
        </div>`;
    }
  } catch(e) {
    document.getElementById('brief-results').innerHTML = `<div class="card" style="color:var(--red)">Error: ${e.message}</div>`;
  }
}

// Load dashboard on startup
loadDashboard();
</script>
</body>
</html>"""


@xframe_options_exempt
def dashboard_view(request, path=""):
    """Serve the SPA for all non-API routes."""
    return HttpResponse(DASHBOARD_HTML, content_type="text/html")
