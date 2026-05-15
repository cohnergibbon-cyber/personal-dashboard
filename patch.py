import re

path = r'C:\Users\CohnerGibbons\personal-dashboard\static\texas_alcohol_explorer.html'

with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

print('File size before:', len(c))
changes = 0

# ── 1. Fix setRadius - _nearbyGeocoded.length crash
# The issue is setRadius references _nearbyGeocoded before it's declared
# Find setRadius and fix the guard
old_setradius = """function setRadius(val) {
  _currentRadius = val;
  document.getElementById('radius-val').textContent = val + ' mi';
  document.querySelectorAll('.radius-pill').forEach(function(btn) {
    btn.classList.toggle('active', btn.getAttribute('data-sort') === mode);
  });
  if (_nearbyGeocoded.length) renderNearbyCards(_nearbyGeocoded, val);
}"""

# Also try the correct version
old_setradius2 = """function setRadius(val) {
  _currentRadius = val;
  document.getElementById('radius-val').textContent = val + ' mi';
  document.querySelectorAll('.radius-pill').forEach(function(btn, i) {
    btn.classList.toggle('active', i + 1 === val);
  });
  if (_nearbyGeocoded.length) renderNearbyCards(_nearbyGeocoded, val);
}"""

new_setradius = """function setRadius(val) {
  _currentRadius = val || 1;
  var display = document.getElementById('radius-val');
  if (display) display.textContent = _currentRadius + ' mi';
  document.querySelectorAll('.radius-pill').forEach(function(btn, i) {
    btn.classList.toggle('active', i + 1 === _currentRadius);
  });
  if (_nearbyGeocoded && _nearbyGeocoded.length) renderNearbyCards(_nearbyGeocoded, _currentRadius);
}"""

if old_setradius in c:
    c = c.replace(old_setradius, new_setradius); print('1. setRadius fixed (v1)'); changes += 1
elif old_setradius2 in c:
    c = c.replace(old_setradius2, new_setradius); print('1. setRadius fixed (v2)'); changes += 1
else:
    # Find and replace by regex
    m = re.search(r'function setRadius\(val\) \{[\s\S]+?\n\}', c)
    if m:
        c = c.replace(m.group(), new_setradius); print('1. setRadius fixed (regex)'); changes += 1
    else:
        print('1. setRadius: not found')

# ── 2. Ensure _nearbyGeocoded declared before everything
if 'var _nearbyGeocoded = []' not in c:
    # Find first var declaration in nearby section and prepend
    c = c.replace('var _currentRadius = 1;', 'var _nearbyGeocoded = [];\nvar _currentRadius = 1;', 1)
    print('2. _nearbyGeocoded declaration: added'); changes += 1
else:
    print('2. _nearbyGeocoded: already declared')

# ── 3. Fix addEventListener null error - wrap in null check
# Find the addEventListener calls at bottom of script
old_listeners = "document.getElementById('btn-run').addEventListener('click',runQuery);"
new_listeners = "var _btnRun=document.getElementById('btn-run'); if(_btnRun)_btnRun.addEventListener('click',runQuery);"
if old_listeners in c:
    c = c.replace(old_listeners, new_listeners); print('3. btn-run null guard: added'); changes += 1
else:
    print('3. btn-run null guard: not found')

# ── 4. Add debug logging to finalize for Ida Claire
if '[Nearby miss]' not in c:
    old_geo_push = "        if(geo) geocoded.push({record:v,lat:geo.lat,lng:geo.lng,dist:geo.dist});"
    new_geo_push = """        if(geo){
          geocoded.push({record:v,lat:geo.lat,lng:geo.lng,dist:geo.dist});
        } else {
          console.log('[Nearby miss]', addrKey(v.location_address||'',v.location_city||'',v.location_zip||''));
        }"""
    if old_geo_push in c:
        c = c.replace(old_geo_push, new_geo_push); print('4. Debug logging: added'); changes += 1
    else:
        print('4. Debug logging: geo push pattern not found')
else:
    print('4. Debug logging: already present')

# ── 5. Fix renderNearbyCards maxMi guard
c = c.replace(
    "status.textContent='No venues within '+maxMi+' mi",
    "status.textContent='No venues within '+(maxMi||_currentRadius||1)+' mi"
)
c = c.replace(
    "' venue'+(filtered.length!==1?'s':'')+' within '+maxMi+' mi",
    "' venue'+(filtered.length!==1?'s':'')+' within '+(maxMi||_currentRadius||1)+' mi"
)
print('5. maxMi guard: applied'); changes += 1

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

print('File size after:', len(c))
print('Changes made:', changes)
print('Done.')
