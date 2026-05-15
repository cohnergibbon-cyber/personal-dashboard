import re

path = r'C:\Users\CohnerGibbons\personal-dashboard\static\texas_alcohol_explorer.html'

with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

print('File size before:', len(c))
changes = 0

# ── 1. Move footnote to be inline with "Tap any row for history" hint
# Remove existing results-note if it was added in wrong place
c = c.replace('\n      <div class="results-note">Showing venues with \u2265$25,000 monthly alcohol sales</div>', '')
c = c.replace('\n<div class="results-note">Showing venues with \u2265$25,000 monthly alcohol sales</div>', '')

# Update the tbl-hint span to include the footnote inline
old_hint = '<span class="tbl-hint">Tap any row for history</span>'
new_hint = '<span class="tbl-hint">Tap any venue for history &nbsp;&middot;&nbsp; Showing \u2265$25k monthly sales only</span>'
if old_hint in c:
    c = c.replace(old_hint, new_hint)
    print('1. Footnote moved inline with hint'); changes += 1
else:
    old_hint2 = '<span class="tbl-hint">Tap any venue for history</span>'
    if old_hint2 in c:
        c = c.replace(old_hint2, new_hint)
        print('1. Footnote moved inline with hint (v2)'); changes += 1
    else:
        print('1. tbl-hint not found')

# ── 2. Add $25k filter to nearby query in runNearbySearch fetchBatch
# The nearby query needs total_receipts>=25000 added to dateWhere
old_date_where = """    var dateWhere=[
      "obligation_end_date_yyyymmdd>='"+year+'-'+month+"-01T00:00:00.000'",
      "obligation_end_date_yyyymmdd<'"+ny+'-'+pad+"-01T00:00:00.000'"
    ];"""
new_date_where = """    var dateWhere=[
      "obligation_end_date_yyyymmdd>='"+year+'-'+month+"-01T00:00:00.000'",
      "obligation_end_date_yyyymmdd<'"+ny+'-'+pad+"-01T00:00:00.000'",
      "total_receipts>=25000"
    ];"""
if old_date_where in c:
    c = c.replace(old_date_where, new_date_where)
    print('2. $25k filter added to nearby'); changes += 1
else:
    print('2. dateWhere not found - checking for alternate')
    # Try finding it another way
    idx = c.find('runNearbySearch')
    snippet = c[idx:idx+2000] if idx>=0 else ''
    if 'dateWhere' in snippet:
        print('   dateWhere exists but format differs')
    else:
        print('   dateWhere not in runNearbySearch')

# ── 3. Fix Ida Claire - add to fixVenueName AND add special address alias
# First fix the name typo handler
old_fixes = """  var fixes = {
    'IDA CLLAIRE': 'IDA CLAIRE',
    'IDA CLLAIRE BAR': 'IDA CLAIRE BAR',
  };"""
if old_fixes in c:
    print('3. fixVenueName already has Ida Claire fix')
elif 'function fixVenueName' in c:
    # Function exists but without the fix - update it
    c = c.replace(
        "var fixes = {",
        "var fixes = {\n    'IDA CLLAIRE': 'IDA CLAIRE',"
    )
    print('3. Added Ida Claire to fixVenueName'); changes += 1
else:
    # Add fixVenueName entirely
    fix_fn = """
function fixVenueName(name) {
  if (!name) return name;
  var fixes = {'IDA CLLAIRE': 'IDA CLAIRE'};
  var up = name.toUpperCase();
  for (var w in fixes) { if (up.indexOf(w) >= 0) return name.toUpperCase().replace(w, fixes[w]); }
  return name;
}
"""
    c = c.replace('function renderNearbyCards(', fix_fn + '\nfunction renderNearbyCards(')
    print('3. fixVenueName added'); changes += 1

# ── 4. Add address alias for Ida Claire in runNearbySearch
# After building nearbyCoords, add known address aliases
old_nearby_scan = "    Object.keys(geoLookup).forEach(function(key){"
new_nearby_scan = """    // Known address aliases (TABC address -> geo lookup key)
    var ADDRESS_ALIASES = {
      '5001 BELT LINE RD|DALLAS|75254': '5001 BELTLINE RD|DALLAS|75254',
      '5001 BELTLINE RD|DALLAS|75254': '5001 BELT LINE RD|DALLAS|75254',
    };

    Object.keys(geoLookup).forEach(function(key){"""

if old_nearby_scan in c and 'ADDRESS_ALIASES' not in c:
    c = c.replace(old_nearby_scan, new_nearby_scan)
    print('4. Address aliases added'); changes += 1
else:
    print('4. Address aliases: already present or scan not found')

# ── 5. Apply aliases in finalize() geo matching
old_geo_match = """        var key=addrKey(v.location_address||'',v.location_city||'',v.location_zip||'');
        var geo=nearbyCoords[key];
        if(!geo){
          // Fuzzy fallback: match on base address + zip only
          var base=addrKeyBase(v.location_address||'')+'|'+((v.location_zip||'').slice(0,5));
          geo=baseIndex[base];
        }
        if(geo) geocoded.push({record:v,lat:geo.lat,lng:geo.lng,dist:geo.dist});"""
new_geo_match = """        var key=addrKey(v.location_address||'',v.location_city||'',v.location_zip||'');
        var geo=nearbyCoords[key];
        if(!geo){
          // Try address alias
          var aliasKey=ADDRESS_ALIASES[key];
          if(aliasKey) geo=nearbyCoords[aliasKey];
        }
        if(!geo){
          // Fuzzy fallback: match on base address + zip only
          var base=addrKeyBase(v.location_address||'')+'|'+((v.location_zip||'').slice(0,5));
          geo=baseIndex[base];
        }
        if(geo) geocoded.push({record:v,lat:geo.lat,lng:geo.lng,dist:geo.dist});"""
if old_geo_match in c:
    c = c.replace(old_geo_match, new_geo_match)
    print('5. Alias lookup in finalize: added'); changes += 1
else:
    print('5. finalize geo match: pattern not found')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

print('File size after:', len(c))
print('Changes made:', changes)
print('Done.')
