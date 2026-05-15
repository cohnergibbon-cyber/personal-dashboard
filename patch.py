import re

path = r'C:\Users\CohnerGibbons\personal-dashboard\static\texas_alcohol_explorer.html'

with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

print('File size before:', len(c))
changes = 0

# ── 1. Fix "undefined mi" - _currentRadius not set on first run
# Replace all uses of _currentRadius||1 with a safe getter
if 'function getRadius()' not in c:
    radius_getter = """
function getRadius() {
  var el = document.getElementById('radius-slider') || {};
  return parseInt(document.querySelector('.radius-pill.active')&&document.querySelector('.radius-pill.active').textContent)||_currentRadius||1;
}
"""
    c = c.replace('var _nearbySort =', radius_getter + '\nvar _nearbySort =')
    # Fix the undefined mi message
    c = c.replace(
        "status.textContent='No venues within '+maxMi+' mi \u2014 try a larger radius.'",
        "status.textContent='No venues within '+(maxMi||_currentRadius||1)+' mi \u2014 try a larger radius.'"
    )
    c = c.replace(
        "status.textContent=filtered.length+' venue'+(filtered.length!==1?'s':'')+' within '+maxMi+' mi",
        "status.textContent=filtered.length+' venue'+(filtered.length!==1?'s':'')+' within '+(maxMi||_currentRadius||1)+' mi"
    )
    print('1. Radius undefined fix: added'); changes += 1
else:
    print('1. getRadius: already present')

# ── 2. Fix _currentRadius initialization - set to 1 by default
old_radius_var = "var _currentRadius = 1;"
if old_radius_var not in c:
    # It might be declared differently
    c = c.replace('var _nearbyGeocoded = [];', 'var _nearbyGeocoded = [];\nvar _currentRadius = 1;', 1)
    print('2. _currentRadius init: added'); changes += 1
else:
    print('2. _currentRadius: already initialized')

# ── 3. Fix renderNearbyCards to always pass explicit radius
# Make sure radiusMi param is used not maxMi which could be undefined
old_render_call_1 = 'renderNearbyCards(geocoded,radiusMi);'
new_render_call_1 = 'renderNearbyCards(geocoded, radiusMi||_currentRadius||1);'
if old_render_call_1 in c:
    c = c.replace(old_render_call_1, new_render_call_1)
    print('3. renderNearbyCards call fixed'); changes += 1

old_render_call_2 = 'renderNearbyCards(geocoded,_currentRadius||1);'
new_render_call_2 = 'renderNearbyCards(geocoded, _currentRadius||1);'
c = c.replace(old_render_call_2, new_render_call_2)

# ── 4. Add "no suite" hint to address placeholder
c = c.replace(
    'placeholder="Enter address, city, or ZIP"',
    'placeholder="Enter address, city, or ZIP (no suite number)"'
)
# Also add a small hint below the input
if 'addr-hint' not in c:
    c = c.replace(
        '<button class="addr-btn" onclick="findNearbyByAddress()">Search</button>\n      </div>',
        '<button class="addr-btn" onclick="findNearbyByAddress()">Search</button>\n      </div>\n      <div class="addr-hint">Tip: omit suite numbers for best results \u2014 e.g. "5001 Belt Line Rd, Dallas"</div>'
    )
    hint_css = '\n.addr-hint { font-size: 11px; color: var(--text3); font-family: var(--mono); margin-top: 6px; }'
    c = c.replace('</style>', hint_css + '\n</style>', 1)
    print('4. Suite hint added'); changes += 1
else:
    print('4. Suite hint: already present')

# ── 5. Ida Claire - check what addrKey generates and add more alias variants
# TABC likely stores: "5001 BELT LINE RD" with city DALLAS zip 75254
# Geocoder may have stored as: "5001 BELTLINE RD" or "5001 BELT LINE ROAD" etc
# Add comprehensive aliases
old_aliases = """    var ADDRESS_ALIASES = {
      '5001 BELT LINE RD|DALLAS|75254': '5001 BELTLINE RD|DALLAS|75254',
      '5001 BELTLINE RD|DALLAS|75254': '5001 BELT LINE RD|DALLAS|75254',
    };"""

new_aliases = """    var ADDRESS_ALIASES = {
      '5001 BELT LINE RD|DALLAS|75254': '5001 BELTLINE RD|DALLAS|75254',
      '5001 BELTLINE RD|DALLAS|75254': '5001 BELT LINE RD|DALLAS|75254',
      '5001 BELT LINE RD|ADDISON|75001': '5001 BELTLINE RD|ADDISON|75001',
      '5001 BELTLINE RD|ADDISON|75001': '5001 BELT LINE RD|ADDISON|75001',
    };"""

if old_aliases in c:
    c = c.replace(old_aliases, new_aliases)
    print('5. Ida Claire aliases expanded'); changes += 1
elif 'ADDRESS_ALIASES' not in c:
    # Inject before Object.keys(geoLookup)
    c = c.replace(
        '    Object.keys(geoLookup).forEach(function(key){',
        """    var ADDRESS_ALIASES = {
      '5001 BELT LINE RD|DALLAS|75254': '5001 BELTLINE RD|DALLAS|75254',
      '5001 BELTLINE RD|DALLAS|75254': '5001 BELT LINE RD|DALLAS|75254',
      '5001 BELT LINE RD|ADDISON|75001': '5001 BELTLINE RD|ADDISON|75001',
    };
    Object.keys(geoLookup).forEach(function(key){""",
        1
    )
    print('5. ADDRESS_ALIASES injected fresh'); changes += 1
else:
    print('5. ADDRESS_ALIASES already present - check variants')

# ── 6. Log nearby geo matches to console so we can debug Ida Claire
# Add a debug log in finalize
old_finalize_end = "        if(geo) geocoded.push({record:v,lat:geo.lat,lng:geo.lng,dist:geo.dist});"
new_finalize_end = """        if(geo){
          geocoded.push({record:v,lat:geo.lat,lng:geo.lng,dist:geo.dist});
        } else {
          console.log('[Nearby miss]', addrKey(v.location_address||'',v.location_city||'',v.location_zip||''));
        }"""
if old_finalize_end in c and '[Nearby miss]' not in c:
    c = c.replace(old_finalize_end, new_finalize_end)
    print('6. Debug logging added for misses'); changes += 1
else:
    print('6. Debug logging: already present or pattern not found')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

print('File size after:', len(c))
print('Changes made:', changes)
print('Done.')
