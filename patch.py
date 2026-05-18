"""
patch_compare.py
Patches texas_alcohol_explorer.html with the new Compare tab:
  - Single search input -> dropdown results -> chip selection -> Compare button
Run from personal-dashboard root:
    python patch_compare.py
"""

import re, sys, os

HTML_PATH = os.path.join("static", "texas_alcohol_explorer.html")

# ── 1. New CSS (chip styles) ──────────────────────────────────────────────────
OLD_CSS_ANCHOR = ".cmp-grid td.best { color:var(--pos); font-weight:700; }"

NEW_CSS = """.cmp-grid td.best { color:var(--pos); font-weight:700; }

/* Compare search + chips */
.cmp-search-wrap { position:relative; }
.cmp-chip { display:flex; align-items:center; gap:8px; background:var(--accent-dim); border:1px solid var(--border2); border-radius:20px; padding:6px 10px 6px 14px; font-size:13px; font-weight:500; color:var(--text); margin-bottom:6px; }
.cmp-chip-name { flex:1; min-width:0; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.cmp-chip-addr { font-size:11px; color:var(--text3); flex-shrink:0; white-space:nowrap; margin-left:4px; }
.cmp-chip-rm { width:22px; height:22px; border-radius:50%; border:none; background:var(--s3); color:var(--text2); font-size:14px; cursor:pointer; display:flex; align-items:center; justify-content:center; flex-shrink:0; line-height:1; -webkit-tap-highlight-color:transparent; }
.cmp-chip-rm:hover { background:var(--neg-dim); color:var(--neg); }
.cmp-sug-item.already-added { opacity:0.45; pointer-events:none; }
.cmp-sug-item .sug-added-badge { display:none; font-size:10px; color:var(--pos); font-weight:600; margin-left:4px; }
.cmp-sug-item.already-added .sug-added-badge { display:inline; }"""

# ── 2. New Compare page HTML ──────────────────────────────────────────────────
OLD_HTML_ANCHOR = '<div class="section-label">Up to 5 venues</div>'
# Everything from that line through the closing </div> of fcard
OLD_HTML_FCARD_INNER = re.compile(
    r'<div class="section-label">Up to 5 venues</div>.*?</div>\s*\n\s*<div id="cmp-status"',
    re.DOTALL
)

NEW_HTML_FCARD_INNER = """<div class="section-label">Search &amp; select up to 5 venues</div>

      <!-- Single search input -->
      <div class="cmp-search-wrap">
        <input class="cmp-venue-input" id="cmp-search-input" type="text" placeholder="Type a venue name\u2026" oninput="cmpSearch(this)" autocomplete="off">
        <div class="cmp-suggestions" id="cmp-sug-main"></div>
      </div>

      <!-- Selected venue chips -->
      <div id="cmp-chips" style="display:none">
        <div class="section-label" style="margin-top:12px;margin-bottom:6px">Selected venues</div>
        <div id="cmp-chips-list"></div>
      </div>

      <div style="display:flex;gap:8px;margin-top:14px">
        <button class="btn-run" id="cmp-run-btn" onclick="runComparison()" disabled>Compare</button>
        <button class="btn-clear" onclick="clearComparison()">Clear</button>
      </div>
    </div>

    <div id="cmp-status" class="map-status" style="display:none"""

# ── 3. New JS ─────────────────────────────────────────────────────────────────
OLD_JS_ANCHOR = re.compile(
    r'var cmpSugTimers\s*=\s*\{\};.*?(?=function renderComparison)',
    re.DOTALL
)

NEW_JS = """// ── Compare: single search -> select -> chip flow ──
var cmpSearchTimer = null;

function cmpSearch(input) {
  var q = input.value.trim();
  var sugBox = document.getElementById('cmp-sug-main');
  clearTimeout(cmpSearchTimer);
  if (q.length < 2) { sugBox.style.display = 'none'; return; }
  cmpSearchTimer = setTimeout(function() {
    var url = 'https://data.texas.gov/resource/naix-2893.json' +
      '?$select=location_name,location_city,location_address,location_zip,taxpayer_name' +
      '&$where=' + encodeURIComponent("upper(location_name) like '%" + q.toUpperCase().replace(/'/g,"''") + "%' AND total_receipts>=25000") +
      '&$limit=12&$order=location_name';
    fetch(url).then(function(r){return r.json();}).then(function(data){
      var seen = {}, results = [];
      data.forEach(function(r) {
        var k = (r.location_name||'') + '|' + (r.location_zip||'');
        if (!seen[k]) { seen[k]=true; results.push(r); }
      });
      sugBox.innerHTML = '';
      if (!results.length) { sugBox.style.display='none'; return; }
      results.forEach(function(r) {
        var alreadyAdded = cmpVenues.some(function(v){ return v && cmpKey(v) === cmpKey(r); });
        var div = document.createElement('div');
        div.className = 'cmp-sug-item' + (alreadyAdded ? ' already-added' : '');
        div.innerHTML =
          '<div class="cmp-sug-name">' + (r.location_name||'') +
          '<span class="sug-added-badge">\u2713 Added</span></div>' +
          '<div class="cmp-sug-addr">' + (r.location_address||'') + (r.location_city ? ', '+r.location_city : '') + '</div>';
        if (!alreadyAdded) {
          div.onclick = function() {
            cmpAddVenue(r);
            sugBox.style.display = 'none';
            input.value = '';
          };
        }
        sugBox.appendChild(div);
      });
      sugBox.style.display = 'block';
    }).catch(function(){});
  }, 280);
}

function cmpAddVenue(venue) {
  if (cmpVenues.length >= 5) return;
  if (cmpVenues.some(function(v){ return v && cmpKey(v) === cmpKey(venue); })) return;
  cmpVenues.push(venue);
  renderChips();
}

function cmpRemoveVenue(key) {
  cmpVenues = cmpVenues.filter(function(v){ return cmpKey(v) !== key; });
  renderChips();
}

function renderChips() {
  var chipsSection = document.getElementById('cmp-chips');
  var chipsList = document.getElementById('cmp-chips-list');
  var runBtn = document.getElementById('cmp-run-btn');
  var searchInput = document.getElementById('cmp-search-input');
  chipsList.innerHTML = '';
  if (!cmpVenues.length) {
    chipsSection.style.display = 'none';
    runBtn.disabled = true;
    searchInput.disabled = false;
    searchInput.placeholder = 'Type a venue name\u2026';
    return;
  }
  chipsSection.style.display = 'block';
  runBtn.disabled = cmpVenues.length < 2;
  cmpVenues.forEach(function(v) {
    var chip = document.createElement('div');
    chip.className = 'cmp-chip';
    var city = v.location_city || '';
    chip.innerHTML =
      '<span class="cmp-chip-name">' + (v.location_name||'') + '</span>' +
      (city ? '<span class="cmp-chip-addr">' + city + '</span>' : '') +
      '<button class="cmp-chip-rm" title="Remove">\u00d7</button>';
    var key = cmpKey(v);
    chip.querySelector('.cmp-chip-rm').onclick = function() { cmpRemoveVenue(key); };
    chipsList.appendChild(chip);
  });
  if (cmpVenues.length >= 5) {
    searchInput.placeholder = 'Max 5 venues selected';
    searchInput.disabled = true;
  } else {
    searchInput.placeholder = 'Add another venue\u2026';
    searchInput.disabled = false;
  }
}

document.addEventListener('click', function(e) {
  if (!e.target.closest('.cmp-search-wrap')) {
    var s = document.getElementById('cmp-sug-main');
    if (s) s.style.display = 'none';
  }
});

function clearComparison() {
  cmpVenues = [];
  cmpHistory = {};
  var input = document.getElementById('cmp-search-input');
  if (input) { input.value = ''; input.disabled = false; input.placeholder = 'Type a venue name\u2026'; }
  var s = document.getElementById('cmp-sug-main');
  if (s) { s.innerHTML = ''; s.style.display = 'none'; }
  document.getElementById('cmp-chips').style.display = 'none';
  document.getElementById('cmp-chips-list').innerHTML = '';
  document.getElementById('cmp-result').style.display = 'none';
  document.getElementById('cmp-status').style.display = 'none';
  document.getElementById('cmp-run-btn').disabled = true;
}

function runComparison() {
  if (cmpVenues.length < 2) return;
  var status = document.getElementById('cmp-status');
  status.style.display = 'block';
  status.textContent = 'Fetching history for ' + cmpVenues.length + ' venue(s)\u2026';
  document.getElementById('cmp-result').style.display = 'none';
  var promises = cmpVenues.map(function(v) {
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
    renderComparison(cmpVenues);
  }).catch(function(e){
    status.textContent = 'Error: ' + e.message;
  });
}

"""

# ── 4. Also fix cmpVenues init from slot array to plain array ─────────────────
OLD_VENUES_INIT = "var cmpVenues   = [null,null,null,null,null]; // selected venue objects"
NEW_VENUES_INIT = "var cmpVenues   = [];   // selected venue objects (up to 5)"


def patch(content):
    changes = 0

    # CSS
    if OLD_CSS_ANCHOR in content:
        content = content.replace(OLD_CSS_ANCHOR, NEW_CSS, 1)
        changes += 1
        print("  [OK] CSS chip styles added")
    else:
        print("  [SKIP] CSS anchor not found (may already be patched)")

    # HTML fcard inner
    m = OLD_HTML_FCARD_INNER.search(content)
    if m:
        content = content[:m.start()] + NEW_HTML_FCARD_INNER + content[m.end():]
        changes += 1
        print("  [OK] Compare HTML updated to search+chip flow")
    else:
        print("  [SKIP] Compare HTML anchor not found (may already be patched)")

    # JS
    m = OLD_JS_ANCHOR.search(content)
    if m:
        content = content[:m.start()] + NEW_JS + content[m.end():]
        changes += 1
        print("  [OK] Compare JS replaced")
    else:
        print("  [SKIP] JS anchor not found (may already be patched)")

    # cmpVenues init
    if OLD_VENUES_INIT in content:
        content = content.replace(OLD_VENUES_INIT, NEW_VENUES_INIT, 1)
        changes += 1
        print("  [OK] cmpVenues init updated")
    else:
        print("  [SKIP] cmpVenues init not found (may already be patched)")

    return content, changes


def main():
    if not os.path.exists(HTML_PATH):
        print(f"ERROR: {HTML_PATH} not found. Run from personal-dashboard root.")
        sys.exit(1)

    with open(HTML_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"Patching {HTML_PATH} ({len(content):,} chars)...")
    content, changes = patch(content)

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Done. {changes} change(s) applied.")


if __name__ == "__main__":
    main()
