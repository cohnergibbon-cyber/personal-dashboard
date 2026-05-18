
"""
patch_compare.py - patches Compare tab: 5 input boxes with live dropdowns
Run from personal-dashboard root: python patch_compare.py
"""
import re, sys, os

HTML_PATH = os.path.join("static", "texas_alcohol_explorer.html")

# ── 1. CSS ────────────────────────────────────────────────────────────────────
OLD_CSS = ".cmp-grid td.best { color:var(--pos); font-weight:700; }"
NEW_CSS = """.cmp-grid td.best { color:var(--pos); font-weight:700; }

/* Compare slots */
.cmp-slot { margin-bottom:8px; position:relative; }
.cmp-slot-inner { position:relative; display:flex; align-items:center; }
.cmp-slot-input { flex:1; padding:10px 36px 10px 12px; border:1.5px solid var(--border2); border-radius:var(--r-sm); background:var(--s2); color:var(--text); font-size:14px; font-family:var(--sans); outline:none; transition:border-color 0.15s; box-sizing:border-box; width:100%; }
.cmp-slot-input:focus { border-color:var(--accent); }
.cmp-slot-input.selected { border-color:var(--pos); background:var(--pos-dim); }
.cmp-slot-input::placeholder { color:var(--text3); }
.cmp-slot-check { position:absolute; right:10px; color:var(--pos); font-size:15px; font-weight:700; display:none; pointer-events:none; }
.cmp-slot-check.visible { display:block; }
.cmp-slot-dd { display:none; position:absolute; top:calc(100% + 2px); left:0; right:0; background:var(--s1); border:1px solid var(--border2); border-radius:var(--r-sm); box-shadow:0 6px 20px rgba(0,0,0,0.14); z-index:200; max-height:220px; overflow-y:auto; }
.cmp-slot-dd.open { display:block; }
.cmp-dd-item { padding:10px 12px; cursor:pointer; border-bottom:1px solid var(--border); }
.cmp-dd-item:last-child { border-bottom:none; }
.cmp-dd-item:hover, .cmp-dd-item:active { background:var(--s2); }
.cmp-dd-name { font-size:13px; font-weight:600; color:var(--text); }
.cmp-dd-addr { font-size:11px; color:var(--text3); margin-top:2px; }
.cmp-dd-empty { padding:10px 12px; font-size:12px; color:var(--text3); }"""

# ── 2. Compare page HTML ──────────────────────────────────────────────────────
NEW_COMPARE_HTML = """<!-- \u2500\u2500 Compare \u2500\u2500 -->
<div id="compare-page" class="page">
  <div class="hdr">
    <div class="hdr-eyebrow">Texas Open Data \u00b7 TABC</div>
    <h1 class="hdr-title"><strong>Venue</strong> <em>Comparison</em></h1>
  </div>
  <div class="wrap">
    <div class="fcard">
      <div class="section-label" style="margin-bottom:10px">Type a venue name \u2014 select from results below each box</div>
      <div id="cmp-slots">
        <div class="cmp-slot" data-slot="0">
          <div class="cmp-slot-inner">
            <input class="cmp-slot-input" type="text" placeholder="Venue 1" oninput="cmpType(this,0)" autocomplete="off">
            <span class="cmp-slot-check" id="cmp-check-0">\u2713</span>
          </div>
          <div class="cmp-slot-dd" id="cmp-dd-0"></div>
        </div>
        <div class="cmp-slot" data-slot="1">
          <div class="cmp-slot-inner">
            <input class="cmp-slot-input" type="text" placeholder="Venue 2" oninput="cmpType(this,1)" autocomplete="off">
            <span class="cmp-slot-check" id="cmp-check-1">\u2713</span>
          </div>
          <div class="cmp-slot-dd" id="cmp-dd-1"></div>
        </div>
        <div class="cmp-slot" data-slot="2">
          <div class="cmp-slot-inner">
            <input class="cmp-slot-input" type="text" placeholder="Venue 3 (optional)" oninput="cmpType(this,2)" autocomplete="off">
            <span class="cmp-slot-check" id="cmp-check-2">\u2713</span>
          </div>
          <div class="cmp-slot-dd" id="cmp-dd-2"></div>
        </div>
        <div class="cmp-slot" data-slot="3">
          <div class="cmp-slot-inner">
            <input class="cmp-slot-input" type="text" placeholder="Venue 4 (optional)" oninput="cmpType(this,3)" autocomplete="off">
            <span class="cmp-slot-check" id="cmp-check-3">\u2713</span>
          </div>
          <div class="cmp-slot-dd" id="cmp-dd-3"></div>
        </div>
        <div class="cmp-slot" data-slot="4">
          <div class="cmp-slot-inner">
            <input class="cmp-slot-input" type="text" placeholder="Venue 5 (optional)" oninput="cmpType(this,4)" autocomplete="off">
            <span class="cmp-slot-check" id="cmp-check-4">\u2713</span>
          </div>
          <div class="cmp-slot-dd" id="cmp-dd-4"></div>
        </div>
      </div>
      <div style="display:flex;align-items:center;gap:10px;margin-top:14px">
        <button class="btn-run" id="cmp-run-btn" onclick="runComparison()" disabled>Compare</button>
        <button class="btn-clear" onclick="clearComparison()">Clear</button>
        <span id="cmp-sel-count" style="font-family:var(--mono);font-size:11px;color:var(--text3);margin-left:4px;"></span>
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
</div>"""

# ── 3. JS ─────────────────────────────────────────────────────────────────────
NEW_JS = """var cmpSlots = [null, null, null, null, null];
var cmpHistory = {};
var cmpTimers = {};

function cmpKey(v) { return (v.location_name||'')+'|'+(v.location_zip||''); }

function cmpType(input, slot) {
  var q = input.value.trim();
  var dd = document.getElementById('cmp-dd-' + slot);
  if (cmpSlots[slot]) {
    cmpSlots[slot] = null;
    input.classList.remove('selected');
    document.getElementById('cmp-check-' + slot).classList.remove('visible');
    updateCmpBtn();
  }
  clearTimeout(cmpTimers[slot]);
  if (q.length < 2) { dd.classList.remove('open'); dd.innerHTML=''; return; }
  cmpTimers[slot] = setTimeout(function() {
    var url = 'https://data.texas.gov/resource/naix-2893.json' +
      '?$select=location_name,location_city,location_address,location_zip' +
      '&$where=' + encodeURIComponent("upper(location_name) like '%" + q.toUpperCase().replace(/'/g,"''") + "%' AND total_receipts>=25000") +
      '&$limit=10&$order=location_name';
    fetch(url).then(function(r){return r.json();}).then(function(data){
      var seen={}, results=[];
      data.forEach(function(r){
        var k=(r.location_name||'')+'|'+(r.location_zip||'');
        if(!seen[k]){seen[k]=true;results.push(r);}
      });
      dd.innerHTML='';
      if (!results.length) { dd.innerHTML='<div class="cmp-dd-empty">No results</div>'; dd.classList.add('open'); return; }
      results.forEach(function(r) {
        var item = document.createElement('div');
        item.className = 'cmp-dd-item';
        item.innerHTML = '<div class="cmp-dd-name">'+(r.location_name||'')+'</div>'+
          '<div class="cmp-dd-addr">'+(r.location_address||'')+(r.location_city?', '+r.location_city:'')+'</div>';
        item.addEventListener('mousedown', function(e){ e.preventDefault(); });
        item.addEventListener('click', function(){
          cmpSlots[slot] = r;
          input.value = r.location_name || '';
          input.classList.add('selected');
          document.getElementById('cmp-check-' + slot).classList.add('visible');
          dd.classList.remove('open'); dd.innerHTML='';
          updateCmpBtn();
        });
        dd.appendChild(item);
      });
      dd.classList.add('open');
    }).catch(function(){ dd.classList.remove('open'); });
  }, 280);
}

document.addEventListener('click', function(e){
  if (!e.target.closest('.cmp-slot')) {
    document.querySelectorAll('.cmp-slot-dd').forEach(function(d){ d.classList.remove('open'); });
  }
});

function updateCmpBtn() {
  var count = cmpSlots.filter(function(v){ return v!==null; }).length;
  var btn = document.getElementById('cmp-run-btn');
  var lbl = document.getElementById('cmp-sel-count');
  btn.disabled = count < 2;
  lbl.textContent = count >= 2 ? count + ' selected' : (count === 1 ? '1 selected \u2014 need 1 more' : '');
}

function clearComparison() {
  cmpSlots = [null,null,null,null,null]; cmpHistory = {};
  document.querySelectorAll('.cmp-slot-input').forEach(function(i){ i.value=''; i.classList.remove('selected'); });
  document.querySelectorAll('.cmp-slot-check').forEach(function(c){ c.classList.remove('visible'); });
  document.querySelectorAll('.cmp-slot-dd').forEach(function(d){ d.classList.remove('open'); d.innerHTML=''; });
  document.getElementById('cmp-result').style.display='none';
  document.getElementById('cmp-status').style.display='none';
  document.getElementById('cmp-sel-count').textContent='';
  document.getElementById('cmp-run-btn').disabled=true;
}

function runComparison() {
  var selected = cmpSlots.filter(function(v){ return v!==null; });
  if (selected.length < 2) return;
  var status = document.getElementById('cmp-status');
  status.style.display='block';
  status.textContent='Fetching history for '+selected.length+' venue(s)\u2026';
  document.getElementById('cmp-result').style.display='none';
  var promises = selected.map(function(v){
    var where="upper(location_name)='"+(v.location_name||'').toUpperCase().replace(/'/g,"''")+"' AND location_zip='"+(v.location_zip||'')+"'";
    var url='https://data.texas.gov/resource/naix-2893.json?$where='+encodeURIComponent(where)+
      '&$select=total_receipts,obligation_end_date_yyyymmdd&$limit=200&$order=obligation_end_date_yyyymmdd DESC';
    return fetch(url).then(function(r){return r.json();}).then(function(data){ cmpHistory[cmpKey(v)]=data; });
  });
  Promise.all(promises).then(function(){
    status.style.display='none'; renderComparison(selected);
  }).catch(function(e){ status.textContent='Error: '+e.message; });
}

"""

def patch(content):
    changes = 0

    # 1. CSS
    if OLD_CSS in content and 'cmp-slot-input' not in content:
        content = content.replace(OLD_CSS, NEW_CSS, 1)
        changes += 1; print("  [OK] CSS updated")
    else:
        print("  [SKIP] CSS (already patched or anchor missing)")

    # 2. HTML
    m = re.search(r'<!-- .*?Compare.*? -->\s*<div id="compare-page".*?(?=\n<!-- |\n</body>)', content, re.DOTALL)
    if m:
        content = content[:m.start()] + NEW_COMPARE_HTML + content[m.end():]
        changes += 1; print("  [OK] Compare HTML updated")
    else:
        print("  [SKIP] Compare HTML (not found)")

    # 3. JS — match from cmpSlots/cmpVenues/cmpVenuesPicked init through end of runComparison
    m = re.search(r'var cmp(?:Slots|Venues[a-zA-Z]*)\s*=.*?(?=\nfunction renderComparison)', content, re.DOTALL)
    if m:
        content = content[:m.start()] + NEW_JS + content[m.end():]
        changes += 1; print("  [OK] JS replaced")
    else:
        print("  [SKIP] JS (anchor not found)")

    return content, changes

def main():
    if not os.path.exists(HTML_PATH):
        print(f"ERROR: {HTML_PATH} not found. Run from personal-dashboard root.")
        import sys; sys.exit(1)
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"Patching {HTML_PATH} ({len(content):,} chars)...")
    content, changes = patch(content)
    with open(HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Done. {changes} change(s) applied.")

if __name__ == "__main__":
    main()
