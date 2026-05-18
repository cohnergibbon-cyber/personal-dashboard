
"""
patch_compare.py - patches the Compare tab to multi-name search flow
Run from personal-dashboard root: python patch_compare.py
"""
import re, sys, os

HTML_PATH = os.path.join("static", "texas_alcohol_explorer.html")

OLD_CSS = ".cmp-grid td.best { color:var(--pos); font-weight:700; }"
NEW_CSS = """.cmp-grid td.best { color:var(--pos); font-weight:700; }

/* Compare pick list */
.cmp-pick-row { display:flex; align-items:center; gap:10px; padding:9px 10px; border-radius:var(--r-sm); cursor:pointer; border:1px solid transparent; margin-bottom:4px; transition:background 0.1s; -webkit-tap-highlight-color:transparent; }
.cmp-pick-row:hover { background:var(--s2); }
.cmp-pick-row input[type=checkbox] { width:18px; height:18px; accent-color:var(--accent); cursor:pointer; flex-shrink:0; }
.cmp-pick-info { flex:1; min-width:0; }
.cmp-pick-name { font-size:13px; font-weight:600; color:var(--text); }
.cmp-pick-addr { font-size:11px; color:var(--text3); margin-top:1px; }"""

NEW_COMPARE_HTML = """<!-- \u2500\u2500 Compare \u2500\u2500 -->
<div id="compare-page" class="page">
  <div class="hdr">
    <div class="hdr-eyebrow">Texas Open Data \u00b7 TABC</div>
    <h1 class="hdr-title"><strong>Venue</strong> <em>Comparison</em></h1>
  </div>
  <div class="wrap">
    <div class="fcard">
      <div class="section-label">Step 1 \u2014 Enter names to search (comma or newline separated)</div>
      <textarea id="cmp-name-input" rows="3" placeholder="Haywire, Perry\u2019s, Legacy Hall, Rollertown\u2026" style="width:100%;font-family:var(--sans);font-size:14px;padding:10px 12px;border-radius:var(--r-sm);border:1px solid var(--border2);background:var(--s2);color:var(--text);resize:vertical;outline:none;box-sizing:border-box;"></textarea>
      <div style="display:flex;gap:8px;margin-top:10px">
        <button class="btn-run" onclick="cmpSearchAll()">Search</button>
        <button class="btn-clear" onclick="clearComparison()">Clear</button>
      </div>
    </div>
    <div id="cmp-pick-section" style="display:none">
      <div class="fcard" style="padding-bottom:10px">
        <div class="section-label" style="margin-bottom:10px">Step 2 \u2014 Select up to 5 venues to compare</div>
        <div id="cmp-pick-list"></div>
      </div>
      <div style="display:flex;gap:8px;margin-bottom:14px">
        <button class="btn-run" id="cmp-run-btn" onclick="runComparison()" disabled>Compare selected</button>
        <span id="cmp-sel-count" style="font-family:var(--mono);font-size:11px;color:var(--text3);align-self:center;"></span>
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

NEW_JS = """var cmpVenuesPicked = [];
var cmpHistory = {};

function cmpKey(v) { return (v.location_name||'')+'|'+(v.location_zip||''); }

function cmpSearchAll() {
  var raw = document.getElementById('cmp-name-input').value;
  var names = raw.split(/[,\\n]/).map(function(s){return s.trim();}).filter(function(s){return s.length>0;});
  if (!names.length) return;
  var pickSection = document.getElementById('cmp-pick-section');
  var pickList = document.getElementById('cmp-pick-list');
  pickSection.style.display = 'none';
  pickList.innerHTML = '<div style="color:var(--text3);font-size:13px;padding:8px 0">Searching...</div>';
  document.getElementById('cmp-result').style.display = 'none';
  document.getElementById('cmp-status').style.display = 'none';
  cmpVenuesPicked = [];
  updatePickBtn();
  var promises = names.map(function(name) {
    var url = 'https://data.texas.gov/resource/naix-2893.json?$select=location_name,location_city,location_address,location_zip,taxpayer_name&$where='+
      encodeURIComponent("upper(location_name) like '%"+name.toUpperCase().replace(/'/g,"''")+ "%' AND total_receipts>=25000")+
      '&$limit=8&$order=location_name';
    return fetch(url).then(function(r){return r.json();}).then(function(data){return {name:name,results:data};});
  });
  pickSection.style.display = 'block';
  Promise.all(promises).then(function(groups) {
    pickList.innerHTML = '';
    var totalResults = 0;
    groups.forEach(function(group) {
      if (!group.results||!group.results.length) {
        var el=document.createElement('div');
        el.style.cssText='font-size:12px;color:var(--text3);padding:4px 0 10px;';
        el.textContent='No results for "'+group.name+'"';
        pickList.appendChild(el); return;
      }
      var hdr=document.createElement('div');
      hdr.style.cssText='font-family:var(--mono);font-size:9px;letter-spacing:0.1em;text-transform:uppercase;color:var(--text3);margin:10px 0 4px;';
      hdr.textContent='Results for "'+group.name+'"';
      pickList.appendChild(hdr);
      var seen={};
      group.results.forEach(function(r) {
        var k=(r.location_name||'')+'|'+(r.location_zip||'');
        if (seen[k]) return; seen[k]=true; totalResults++;
        var row=document.createElement('div');
        row.className='cmp-pick-row'; row.dataset.key=k;
        row.innerHTML='<input type="checkbox" class="cmp-pick-cb"><div class="cmp-pick-info"><div class="cmp-pick-name">'+(r.location_name||'')+'</div><div class="cmp-pick-addr">'+(r.location_address||'')+(r.location_city?', '+r.location_city:'')+'</div></div>';
        var cb=row.querySelector('input');
        cb.addEventListener('change',function(){
          if (cb.checked){if(cmpVenuesPicked.length>=5){cb.checked=false;return;}cmpVenuesPicked.push(r);}
          else{cmpVenuesPicked=cmpVenuesPicked.filter(function(v){return cmpKey(v)!==cmpKey(r);});}
          updatePickBtn();
        });
        row.addEventListener('click',function(e){if(e.target===cb)return;cb.click();});
        pickList.appendChild(row);
      });
    });
    if (!totalResults) pickList.innerHTML='<div style="color:var(--text3);font-size:13px;padding:8px 0">No venues found.</div>';
  }).catch(function(e){pickList.innerHTML='<div style="color:var(--neg);font-size:13px;">Error: '+e.message+'</div>';});
}

function updatePickBtn() {
  var btn=document.getElementById('cmp-run-btn');
  var count=document.getElementById('cmp-sel-count');
  if (!btn) return;
  btn.disabled=cmpVenuesPicked.length<2;
  count.textContent=cmpVenuesPicked.length?cmpVenuesPicked.length+' selected':'';
}

function clearComparison() {
  cmpVenuesPicked=[]; cmpHistory={};
  var ta=document.getElementById('cmp-name-input'); if(ta)ta.value='';
  var ps=document.getElementById('cmp-pick-section'); if(ps)ps.style.display='none';
  var pl=document.getElementById('cmp-pick-list'); if(pl)pl.innerHTML='';
  document.getElementById('cmp-result').style.display='none';
  document.getElementById('cmp-status').style.display='none';
  updatePickBtn();
}

function runComparison() {
  if (cmpVenuesPicked.length<2) return;
  var selected=cmpVenuesPicked;
  var status=document.getElementById('cmp-status');
  status.style.display='block';
  status.textContent='Fetching history for '+selected.length+' venue(s)...';
  document.getElementById('cmp-result').style.display='none';
  var promises=selected.map(function(v){
    var where="upper(location_name)='"+(v.location_name||'').toUpperCase().replace(/'/g,"''")+"' AND location_zip='"+(v.location_zip||'')+"'";
    var url='https://data.texas.gov/resource/naix-2893.json?$where='+encodeURIComponent(where)+'&$select=total_receipts,obligation_end_date_yyyymmdd&$limit=200&$order=obligation_end_date_yyyymmdd DESC';
    return fetch(url).then(function(r){return r.json();}).then(function(data){cmpHistory[cmpKey(v)]=data;});
  });
  Promise.all(promises).then(function(){
    status.style.display='none';
    renderComparison(selected);
  }).catch(function(e){status.textContent='Error: '+e.message;});
}

"""

def patch(content):
    changes = 0

    if OLD_CSS in content and 'cmp-pick-row' not in content:
        content = content.replace(OLD_CSS, NEW_CSS, 1)
        changes += 1; print("  [OK] CSS added")
    else:
        print("  [SKIP] CSS (already patched or anchor missing)")

    m = re.search(r'<!-- .*?Compare.*? -->\s*<div id="compare-page".*?(?=\n<!-- |\n</body>)', content, re.DOTALL)
    if m:
        content = content[:m.start()] + NEW_COMPARE_HTML + content[m.end():]
        changes += 1; print("  [OK] Compare HTML updated")
    else:
        print("  [SKIP] Compare HTML (not found)")

    m = re.search(r'var cmpVenues[a-zA-Z]*\s*=.*?(?=\nfunction renderComparison)', content, re.DOTALL)
    if m:
        content = content[:m.start()] + NEW_JS + content[m.end():]
        changes += 1; print("  [OK] JS replaced")
    else:
        print("  [SKIP] JS (anchor not found)")

    return content, changes

def main():
    if not os.path.exists(HTML_PATH):
        print(f"ERROR: {HTML_PATH} not found. Run from personal-dashboard root.")
        sys.exit(1)
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"Patching {HTML_PATH} ({len(content):,} chars)...")
    content, changes = patch(content)
    with open(HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Done. {changes} change(s) applied.")

if __name__ == "__main__":
    main()
