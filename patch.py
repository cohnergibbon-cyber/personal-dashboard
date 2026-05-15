path = r'C:\Users\CohnerGibbons\personal-dashboard\static\texas_alcohol_explorer.html'

with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

print('File size before:', len(c))
changes = 0

# ── 1. Sort CSS
if '.sort-pill' not in c:
    sort_css = """
.sort-row { display:flex; gap:8px; margin-bottom:10px; align-items:center; flex-wrap:wrap; }
.sort-lbl { font-size:11px; font-family:var(--mono); text-transform:uppercase; letter-spacing:0.08em; color:var(--text3); margin-right:4px; }
.sort-pill { height:30px; padding:0 14px; border:1.5px solid var(--border2); border-radius:20px; background:transparent; color:var(--text2); font-size:11px; font-family:var(--mono); font-weight:600; cursor:pointer; transition:all 0.15s; -webkit-tap-highlight-color:transparent; white-space:nowrap; }
.sort-pill.active { background:var(--accent); border-color:var(--accent); color:#F5F0E8; }
.sort-pill:hover:not(.active) { border-color:var(--accent); color:var(--accent); }
"""
    c = c.replace('</style>', sort_css + '</style>', 1)
    print('1. Sort CSS: added'); changes += 1
else:
    print('1. Sort CSS: already present')

# ── 2. Sort state + function
if 'function setNearbySort' not in c:
    sort_js = """
var _nearbySort = 'proximity';
function setNearbySort(mode) {
  _nearbySort = mode;
  document.querySelectorAll('.sort-pill').forEach(function(btn) {
    btn.classList.toggle('active', btn.getAttribute('data-sort') === mode);
  });
  if (_nearbyGeocoded.length) renderNearbyCards(_nearbyGeocoded, _currentRadius);
}
"""
    c = c.replace('function findNearby(){', sort_js + '\nfunction findNearby(){')
    print('2. setNearbySort: added'); changes += 1
else:
    print('2. setNearbySort: already present')

# ── 3. Sort row HTML above map-results
if 'sort-row-wrap' not in c:
    c = c.replace(
        '<div id="map-results"',
        '<div id="sort-row-wrap" style="display:none;" class="sort-row">'
        + '<span class="sort-lbl">Sort</span>'
        + '<button class="sort-pill active" data-sort="proximity" onclick="setNearbySort(\'proximity\')">Proximity</button>'
        + '<button class="sort-pill" data-sort="sales" onclick="setNearbySort(\'sales\')">Highest sales</button>'
        + '</div>\n    <div id="map-results"',
        1
    )
    print('3. Sort row HTML: added'); changes += 1
else:
    print('3. Sort row HTML: already present')

# ── 4. Sort logic inside renderNearbyCards
if "if(_nearbySort===" not in c:
    c = c.replace(
        "  var filtered=geocoded.filter(function(v){return v.dist<=maxMi;});\n  filtered.sort(function(a,b){return a.dist-b.dist;});\n  if(!filtered.length){",
        """  var filtered=geocoded.filter(function(v){return v.dist<=maxMi;});
  if(_nearbySort==='sales'){
    filtered.sort(function(a,b){return (parseFloat(b.record.total_receipts)||0)-(parseFloat(a.record.total_receipts)||0);});
  } else {
    filtered.sort(function(a,b){return a.dist-b.dist;});
  }
  var sortWrap=document.getElementById('sort-row-wrap');
  if(sortWrap) sortWrap.style.display=filtered.length?'flex':'none';
  if(!filtered.length){"""
    )
    print('4. Sort logic: added'); changes += 1
else:
    print('4. Sort logic: already present')

# ── 5. Next button - ensure results div shown on EVERY renderTable call
if "getElementById('results').style.display='block'" not in c:
    for old in [
        "function renderTable() {\n  var isMobile",
        "function renderTable() {\n  var start=(page-1)*PER",
    ]:
        if old in c:
            c = c.replace(old, "function renderTable() {\n  document.getElementById('results').style.display='block';\n" + old[len("function renderTable() {\n"):])
            print('5. Next button fix: added'); changes += 1
            break
    else:
        print('5. Next button fix: renderTable not found in expected form')
else:
    print('5. Next button fix: already present')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

print('File size after:', len(c))
print('Changes made:', changes)
print('Done.')
