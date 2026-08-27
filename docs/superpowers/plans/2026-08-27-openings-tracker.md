# Openings Tracker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the Compare tab in `static/texas_alcohol_explorer.html` with an "Openings" tab that shows newly-issued and recently-cancelled/surrendered TABC Mixed Beverage (MB) permits for a selected Month/Year (+ optional City/ZIP).

**Architecture:** Single self-contained static HTML file, no build step. This plan removes one self-contained block of markup/CSS/JS (Compare) and adds another self-contained block (Openings) in the same style, reusing existing global helpers (`fmtMoney`, `openHistory`, `downloadCSV`, `TOP_METRO_CITIES`, `switchTab`) rather than duplicating them.

**Tech Stack:** Vanilla JS (ES5-style, matches existing code), inline CSS, Socrata Open Data API (`data.texas.gov`) — no new dependencies.

**Design spec:** `docs/superpowers/specs/2026-08-27-openings-tracker-design.md`

**No automated test suite exists in this project** (no `package.json`, no test runner). "Testing" in every task below means live verification in a browser against the real `static/texas_alcohol_explorer.html` file, served locally — the same approach already used earlier to verify Explorer/Nearby/Compare. A `.claude/.claude/launch.json` dev-server config already exists (serves `personal-dashboard/` on port 8000 via `python -m http.server`); reuse `preview_start` with that config name (`texas-alcohol-explorer`) rather than creating a new one.

---

### Task 1: Create the working branch

**Files:** none (git only)

- [ ] **Step 1: Create and switch to a new branch**

```bash
cd ~/personal-dashboard && git checkout -b feature/openings-tracker
```

Expected: `Switched to a new branch 'feature/openings-tracker'`

- [ ] **Step 2: Confirm clean starting point**

```bash
cd ~/personal-dashboard && git status
```

Expected: `nothing to commit, working tree clean` (aside from any pre-existing unrelated uncommitted changes to `static/geocode_tabc.py` / `static/tx_venues_geo.json` / `geocode_tabc_update.py` noted earlier this session — leave those untouched, don't commit them as part of this feature).

---

### Task 2: Remove the Compare feature

**Files:**
- Modify: `static/texas_alcohol_explorer.html`

Everything Compare-related lives in three contiguous, self-contained regions of the file (verified via full-file grep — no `cmp*`/`Compare` references exist outside these three regions). Remove all three in this task.

- [ ] **Step 1: Remove the Compare CSS block**

Find this exact block (currently lines 246–285) and delete it entirely, including the blank line that follows it:

```css
/* Compare tab */
.cmp-input-row { position:relative; margin-bottom:8px; }
.cmp-venue-input { width:100%; padding:10px 12px; border:1.5px solid var(--border2); border-radius:var(--r-sm); background:var(--s1); color:var(--text); font-size:14px; font-family:var(--font); outline:none; transition:border-color 0.15s; }
.cmp-venue-input:focus { border-color:var(--accent); }
.cmp-venue-input.cmp-confirmed { border-color:var(--pos); background:var(--pos-dim); }
/* Compare search results list */
.cmp-result-row { display:flex; align-items:center; padding:10px 12px; border-bottom:1px solid var(--border); cursor:pointer; gap:10px; -webkit-tap-highlight-color:transparent; }
.cmp-result-row:last-child { border-bottom:none; }
.cmp-result-row:hover, .cmp-result-row:active { background:var(--s2); }
.cmp-result-row.selected { background:var(--pos-dim); }
.cmp-result-cb { width:18px; height:18px; accent-color:var(--accent); flex-shrink:0; cursor:pointer; }
.cmp-result-info { flex:1; min-width:0; }
.cmp-result-name { font-size:13px; font-weight:600; color:var(--text); }
.cmp-result-sub { font-size:11px; color:var(--text3); margin-top:2px; }

.cmp-chip { display:flex; align-items:center; gap:8px; background:var(--pos-dim); border:1px solid var(--pos); border-radius:20px; padding:5px 8px 5px 12px; margin-bottom:5px; }
.cmp-chip-name { font-size:12px; font-weight:600; color:var(--text); flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.cmp-chip-city { font-size:11px; color:var(--text3); flex-shrink:0; }
.cmp-chip-rm { width:20px; height:20px; border-radius:50%; border:none; background:transparent; color:var(--text3); font-size:14px; cursor:pointer; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.cmp-chip-rm:hover { color:var(--neg); }
.cmp-venue-input::placeholder { color:var(--text3); }
.cmp-suggestions { position:absolute; top:100%; left:0; right:0; background:var(--s1); border:1px solid var(--border); border-radius:var(--r-sm); box-shadow:0 4px 16px rgba(0,0,0,0.12); z-index:100; max-height:200px; overflow-y:auto; display:none; }
.cmp-sug-item { padding:10px 14px; cursor:pointer; font-size:13px; border-bottom:1px solid var(--border); }
.cmp-sug-item:last-child { border-bottom:none; }
.cmp-sug-item:hover { background:var(--s2); }
.cmp-sug-name { font-weight:600; }
.cmp-sug-addr { font-size:11px; color:var(--text3); margin-top:1px; }
.cmp-table-wrap { overflow-x:auto; -webkit-overflow-scrolling:touch; margin-top:0; }
.cmp-grid { width:100%; border-collapse:collapse; font-size:12px; min-width:400px; }
.cmp-grid th { font-family:var(--mono); font-size:9px; letter-spacing:0.08em; text-transform:uppercase; color:var(--text3); padding:8px 10px; text-align:right; border-bottom:2px solid var(--text); white-space:nowrap; background:var(--s1); position:sticky; top:0; }
.cmp-grid th:first-child { text-align:left; position:sticky; left:0; background:var(--s1); z-index:2; min-width:60px; }
.cmp-grid td { padding:8px 10px; text-align:right; border-bottom:1px solid var(--border); font-family:var(--mono); font-size:12px; white-space:nowrap; }
.cmp-grid td:first-child { text-align:left; font-family:var(--font); font-size:12px; color:var(--text2); position:sticky; left:0; background:var(--s1); z-index:1; }
.cmp-grid tr:hover td { background:var(--s2); }
.cmp-grid tr:hover td:first-child { background:var(--s2); }
.cmp-grid .cmp-header-row th { color:var(--text); font-size:10px; font-family:var(--font); font-weight:600; }
.cmp-grid .cmp-total-row td { font-weight:700; border-top:2px solid var(--text); }
.cmp-grid .cmp-avg-row td { color:var(--text3); border-top:1px solid var(--border2); }
.cmp-grid td.no-data { color:var(--text3); }
.cmp-grid td.best { color:var(--pos); font-weight:700; }
```

- [ ] **Step 2: Remove the Compare page markup**

The file currently has this structure around the Compare section (line numbers as of this plan's writing):

```
433: </div>                          <- closes map-page
434: (blank)
435: <!-- ── Compare ── -->
436: <div id="compare-page" ...>
  ...compare-page contents...
473: </div>                          <- closes compare-page
474: (blank)
475: (blank)                         <- note: TWO blank lines here (pre-existing inconsistency)
476: <!-- ── Modal ── -->
```

Every other top-level page section in this file (Explorer→Map, etc.) is separated by exactly **one** blank line — the double blank line before Modal is a pre-existing anomaly specific to Compare. Delete everything from `<!-- ── Compare ── -->` (435) through the second blank line (475) inclusive, i.e. delete this exact block:

```html
<!-- ── Compare ── -->
<div id="compare-page" class="page">
  <div class="hdr">
    <div class="hdr-eyebrow">Texas Open Data · TABC</div>
    <h1 class="hdr-title"><strong>Venue</strong> <em>Comparison</em></h1>
  </div>
  <div class="wrap">
    <div class="fcard">
      <div class="section-label" style="margin-bottom:10px">Search venues — select up to 5 to compare</div>
      <div style="display:flex;gap:8px;margin-bottom:10px">
        <input id="cmp-search-input" type="text" placeholder="Search by name, e.g. Haywire…"
          style="flex:1;padding:10px 12px;border:1.5px solid var(--border2);border-radius:var(--r-sm);background:var(--s2);color:var(--text);font-size:14px;font-family:var(--sans);outline:none;"
          oninput="cmpLiveSearch(this)" autocomplete="off" autocorrect="off">
        <button class="btn-clear" onclick="cmpClearSearch()" style="white-space:nowrap">Clear</button>
      </div>
      <div id="cmp-search-results" style="display:none;margin-bottom:12px;border:1px solid var(--border2);border-radius:var(--r-sm);overflow:hidden;"></div>
      <div id="cmp-selected-list" style="display:none;margin-bottom:10px">
        <div style="font-family:var(--mono);font-size:9px;text-transform:uppercase;letter-spacing:0.08em;color:var(--text3);margin-bottom:6px">Selected venues</div>
        <div id="cmp-chips"></div>
      </div>
      <div style="display:flex;align-items:center;gap:10px;margin-top:14px">
        <button class="btn-run" id="cmp-run-btn" onclick="runComparison()" disabled>Compare</button>
        <button class="btn-clear" onclick="clearComparison()">Reset all</button>
        <span id="cmp-sel-count" style="font-family:var(--mono);font-size:11px;color:var(--text3);"></span>
      </div>
    </div>

    <div id="cmp-status" class="map-status" style="display:none"></div>
    <div id="cmp-result" style="display:none">
      <div class="tbl-hdr" style="margin-top:16px">
        <span class="tbl-hint" id="cmp-period-label"></span>
        <button class="btn-sm" onclick="exportCompareCSV()">Export CSV</button>
      </div>
      <div class="cmp-table-wrap">
        <table class="cmp-grid" id="cmp-grid"></table>
      </div>
    </div>
  </div>
</div>


```

This leaves `</div>` (map-page's close, line 433) immediately followed by zero blank lines, then `<!-- ── Modal ── -->`. Add back exactly **one** blank line between them, matching the spacing convention used everywhere else in the file (Explorer→Map is a single blank line, for example) — so the result reads:

```
  </div>
</div>

<!-- ── Modal ── -->
```

- [ ] **Step 3: Remove the Compare tab button**

Find this exact block (currently lines 501–504) and delete it:

```html
  <button class="tab" id="tab-compare" onclick="switchTab('compare')">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
    Compare
  </button>
```

(Task 3 will add the Openings tab button in its place, immediately after `tab-map`.)

- [ ] **Step 4: Remove the Compare JS block**

Find this exact block — it starts at `var cmpVenues = [null,null,null,null,null];` and ends right before the `// Tab switching` comment (currently lines 1547–1839, including the trailing blank lines before that comment) — and delete it entirely:

```javascript
var cmpVenues = [null,null,null,null,null]; // selected (up to 5)
var cmpHistory = {};
var cmpSearchTimer = null;
var cmpAllResults = []; // last search results

function cmpKey(v) {
  return (v.location_name||'') + '|' + (v.location_zip||'');
}

function cmpLiveSearch(input) {
  var q = input.value.trim();
  var box = document.getElementById('cmp-search-results');
  clearTimeout(cmpSearchTimer);
  if (q.length < 2) { box.style.display = 'none'; return; }
  cmpSearchTimer = setTimeout(function() {
    var url = 'https://data.texas.gov/resource/naix-2893.json' +
      '?$select=location_name,location_city,location_address,location_zip,taxpayer_name' +
      '&$where=' + encodeURIComponent("upper(location_name) like '%" + q.toUpperCase().replace(/'/g,"''") + "%' AND total_receipts>=25000") +
      '&$limit=20&$order=total_receipts DESC';
    fetch(url).then(function(r){return r.json();}).then(function(data){
      // Dedupe by name+zip
      var seen = {}, results = [];
      data.forEach(function(r) {
        var k = cmpKey(r);
        if (!seen[k]) { seen[k]=true; results.push(r); }
      });
      cmpAllResults = results;
      box.innerHTML = '';
      if (!results.length) { box.style.display='none'; return; }
      results.forEach(function(r) {
        var isSelected = cmpVenues.some(function(v){ return v && cmpKey(v)===cmpKey(r); });
        var row = document.createElement('div');
        row.className = 'cmp-result-row' + (isSelected?' selected':'');
        var city = (r.location_city||'').charAt(0)+(r.location_city||'').slice(1).toLowerCase();
        var addr = r.location_address ? r.location_address+', '+city : city;
        row.innerHTML =
          '<input type="checkbox" class="cmp-result-cb"'+(isSelected?' checked':'')+'>' +
          '<div class="cmp-result-info">' +
            '<div class="cmp-result-name">'+(r.location_name||'')+'</div>' +
            '<div class="cmp-result-sub">'+addr+' &nbsp;·&nbsp; '+(r.location_zip||'')+'</div>' +
          '</div>';
        var cb = row.querySelector('input');
        function toggle(e) {
          if (e && e.target === cb) return; // handled by change
          cb.checked = !cb.checked;
          cb.dispatchEvent(new Event('change'));
        }
        cb.addEventListener('change', function() {
          if (cb.checked) {
            var filled = cmpVenues.filter(function(v){return v!==null;});
            if (filled.length >= 5) { cb.checked=false; return; }
            var slot = cmpVenues.indexOf(null);
            if (slot === -1) { cb.checked=false; return; }
            cmpVenues[slot] = r;
            row.classList.add('selected');
          } else {
            var key = cmpKey(r);
            for (var i=0;i<cmpVenues.length;i++) {
              if (cmpVenues[i] && cmpKey(cmpVenues[i])===key) { cmpVenues[i]=null; break; }
            }
            row.classList.remove('selected');
          }
          renderCmpChips();
          updateCmpBtn();
        });
        row.addEventListener('click', function(e){
          if (e.target===cb) return;
          cb.checked = !cb.checked;
          cb.dispatchEvent(new Event('change'));
        });
        box.appendChild(row);
      });
      box.style.display = 'block';
    }).catch(function(){});
  }, 300);
}

function renderCmpChips() {
  var selected = cmpVenues.filter(function(v){return v!==null;});
  var wrap = document.getElementById('cmp-selected-list');
  var chips = document.getElementById('cmp-chips');
  if (!selected.length) { wrap.style.display='none'; return; }
  wrap.style.display = 'block';
  chips.innerHTML = '';
  selected.forEach(function(v) {
    var city = (v.location_city||'').charAt(0)+(v.location_city||'').slice(1).toLowerCase();
    var chip = document.createElement('div');
    chip.className = 'cmp-chip';
    chip.innerHTML =
      '<span class="cmp-chip-name">'+(v.location_name||'')+'</span>' +
      '<span class="cmp-chip-city">'+city+'</span>' +
      '<button class="cmp-chip-rm" title="Remove">×</button>';
    var key = cmpKey(v);
    chip.querySelector('.cmp-chip-rm').onclick = function() {
      for (var i=0;i<cmpVenues.length;i++) {
        if (cmpVenues[i] && cmpKey(cmpVenues[i])===key) { cmpVenues[i]=null; break; }
      }
      renderCmpChips();
      updateCmpBtn();
      // Uncheck in results list if visible
      var rows = document.querySelectorAll('#cmp-search-results .cmp-result-row');
      rows.forEach(function(row){
        var cb = row.querySelector('input');
        if (cb && row.querySelector('.cmp-result-name') &&
            row.querySelector('.cmp-result-name').textContent === (v.location_name||'')) {
          cb.checked = false;
          row.classList.remove('selected');
        }
      });
    };
    chips.appendChild(chip);
  });
}

function cmpClearSearch() {
  var input = document.getElementById('cmp-search-input');
  if (input) { input.value = ''; }
  var box = document.getElementById('cmp-search-results');
  if (box) { box.innerHTML=''; box.style.display='none'; }
}

function updateCmpBtn() {
  var count = cmpVenues.filter(function(v){ return v !== null; }).length;
  var btn = document.getElementById('cmp-run-btn');
  var lbl = document.getElementById('cmp-sel-count');
  btn.disabled = count < 2;
  lbl.textContent = count >= 2 ? count + ' selected' : (count === 1 ? '1 selected — need 1 more' : '');
}

function cmpSelectVenue(slot, venue) {
  cmpVenues[slot] = venue;
  var inputs = document.querySelectorAll('.cmp-venue-input');
  if (inputs[slot]) inputs[slot].classList.add('cmp-confirmed');
  updateCmpBtn();
}

function clearComparison() {
  cmpVenues = [null,null,null,null,null];
  cmpHistory = {};
  cmpClearSearch();
  var input = document.getElementById('cmp-search-input');
  if (input) input.value = '';
  document.getElementById('cmp-selected-list').style.display='none';
  document.getElementById('cmp-chips').innerHTML='';
  document.getElementById('cmp-result').style.display='none';
  document.getElementById('cmp-status').style.display='none';
  document.getElementById('cmp-run-btn').disabled = true;
  document.getElementById('cmp-sel-count').textContent = '';
}

function runComparison() {
  var selected = cmpVenues.filter(function(v){return v!==null;});
  if (selected.length < 2) return;
  var status = document.getElementById('cmp-status');
  status.style.display = 'block';
  status.textContent = 'Fetching history for ' + selected.length + ' venue(s)…';
  document.getElementById('cmp-result').style.display = 'none';
  var promises = selected.map(function(v) {
    var where = "upper(location_name)='" + (v.location_name||'').toUpperCase().replace(/'/g,"''") + "'" +
      " AND location_zip='" + (v.location_zip||'') + "'";
    var url = 'https://data.texas.gov/resource/naix-2893.json?$where=' + encodeURIComponent(where) +
      '&$select=total_receipts,obligation_end_date_yyyymmdd&$limit=200&$order=obligation_end_date_yyyymmdd DESC';
    return fetch(url).then(function(r){return r.json();}).then(function(data){
      cmpHistory[cmpKey(v)] = data;
    });
  });
  Promise.all(promises).then(function() {
    status.style.display = 'none';
    renderComparison(selected);
  }).catch(function(e){
    status.textContent = 'Error: ' + e.message;
  });
}


function renderComparison(selected) {
  var grid = document.getElementById('cmp-grid');
  grid.innerHTML = '';

  // Collect all periods across all venues
  var periodSet = {};
  selected.forEach(function(v) {
    var hist = cmpHistory[cmpKey(v)] || [];
    hist.forEach(function(r) {
      var p = r.obligation_end_date_yyyymmdd;
      if (p) periodSet[p] = true;
    });
  });

  // Sort periods newest first
  var periods = Object.keys(periodSet).sort().reverse();
  var mNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];

  function periodLabel(iso) {
    var d = new Date(iso);
    return mNames[d.getUTCMonth()] + ' ' + d.getUTCFullYear();
  }

  // Build lookup: venue -> period -> amount
  var lookup = {};
  selected.forEach(function(v) {
    var k = cmpKey(v);
    lookup[k] = {};
    (cmpHistory[k]||[]).forEach(function(r) {
      if (r.obligation_end_date_yyyymmdd)
        lookup[k][r.obligation_end_date_yyyymmdd] = parseFloat(r.total_receipts)||0;
    });
  });

  // Header row
  var thead = document.createElement('thead');
  var htr = document.createElement('tr');
  var th0 = document.createElement('th'); th0.textContent = 'Period'; htr.appendChild(th0);
  selected.forEach(function(v) {
    var th = document.createElement('th');
    th.textContent = (v.location_name||'').length > 20 ? (v.location_name||'').slice(0,20)+'…' : (v.location_name||'');
    th.title = v.location_name || '';
    htr.appendChild(th);
  });
  thead.appendChild(htr);
  grid.appendChild(thead);

  // Body rows
  var tbody = document.createElement('tbody');
  periods.forEach(function(p) {
    var tr = document.createElement('tr');
    var td0 = document.createElement('td'); td0.textContent = periodLabel(p); tr.appendChild(td0);

    // Find max value for this period to highlight best
    var rowVals = selected.map(function(v){ return lookup[cmpKey(v)][p]; });
    var maxVal  = Math.max.apply(null, rowVals.filter(function(x){return x!==undefined;}));

    selected.forEach(function(v) {
      var td = document.createElement('td');
      var val = lookup[cmpKey(v)][p];
      if (val === undefined) {
        td.textContent = '—';
        td.className = 'no-data';
      } else {
        td.textContent = fmtMoney(val, false);
        if (val === maxVal && selected.length > 1) td.className = 'best';
      }
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });

  // Totals + avg rows
  var tfoot = document.createElement('tfoot');
  var totalTr = document.createElement('tr');
  totalTr.className = 'cmp-total-row';
  var ttd0 = document.createElement('td'); ttd0.textContent = 'Total'; totalTr.appendChild(ttd0);
  selected.forEach(function(v) {
    var td = document.createElement('td');
    var vals = Object.values(lookup[cmpKey(v)]);
    td.textContent = fmtMoney(vals.reduce(function(a,b){return a+b;},0), false);
    totalTr.appendChild(td);
  });
  tfoot.appendChild(totalTr);

  var avgTr = document.createElement('tr');
  avgTr.className = 'cmp-avg-row';
  var atd0 = document.createElement('td'); atd0.textContent = 'Avg/mo'; avgTr.appendChild(atd0);
  selected.forEach(function(v) {
    var td = document.createElement('td');
    var vals = Object.values(lookup[cmpKey(v)]);
    td.textContent = vals.length ? fmtMoney(vals.reduce(function(a,b){return a+b;},0)/vals.length, false) : '—';
    avgTr.appendChild(td);
  });
  tfoot.appendChild(avgTr);
  grid.appendChild(tbody);
  grid.appendChild(tfoot);

  document.getElementById('cmp-period-label').textContent =
    periods.length + ' periods · ' + selected.length + ' venues';
  document.getElementById('cmp-result').style.display = 'block';
}

function exportCompareCSV() {
  var grid = document.getElementById('cmp-grid');
  var rows = [];
  grid.querySelectorAll('tr').forEach(function(tr) {
    var row = [];
    tr.querySelectorAll('th,td').forEach(function(cell) { row.push('"'+cell.textContent+'"'); });
    rows.push(row.join(','));
  });
  var blob = new Blob([rows.join('\n')], {type:'text/csv'});
  var a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = 'venue_comparison.csv';
  a.click();
}


```

(Note the two blank lines after the closing `}` before `// Tab switching` — match exactly, don't collapse to one.)

- [ ] **Step 5: Verify the app still loads with no dangling references**

```bash
grep -in "compare\|cmp-\|cmpVenues\|cmpHistory" static/texas_alcohol_explorer.html
```

Expected: no output (the two pre-existing `localeCompare(` calls elsewhere in the file are gone too, since they lived inside the deleted block — confirm with a second check):

```bash
grep -n "localeCompare" static/texas_alcohol_explorer.html
```

Expected: no output (both occurrences were inside the deleted Compare JS; all other `sort()`/compare logic in the file uses numeric subtraction, not `localeCompare`).

- [ ] **Step 6: Manually verify in browser**

Use `preview_start` with name `texas-alcohol-explorer`, then `navigate` to `http://localhost:8000/static/texas_alcohol_explorer.html`. Confirm:
- Only two tabs show: Explorer, Nearby (no Compare tab, no JS console errors)
- Explorer's "Run query" still works and returns results (click a row, confirm the history modal opens)
- Nearby's search still works

Check `read_console_messages` for any errors (there should be none — the only error the missing Compare tab button would produce is silent, since nothing calls `switchTab('compare')` anymore).

- [ ] **Step 7: Commit**

```bash
cd ~/personal-dashboard && git add static/texas_alcohol_explorer.html && git commit -m "Remove Compare tab (CSS, markup, JS)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 3: Scaffold the Openings tab shell

**Files:**
- Modify: `static/texas_alcohol_explorer.html`

Add the tab button, page markup, and JS state/init — no query logic yet. This task should produce a tab that switches correctly and shows the empty-state placeholder.

- [ ] **Step 1: Add the Openings tab button**

In the nav bar, right after the `tab-map` button (which now immediately precedes where `tab-compare` used to be), add:

```html
  <button class="tab" id="tab-openings" onclick="switchTab('openings')">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
    Openings
  </button>
```

(This reuses the exact same SVG icon Compare used, per the design spec — no new artwork.)

- [ ] **Step 2: Add the Openings page markup**

Right after the closing `</div>` of `map-page` (immediately before `<!-- ── Modal ── -->`), add:

```html
<!-- ── Openings ── -->
<div id="openings-page" class="page">
  <div class="hdr">
    <div class="hdr-eyebrow">Texas Open Data · TABC License Information</div>
    <h1 class="hdr-title"><strong>Openings</strong> <em>&amp; Closures</em></h1>
  </div>
  <div class="wrap">
    <div class="fcard">
      <div class="section-label">Filters</div>
      <div style="display:grid;grid-template-columns:2fr 1fr;gap:10px;margin-bottom:12px;">
        <div>
          <div class="flabel">City</div>
          <select id="op-city" class="sel" style="width:100%"></select>
        </div>
        <div>
          <div class="flabel">ZIP</div>
          <input id="op-zip" type="text" inputmode="numeric" placeholder="75225" autocomplete="off" />
        </div>
      </div>
      <div style="margin-bottom:12px;">
        <div class="flabel">Period</div>
        <div class="period-row">
          <select id="op-month" class="sel">
            <option value="01">January</option><option value="02">February</option><option value="03">March</option>
            <option value="04">April</option><option value="05">May</option><option value="06">June</option>
            <option value="07">July</option><option value="08">August</option><option value="09">September</option>
            <option value="10">October</option><option value="11">November</option><option value="12">December</option>
          </select>
          <select id="op-year" class="sel"></select>
        </div>
      </div>
      <div class="btn-row">
        <button class="btn-run" id="op-run-btn" onclick="runOpenings()">Run query</button>
        <button class="btn-clear" onclick="clearOpenings()">Clear</button>
        <span class="rcount" id="op-summary"></span>
      </div>
    </div>

    <div class="err" id="op-err-box"></div>

    <div class="placeholder" id="op-placeholder">
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
      <p>Set filters and tap <strong>Run query</strong><br>to see new &amp; closed MB permits</p>
    </div>

    <div id="op-results" style="display:none;">
      <div class="tbl-hdr">
        <span class="tbl-hint" id="op-new-hint">New Permits</span>
        <button class="btn-sm" onclick="exportOpeningsCSV('new')">Export CSV</button>
      </div>
      <div class="tbl-wrap">
        <table>
          <thead><tr><th>Location</th><th>City</th><th>Address</th><th>Issue Date</th><th>Owner</th></tr></thead>
          <tbody id="op-new-tbody"></tbody>
        </table>
      </div>

      <div class="tbl-hdr" style="margin-top:20px;">
        <span class="tbl-hint" id="op-closed-hint">Recently Closed</span>
        <button class="btn-sm" onclick="exportOpeningsCSV('closed')">Export CSV</button>
      </div>
      <div class="tbl-wrap">
        <table>
          <thead><tr><th>Location</th><th>City</th><th>Address</th><th>Status</th><th>Status Change Date</th><th>Owner</th></tr></thead>
          <tbody id="op-closed-tbody"></tbody>
        </table>
      </div>
    </div>
  </div>
</div>

```

No new CSS is needed — every class used above (`hdr`, `hdr-eyebrow`, `hdr-title`, `wrap`, `fcard`, `section-label`, `flabel`, `sel`, `period-row`, `btn-row`, `btn-run`, `btn-clear`, `rcount`, `err`, `placeholder`, `tbl-hdr`, `tbl-hint`, `btn-sm`, `tbl-wrap`, plain `table`, `dim`, `pos`, `neg`) is already defined globally and used by Explorer/Nearby.

- [ ] **Step 3: Add Openings JS state and dropdown init**

Add this block where the old Compare JS block used to live (right before the `// Tab switching` comment):

```javascript
// ---- Openings tracker ----
var LICENSE_API = 'https://data.texas.gov/resource/7hf9-qc9f.json';
var opNewRows = [], opClosedRows = [];

(function() {
  var yr = new Date().getFullYear();
  var ySel = document.getElementById('op-year');
  for (var y = yr; y >= 2006; y--) {
    var o = document.createElement('option');
    o.value = String(y); o.textContent = String(y);
    ySel.appendChild(o);
  }

  // Default to 2 months ago, matching Explorer's default (data updates daily,
  // but 2-months-back keeps a full month's worth of issuances/closures visible by default)
  var now = new Date();
  now.setMonth(now.getMonth() - 2);
  var defYear = String(now.getFullYear());
  var defMonth = String(now.getMonth() + 1).padStart(2, '0');
  ySel.value = defYear;
  var mSel = document.getElementById('op-month');
  for (var i = 0; i < mSel.options.length; i++) {
    if (mSel.options[i].value === defMonth) { mSel.selectedIndex = i; break; }
  }

  var citySel = document.getElementById('op-city');
  var allOpt = document.createElement('option');
  allOpt.value = ''; allOpt.textContent = 'All cities';
  citySel.appendChild(allOpt);
  TOP_METRO_CITIES.slice().sort().forEach(function(c) {
    var opt = document.createElement('option');
    opt.value = c;
    opt.textContent = c.charAt(0) + c.slice(1).toLowerCase();
    citySel.appendChild(opt);
  });
})();

function opFmtDate(v) {
  if (!v) return '—';
  var s = String(v).replace(/T.*/,'');
  var parts = s.split('-');
  if (parts.length === 3) return parts[1] + '/' + parts[2] + '/' + parts[0];
  return v;
}

function clearOpenings() {
  document.getElementById('op-city').value = '';
  document.getElementById('op-zip').value = '';
  ['op-month','op-year'].forEach(function(id){ document.getElementById(id).selectedIndex = 0; });
  opNewRows = []; opClosedRows = [];
  document.getElementById('op-results').style.display = 'none';
  document.getElementById('op-err-box').style.display = 'none';
  document.getElementById('op-summary').textContent = '';
  document.getElementById('op-placeholder').style.display = 'block';
}

```

Note: `TOP_METRO_CITIES` (defined earlier in the file, used by Explorer's city dropdown) is a flat array of ~150 Texas city names — reused as-is here rather than rebuilding Explorer's grouped multi-select widget, since a single-select "narrow to one city" control is all this tab needs.

- [ ] **Step 4: Verify the shell in browser**

`navigate` to `http://localhost:8000/static/texas_alcohol_explorer.html`, then:
- Click the "Openings" tab, confirm the page switches (placeholder text shows, filter card renders)
- `read_page` and confirm `op-city` select has "All cities" plus real city names, `op-year` has years from current year down to 2006, `op-month` defaults to 2-months-ago
- Check `read_console_messages` for errors — expect none (clicking "Run query" at this point will throw since `runOpenings` doesn't exist yet — that's expected and fixed in Task 4; don't click it yet)

- [ ] **Step 5: Commit**

```bash
cd ~/personal-dashboard && git add static/texas_alcohol_explorer.html && git commit -m "Add Openings tab shell (markup, tab button, filter init)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 4: Implement the query and render logic

**Files:**
- Modify: `static/texas_alcohol_explorer.html`

- [ ] **Step 1: Add `opDateRange`, `runOpenings`, `currentOpFilterLabel`, and `renderOpenings`**

Add these functions immediately after `clearOpenings()` (added in Task 3):

```javascript
function opDateRange(month, year) {
  var y = parseInt(year, 10), m = parseInt(month, 10);
  var ny = m === 12 ? y + 1 : y;
  var nm = m === 12 ? 1 : m + 1;
  var pad = String(nm).padStart(2, '0');
  return {
    start: year + '-' + month + '-01T00:00:00.000',
    end: ny + '-' + pad + '-01T00:00:00.000'
  };
}

function currentOpFilterLabel() {
  var city = document.getElementById('op-city').value;
  return city ? (city.charAt(0) + city.slice(1).toLowerCase()) : '';
}

function runOpenings() {
  var month = document.getElementById('op-month').value;
  var year = document.getElementById('op-year').value;
  var city = document.getElementById('op-city').value;
  var zip = document.getElementById('op-zip').value.trim();
  var range = opDateRange(month, year);

  document.getElementById('op-placeholder').style.display = 'none';
  document.getElementById('op-err-box').style.display = 'none';
  document.getElementById('op-results').style.display = 'none';
  document.getElementById('op-summary').textContent = 'Loading…';

  var newWhere = "license_type='MB' AND original_issue_date>='" + range.start + "' AND original_issue_date<'" + range.end + "'";
  var closedWhere = "license_type='MB' AND (primary_status='Cancelled' OR primary_status='Surrendered') AND status_change_date>='" + range.start + "' AND status_change_date<'" + range.end + "'";
  if (city) {
    var cityEsc = city.toUpperCase().replace(/'/g,"''");
    newWhere += " AND upper(city)='" + cityEsc + "'";
    closedWhere += " AND upper(city)='" + cityEsc + "'";
  }
  if (zip) {
    var zipEsc = zip.replace(/'/g,"''");
    newWhere += " AND starts_with(zip,'" + zipEsc + "')";
    closedWhere += " AND starts_with(zip,'" + zipEsc + "')";
  }

  var newUrl = LICENSE_API + '?$limit=1000&$order=original_issue_date+DESC&$select=trade_name,owner,address,city,zip,original_issue_date&$where=' + encodeURIComponent(newWhere);
  var closedUrl = LICENSE_API + '?$limit=1000&$order=status_change_date+DESC&$select=trade_name,owner,address,city,zip,primary_status,status_change_date&$where=' + encodeURIComponent(closedWhere);

  Promise.all([
    fetch(newUrl).then(function(r){ if(!r.ok) throw new Error('API error '+r.status); return r.json(); }),
    fetch(closedUrl).then(function(r){ if(!r.ok) throw new Error('API error '+r.status); return r.json(); })
  ]).then(function(results) {
    opNewRows = results[0];
    opClosedRows = results[1];
    document.getElementById('op-summary').textContent = opNewRows.length + ' new · ' + opClosedRows.length + ' closed';
    renderOpenings(month, year);
    document.getElementById('op-results').style.display = 'block';
  }).catch(function(e) {
    document.getElementById('op-err-box').textContent = 'Error: ' + e.message;
    document.getElementById('op-err-box').style.display = 'block';
    document.getElementById('op-summary').textContent = '';
  });
}

function renderOpenings(month, year) {
  var mNames = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  var periodLabel = mNames[parseInt(month,10)-1] + ' ' + year;
  var filterSuffix = currentOpFilterLabel() ? ' for ' + currentOpFilterLabel() : '';

  document.getElementById('op-new-hint').textContent = 'New Permits — ' + periodLabel;
  document.getElementById('op-closed-hint').textContent = 'Recently Closed — ' + periodLabel;

  var newBody = document.getElementById('op-new-tbody');
  newBody.innerHTML = '';
  if (!opNewRows.length) {
    newBody.innerHTML = '<tr><td colspan="5" class="dim">No new MB permits issued in ' + periodLabel + filterSuffix + '.</td></tr>';
  } else {
    opNewRows.forEach(function(r) {
      var tr = document.createElement('tr');
      var args = [r.trade_name||'', r.owner||'', '', r.city||'', (r.zip||'').slice(0,5), r.address||''];
      tr.addEventListener('click', function(){ openHistory.apply(null, args); });
      tr.innerHTML =
        '<td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;font-weight:500">'+(r.trade_name||'—')+'</td>'+
        '<td>'+(r.city||'—')+'</td>'+
        '<td class="dim">'+(r.address||'—')+'</td>'+
        '<td class="dim">'+opFmtDate(r.original_issue_date)+'</td>'+
        '<td class="dim">'+(r.owner||'—')+'</td>';
      newBody.appendChild(tr);
    });
  }

  var closedBody = document.getElementById('op-closed-tbody');
  closedBody.innerHTML = '';
  if (!opClosedRows.length) {
    closedBody.innerHTML = '<tr><td colspan="6" class="dim">No closures in ' + periodLabel + filterSuffix + '.</td></tr>';
  } else {
    opClosedRows.forEach(function(r) {
      var tr = document.createElement('tr');
      var args = [r.trade_name||'', r.owner||'', '', r.city||'', (r.zip||'').slice(0,5), r.address||''];
      tr.addEventListener('click', function(){ openHistory.apply(null, args); });
      tr.innerHTML =
        '<td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;font-weight:500">'+(r.trade_name||'—')+'</td>'+
        '<td>'+(r.city||'—')+'</td>'+
        '<td class="dim">'+(r.address||'—')+'</td>'+
        '<td class="neg">'+(r.primary_status||'—')+'</td>'+
        '<td class="dim">'+opFmtDate(r.status_change_date)+'</td>'+
        '<td class="dim">'+(r.owner||'—')+'</td>';
      closedBody.appendChild(tr);
    });
  }
}

```

Notes on why this differs slightly from patterns elsewhere in the file:
- `opFmtDate` (not the existing `fmtDate`) is used because `fmtDate` truncates to MM/YYYY (fine for monthly receipts periods, which are always the 1st of a month) — permit issue dates and status-change dates carry a real day-of-month that matters here.
- `openHistory` is called with `taxpayerName = r.owner` and `locationName = r.trade_name` — this matches how the receipts dataset's `taxpayer_name`/`location_name` map conceptually to the license dataset's `owner`/`trade_name` (verified against real data: e.g. AT&T Stadium's `location_name` is "AT&T STADIUM" with `taxpayer_name` "LEGENDS HOSPITALITY, LLC" — same owner/trade-name split). The `rowPeriod` argument (3rd param) is passed as `''` since `openHistory` never actually reads it (confirmed by inspection — it's an unused parameter in every other call site too).
- ZIP from the license dataset is 9-digit unformatted (e.g. `"770816967"`); `.slice(0,5)` before passing to `openHistory` matches the 5-digit ZIP the receipts dataset (and `openHistory`'s query) expects.

- [ ] **Step 2: Verify against real data in browser**

`navigate` to the app, click Openings, set Month=June, Year=2026, City="All cities", ZIP blank, click "Run query". Confirm via `get_page_text`:
- Summary line shows a non-zero "new" count and a non-zero "closed" count
- New Permits table includes rows (e.g. venues like "La Table De Sophia" in McKinney should appear — confirmed present in this dataset as of this plan's writing)
- Recently Closed table includes rows with status "Surrendered" or "Cancelled"

Then click a row in each table and confirm the existing history modal opens (`document.querySelector('.modal-overlay.open')` should exist via `javascript_tool`). For a New Permits row this may show "No history found." in the modal body — that's expected (the venue hasn't started reporting sales yet) and confirms the wiring is correct rather than broken.

Check `read_console_messages` for errors — expect none.

- [ ] **Step 3: Commit**

```bash
cd ~/personal-dashboard && git add static/texas_alcohol_explorer.html && git commit -m "Implement Openings query, render, and modal wiring

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 5: Verify empty-state handling

**Files:** none (verification only — the empty-state code was already written in Task 4's `renderOpenings`)

- [ ] **Step 1: Trigger a genuinely empty result in browser**

Set City to a small city unlikely to have any MB permit activity in a given month (e.g. "Wimberley") with Month/Year set to a period already confirmed to have results statewide (June 2026). Click "Run query".

- [ ] **Step 2: Confirm the empty-state message renders correctly**

Via `get_page_text`, confirm the New Permits and/or Recently Closed sections show text like "No new MB permits issued in June 2026 for Wimberley." (not a blank table, not a JS error). Check `read_console_messages` for errors.

If both sections happen to have real activity for that city/month (small chance), pick a different small city and retry rather than treating it as a failure — the goal is confirming the empty-state code path renders correctly, not a specific city.

- [ ] **Step 3: No commit needed** (verification-only task, no code changed)

---

### Task 6: Implement CSV export

**Files:**
- Modify: `static/texas_alcohol_explorer.html`

- [ ] **Step 1: Add `exportOpeningsCSV`**

Add this function immediately after `renderOpenings` (added in Task 4):

```javascript
function exportOpeningsCSV(section) {
  var rows = section === 'new' ? opNewRows : opClosedRows;
  if (!rows.length) return;
  var headers = section === 'new'
    ? ['Location','City','Address','ZIP','Issue Date','Owner']
    : ['Location','City','Address','ZIP','Status','Status Change Date','Owner'];
  var out = [headers];
  rows.forEach(function(r) {
    if (section === 'new') {
      out.push([r.trade_name||'', r.city||'', r.address||'', (r.zip||'').slice(0,5), opFmtDate(r.original_issue_date), r.owner||'']);
    } else {
      out.push([r.trade_name||'', r.city||'', r.address||'', (r.zip||'').slice(0,5), r.primary_status||'', opFmtDate(r.status_change_date), r.owner||'']);
    }
  });
  var month = document.getElementById('op-month').value, year = document.getElementById('op-year').value;
  downloadCSV(out, 'openings_'+section+'_'+year+'-'+month+'.csv');
}

```

This reuses the existing `downloadCSV(rows, filename)` helper (already used by `exportMainCSV`/`exportModalCSV`) rather than duplicating the CSV-building/download-anchor logic the old `exportCompareCSV` had.

- [ ] **Step 2: Verify in browser**

With results already loaded from Task 4's verification, use `javascript_tool` to call `exportOpeningsCSV('new')` and `exportOpeningsCSV('closed')` directly (a real click-triggered file save can't be observed through the browser tool, but the function executing without throwing, plus inspecting the generated data URI, confirms correctness):

```javascript
(function(){
  var origClick = HTMLAnchorElement.prototype.click;
  var captured = null;
  HTMLAnchorElement.prototype.click = function(){ captured = this.href; };
  exportOpeningsCSV('new');
  HTMLAnchorElement.prototype.click = origClick;
  return captured ? decodeURIComponent(captured.slice(captured.indexOf(',')+1)).slice(0,300) : 'no anchor created';
})();
```

Expected: a string starting with `Location,City,Address,ZIP,Issue Date,Owner` followed by real row data, not an error and not `"no anchor created"`. Repeat for `exportOpeningsCSV('closed')` and confirm the `Status` column header appears with real status values.

Check `read_console_messages` for errors.

- [ ] **Step 3: Commit**

```bash
cd ~/personal-dashboard && git add static/texas_alcohol_explorer.html && git commit -m "Add CSV export for Openings tab

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 7: Full regression pass and merge

**Files:** none (verification + git merge)

- [ ] **Step 1: Full regression pass in browser**

`navigate` to `http://localhost:8000/static/texas_alcohol_explorer.html` fresh (hard reload). For each tab, repeat the same checks performed earlier this session:

- **Explorer:** Run a query (e.g. June 2026), confirm records/top-10-cities/table render, click a row, confirm modal opens with period-comparison table.
- **Nearby:** Search a ZIP (e.g. 75225), confirm results render sorted by proximity.
- **Openings:** Run a query (June 2026, all cities), confirm both New and Closed tables render with real rows, click a row in each, confirm modal opens, run Export CSV on both sections.

After each step, check `read_console_messages` (expect zero errors across the whole pass) and `read_network_requests` for any failed (non-200) requests.

- [ ] **Step 2: Diff review**

```bash
cd ~/personal-dashboard && git diff main --stat
```

Expected: one file changed (`static/texas_alcohol_explorer.html`), with roughly proportional insertions/deletions (Compare removed, Openings added — not a runaway diff touching unrelated code).

- [ ] **Step 3: Merge to main**

```bash
cd ~/personal-dashboard && git checkout main && git merge feature/openings-tracker
```

Expected: fast-forward or clean merge, no conflicts (no other work has touched `static/texas_alcohol_explorer.html` on `main` since branching).

- [ ] **Step 4: Delete the feature branch**

```bash
cd ~/personal-dashboard && git branch -d feature/openings-tracker
```
