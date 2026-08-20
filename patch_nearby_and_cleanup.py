#!/usr/bin/env python3
"""
Bundle of fixes:

1. Crash fix: fmtPct()/varClass() treated `null` as finite (JS quirk:
   isFinite(null) === true) and called .toFixed() on it, throwing
   "null is not an object (evaluating 'n.toFixed')" whenever a location's
   prior-year total was exactly $0 (var % is undefined in that case). The
   mobile card renderer also didn't guard varPct independently of varAmt.

2. Correctness fix: Nearby tab fetched its geocoded-address lookup from
   the stale root-level tx_venues_geo.json instead of the actively
   maintained static/tx_venues_geo.json that geocode_tabc_update.py
   writes to. Every geocoding update has had zero effect on production
   until now.

3. Correctness fix: Nearby (both "Use my location" and address search)
   restricted its TABC query to the single city returned by reverse
   geocoding, so venues just across a city line were missed even though
   they're within the selected radius. Now derives the full set of
   nearby cities from the geo lookup file (which is already loaded
   locally) before querying.

4. Perf: the ~2.2MB geo lookup file is now cached in memory after first
   load instead of being re-fetched on every Nearby search.

5. Cleanup: the 118-city "top 50 metro" array was hardcoded twice
   (verbatim) for the City filter's "Other" logic. Both copies are now
   derived from the existing CITY_GROUPS object instead of duplicated.

6. Cleanup: removed the unused buildWhereFilters()/buildUrl() functions
   (dead code — runQuery() has its own filter builders) and the inert
   getElementById('btn-clear') listener (no element has that id; the
   Clear buttons already work via inline onclick).

Run from the repo root: python patch_nearby_and_cleanup.py
"""
import sys

PATH = "static/texas_alcohol_explorer.html"

with open(PATH, "r", encoding="utf-8") as f:
    html = f.read()

changed = 0


def apply(old, new, label, count=1):
    global html, changed
    n = html.count(old)
    if n != count:
        sys.exit(f"ABORT: expected {count} occurrence(s) of [{label}], found {n}. No changes written.")
    html = html.replace(old, new, count) if count != -1 else html.replace(old, new)
    changed += 1


# ── 1) fmtPct / varClass null-safety ────────────────────────────────────
apply(
    '''function fmtPct(n) { if (!isFinite(n)) return '—'; return (n>=0?'+':'')+n.toFixed(1)+'%'; }\nfunction varClass(n) { if (!isFinite(n)||n===0) return ''; return n>0?'pos':'neg'; }''',
    '''function fmtPct(n) { if (n===null||n===undefined||!isFinite(n)) return '—'; return (n>=0?'+':'')+n.toFixed(1)+'%'; }\nfunction varClass(n) { if (n===null||n===undefined||!isFinite(n)||n===0) return ''; return n>0?'pos':'neg'; }''',
    "fmtPct/varClass null guard",
)

# ── 2) Mobile card renderer: guard varPct independently of varAmt ──────
apply(
    '''      if(varAmt!==null){var cls=varClass(varAmt);varHtml='<div class="venue-stat '+cls+'">'+(varAmt>=0?'+':'')+fmtMoney(varAmt,false)+' ('+fmtPct(varPct)+')</div>';}''',
    '''      if(varAmt!==null){var cls=varClass(varAmt);var pctStr=(varPct!==null?' ('+fmtPct(varPct)+')':'');varHtml='<div class="venue-stat '+cls+'">'+(varAmt>=0?'+':'')+fmtMoney(varAmt,false)+pctStr+'</div>';}''',
    "mobile card varPct guard",
)

# ── 3) Add a shared, cached geo-lookup loader ───────────────────────────
apply(
    '''var _nearbyGeocoded = [];\nvar _currentRadius = 1;''',
    '''var _nearbyGeocoded = [];\nvar _currentRadius = 1;\nvar _geoLookupCache = null;\nfunction loadGeoLookup() {\n  if (_geoLookupCache) return Promise.resolve(_geoLookupCache);\n  return fetch('/static/tx_venues_geo.json')\n    .then(function(r){\n      if (!r.ok) throw new Error('tx_venues_geo.json not found — run geocode_tabc.py first');\n      return r.json();\n    })\n    .then(function(data){ _geoLookupCache = data; return data; });\n}\nfunction nearbyCityList(geoLookup, userLat, userLng, fallbackCity) {\n  var found = {};\n  Object.keys(geoLookup).forEach(function(k){\n    var coord = geoLookup[k];\n    if (!coord) return;\n    if (haverDist(userLat, userLng, coord[0], coord[1]) <= 5) {\n      var parts = k.split('|');\n      if (parts[1]) found[parts[1]] = true;\n    }\n  });\n  var cities = Object.keys(found);\n  if (!cities.length) cities = [fallbackCity];\n  if (cities.indexOf('FORT WORTH') > -1 && cities.indexOf('FT WORTH') === -1) cities.push('FT WORTH');\n  return cities;\n}\nfunction cityWhereClause(cities) {\n  var esc = cities.map(function(c){ return c.replace(/'/g,"''"); });\n  return esc.length === 1\n    ? "upper(location_city)='" + esc[0] + "'"\n    : "upper(location_city) in ('" + esc.join("','") + "')";\n}''',
    "geo lookup cache + nearbyCityList/cityWhereClause helpers",
)

# ── 4) findNearbyByAddress: use cached loader + multi-city where clause ─
apply(
    '''    fetch('/tx_venues_geo.json')\n    .then(function(r){\n      if (!r.ok) throw new Error('tx_venues_geo.json not found — run geocode_tabc.py first');\n      return r.json();\n    })\n    .then(function(geoLookup){\n      status.textContent = 'Finding nearest city…';''',
    '''    loadGeoLookup()\n    .then(function(geoLookup){\n      status.textContent = 'Finding nearest city…';''',
    "findNearbyByAddress: cached loader",
)
apply(
    '''        status.textContent = 'Fetching venues in '+rawCity+'…';\n        var _d=new Date(); _d.setMonth(_d.getMonth()-2);\n        var month=String(_d.getMonth()+1).padStart(2,'0');\n        var year=String(_d.getFullYear());\n        var nm=parseInt(month)===12?1:parseInt(month)+1;\n        var ny=parseInt(month)===12?parseInt(year)+1:parseInt(year);\n        var pad=nm<10?'0'+nm:String(nm);\n        var where=[\n          "upper(location_city)='"+city.replace(/'/g,"''")+"'",\n          "obligation_end_date_yyyymmdd>='"+year+'-'+month+"-01T00:00:00.000'",\n          "obligation_end_date_yyyymmdd<'"+ny+'-'+pad+"-01T00:00:00.000'"\n        ];\n        var url='https://data.texas.gov/resource/naix-2893.json?$limit=500&$select=location_name,location_address,location_city,location_zip,total_receipts,obligation_end_date_yyyymmdd,taxpayer_name&$where='+encodeURIComponent(where.join(' AND '));\n        return fetch(url).then(function(r){return r.json();}).then(function(venues){\n          if (!venues||!venues.length) throw new Error('No venues found in '+rawCity);''',
    '''        status.textContent = 'Fetching nearby venues…';\n        var _d=new Date(); _d.setMonth(_d.getMonth()-2);\n        var month=String(_d.getMonth()+1).padStart(2,'0');\n        var year=String(_d.getFullYear());\n        var nm=parseInt(month)===12?1:parseInt(month)+1;\n        var ny=parseInt(month)===12?parseInt(year)+1:parseInt(year);\n        var pad=nm<10?'0'+nm:String(nm);\n        var nearCities = nearbyCityList(geoLookup, userLat, userLng, city);\n        var where=[\n          cityWhereClause(nearCities),\n          "obligation_end_date_yyyymmdd>='"+year+'-'+month+"-01T00:00:00.000'",\n          "obligation_end_date_yyyymmdd<'"+ny+'-'+pad+"-01T00:00:00.000'"\n        ];\n        var url='https://data.texas.gov/resource/naix-2893.json?$limit=3000&$select=location_name,location_address,location_city,location_zip,total_receipts,obligation_end_date_yyyymmdd,taxpayer_name&$where='+encodeURIComponent(where.join(' AND '));\n        return fetch(url).then(function(r){return r.json();}).then(function(venues){\n          if (!venues||!venues.length) throw new Error('No venues found near '+rawCity);''',
    "findNearbyByAddress: multi-city where clause",
)

# ── 5) findNearby (use-my-location): same two changes ───────────────────
apply(
    '''    fetch('/tx_venues_geo.json')\n    .then(function(r){\n      if(!r.ok) throw new Error('tx_venues_geo.json not found — run geocode_tabc.py first');\n      return r.json();\n    })\n    .then(function(geoLookup){\n      status.textContent='Finding your city…';''',
    '''    loadGeoLookup()\n    .then(function(geoLookup){\n      status.textContent='Finding your city…';''',
    "findNearby: cached loader",
)
apply(
    '''        status.textContent='Fetching venues in '+rawCity+'…';\n        var _d=new Date(); _d.setMonth(_d.getMonth()-2);\n        var month=String(_d.getMonth()+1).padStart(2,'0');\n        var year=String(_d.getFullYear());\n        var nm=parseInt(month)===12?1:parseInt(month)+1;\n        var ny=parseInt(month)===12?parseInt(year)+1:parseInt(year);\n        var pad=nm<10?'0'+nm:String(nm);\n        var where=[\n          "upper(location_city)='"+city.replace(/'/g,"''")+"'",\n          "obligation_end_date_yyyymmdd>='"+year+'-'+month+"-01T00:00:00.000'",\n          "obligation_end_date_yyyymmdd<'"+ny+'-'+pad+"-01T00:00:00.000'"\n        ];\n        var url='https://data.texas.gov/resource/naix-2893.json?$limit=500&$select=location_name,location_address,location_city,location_zip,total_receipts,obligation_end_date_yyyymmdd,taxpayer_name&$where='+encodeURIComponent(where.join(' AND '));\n        return fetch(url).then(function(r){return r.json();}).then(function(venues){\n          if(!venues||!venues.length) throw new Error('No venues found in '+rawCity);''',
    '''        status.textContent='Fetching nearby venues…';\n        var _d=new Date(); _d.setMonth(_d.getMonth()-2);\n        var month=String(_d.getMonth()+1).padStart(2,'0');\n        var year=String(_d.getFullYear());\n        var nm=parseInt(month)===12?1:parseInt(month)+1;\n        var ny=parseInt(month)===12?parseInt(year)+1:parseInt(year);\n        var pad=nm<10?'0'+nm:String(nm);\n        var nearCities = nearbyCityList(geoLookup, userLat, userLng, city);\n        var where=[\n          cityWhereClause(nearCities),\n          "obligation_end_date_yyyymmdd>='"+year+'-'+month+"-01T00:00:00.000'",\n          "obligation_end_date_yyyymmdd<'"+ny+'-'+pad+"-01T00:00:00.000'"\n        ];\n        var url='https://data.texas.gov/resource/naix-2893.json?$limit=3000&$select=location_name,location_address,location_city,location_zip,total_receipts,obligation_end_date_yyyymmdd,taxpayer_name&$where='+encodeURIComponent(where.join(' AND '));\n        return fetch(url).then(function(r){return r.json();}).then(function(venues){\n          if(!venues||!venues.length) throw new Error('No venues found near '+rawCity);''',
    "findNearby: multi-city where clause",
)

# ── 6) Consolidate the duplicated 118-city top50 arrays ─────────────────
old_top50a = '''      var top50 = ['DALLAS','FORT WORTH','FT WORTH','ARLINGTON','PLANO','IRVING','GARLAND','FRISCO','MCKINNEY','GRAND PRAIRIE','MESQUITE','DENTON','CARROLLTON','RICHARDSON','LEWISVILLE','ALLEN','GRAPEVINE','SOUTHLAKE','FLOWER MOUND','CEDAR HILL','MANSFIELD','EULESS','BEDFORD','HURST','KELLER','ROCKWALL','THE COLONY','ADDISON','HIGHLAND PARK','BURLESON','COPPELL','COLLEYVILLE','WAXAHACHIE','DUNCANVILLE','DESOTO','ROWLETT','WYLIE','FORNEY','HOUSTON','SUGAR LAND','PEARLAND','LEAGUE CITY','PASADENA','CONROE','THE WOODLANDS','BAYTOWN','FRIENDSWOOD','STAFFORD','MISSOURI CITY','KATY','SPRING','HUMBLE','CLEAR LAKE','CYPRESS','WEBSTER','KEMAH','SHENANDOAH','TOMBALL','MONTGOMERY','AUSTIN','ROUND ROCK','CEDAR PARK','PFLUGERVILLE','SAN MARCOS','KYLE','BUDA','GEORGETOWN','LAKEWAY','BEE CAVE','SAN ANTONIO','NEW BRAUNFELS','SCHERTZ','LIVE OAK','UNIVERSAL CITY','BOERNE','SEGUIN','MCALLEN','BROWNSVILLE','LAREDO','EDINBURG','MISSION','HARLINGEN','PHARR','WESLACO','CORPUS CHRISTI','BEAUMONT','PORT ARTHUR','GALVESTON','VICTORIA','PORT LAVACA','EL PASO','MIDLAND','ODESSA','ABILENE','SAN ANGELO','LUBBOCK','AMARILLO','WICHITA FALLS','WACO','COLLEGE STATION','TYLER','LONGVIEW','KILLEEN','TEMPLE','LUFKIN','NACOGDOCHES','TEXARKANA','SHERMAN','MARSHALL','KERRVILLE','FREDERICKSBURG','MARBLE FALLS','BASTROP','WIMBERLEY','GRANBURY','STEPHENVILLE','BRYAN','SOUTH PADRE ISLAND'];\n      w.push("not upper(location_city) in ('"+top50.join("','")+"')");'''
new_top50a = '''      var top50 = TOP_METRO_CITIES;\n      w.push("not upper(location_city) in ('"+top50.join("','")+"')");'''
apply(old_top50a, new_top50a, "top50 array (baseFilters, OTHER-only branch)")

old_top50b = '''      var top50b = ['DALLAS','FORT WORTH','FT WORTH','ARLINGTON','PLANO','IRVING','GARLAND','FRISCO','MCKINNEY','GRAND PRAIRIE','MESQUITE','DENTON','CARROLLTON','RICHARDSON','LEWISVILLE','ALLEN','GRAPEVINE','SOUTHLAKE','FLOWER MOUND','CEDAR HILL','MANSFIELD','EULESS','BEDFORD','HURST','KELLER','ROCKWALL','THE COLONY','ADDISON','HIGHLAND PARK','BURLESON','COPPELL','COLLEYVILLE','WAXAHACHIE','DUNCANVILLE','DESOTO','ROWLETT','WYLIE','FORNEY','HOUSTON','SUGAR LAND','PEARLAND','LEAGUE CITY','PASADENA','CONROE','THE WOODLANDS','BAYTOWN','FRIENDSWOOD','STAFFORD','MISSOURI CITY','KATY','SPRING','HUMBLE','CLEAR LAKE','CYPRESS','WEBSTER','KEMAH','SHENANDOAH','TOMBALL','MONTGOMERY','AUSTIN','ROUND ROCK','CEDAR PARK','PFLUGERVILLE','SAN MARCOS','KYLE','BUDA','GEORGETOWN','LAKEWAY','BEE CAVE','SAN ANTONIO','NEW BRAUNFELS','SCHERTZ','LIVE OAK','UNIVERSAL CITY','BOERNE','SEGUIN','MCALLEN','BROWNSVILLE','LAREDO','EDINBURG','MISSION','HARLINGEN','PHARR','WESLACO','CORPUS CHRISTI','BEAUMONT','PORT ARTHUR','GALVESTON','VICTORIA','PORT LAVACA','EL PASO','MIDLAND','ODESSA','ABILENE','SAN ANGELO','LUBBOCK','AMARILLO','WICHITA FALLS','WACO','COLLEGE STATION','TYLER','LONGVIEW','KILLEEN','TEMPLE','LUFKIN','NACOGDOCHES','TEXARKANA','SHERMAN','MARSHALL','KERRVILLE','FREDERICKSBURG','MARBLE FALLS','BASTROP','WIMBERLEY','GRANBURY','STEPHENVILLE','BRYAN','SOUTH PADRE ISLAND'];'''
new_top50b = '''      var top50b = TOP_METRO_CITIES;'''
apply(old_top50b, new_top50b, "top50b array (baseFilters, named+OTHER branch)")

# Define TOP_METRO_CITIES once, derived from the existing CITY_GROUPS map,
# right after CITY_GROUPS is declared (BRYAN/FORNEY aren't in CITY_GROUPS'
# dropdown but were in the old hardcoded lists, so keep them explicitly).
apply(
    '''var CITY_GROUPS = {''',
    '''var TOP_METRO_CITIES_EXTRA = ['FT WORTH','FORNEY','BRYAN'];\nvar CITY_GROUPS = {''',
    "TOP_METRO_CITIES_EXTRA declaration",
)
# Insert the derived constant right after the CITY_GROUPS object literal's
# closing brace+semicolon (that whole object is on one line in the file).
marker = '"hill_country": ["KERRVILLE", "FREDERICKSBURG", "MARBLE FALLS", "BASTROP", "WIMBERLEY", "GRANBURY", "STEPHENVILLE"]};'
if html.count(marker) != 1:
    sys.exit("ABORT: CITY_GROUPS closing marker not found/not unique. No changes written.")
html = html.replace(
    marker,
    marker + '\nvar TOP_METRO_CITIES = Object.keys(CITY_GROUPS).reduce(function(acc,k){return acc.concat(CITY_GROUPS[k]);},[]).concat(TOP_METRO_CITIES_EXTRA);',
    1,
)
changed += 1

# ── 7) Remove dead code ─────────────────────────────────────────────────
old_dead_fns = '''function buildWhereFilters(yearOverride, monthOverride) {\n  var taxpayer = document.getElementById('f-taxpayer').value.trim();\n  var cityEl = document.getElementById('f-city');\n  var selectedCities = Array.from(cityEl.selectedOptions).map(function(o){return o.value;}).filter(Boolean);\n  var zip = document.getElementById('f-zip').value.trim();\n  var month = monthOverride !== undefined ? monthOverride : document.getElementById('f-month').value;\n  var year = yearOverride || document.getElementById('f-year').value;\n\n  var where = [];\n  if (taxpayer) { var tUp2 = taxpayer.toUpperCase().replace(/'/g,"''"); where.push("(upper(taxpayer_name) like '%" + tUp2 + "%' OR upper(location_name) like '%" + tUp2 + "%')"); }\n  if (city) where.push("upper(location_city)='" + city.toUpperCase().replace(/'/g,"''") + "'");\n  if (zip) where.push("location_zip='" + zip.replace(/'/g,"''") + "'");\n  if (month === 'YTD' && year) {\n    // YTD: Jan 1 through end of year (API will only have data through current month)\n    where.push("obligation_end_date_yyyymmdd>='" + year + "-01-01T00:00:00.000'");\n    where.push("obligation_end_date_yyyymmdd<'" + (parseInt(year)+1) + "-01-01T00:00:00.000'");\n  } else if (month && month !== 'YTD' && year) {\n    var nm = parseInt(month)===12?1:parseInt(month)+1;\n    var ny = parseInt(month)===12?parseInt(year)+1:parseInt(year);\n    var pad = nm<10?'0'+nm:String(nm);\n    where.push("obligation_end_date_yyyymmdd>='" + year + "-" + month + "-01T00:00:00.000'");\n    where.push("obligation_end_date_yyyymmdd<'" + ny + "-" + pad + "-01T00:00:00.000'");\n  } else if (year && !month) {\n    where.push("obligation_end_date_yyyymmdd>='" + year + "-01-01T00:00:00.000'");\n    where.push("obligation_end_date_yyyymmdd<'" + (parseInt(year)+1) + "-01-01T00:00:00.000'");\n  }\n  return where;\n}\n\nfunction buildUrl(yearOverride, monthOverride) {\n  var where = buildWhereFilters(yearOverride, monthOverride);\n  var url = API + '?$limit=5000&$order=total_receipts+DESC&$select=location_name,location_city,location_address,location_zip,total_receipts,obligation_end_date_yyyymmdd,taxpayer_name';\n  if (where.length) url += '&$where=' + encodeURIComponent(where.join(' AND '));\n  return url;\n}\n\nfunction runQuery() {'''
new_dead_fns = '''function runQuery() {'''
apply(old_dead_fns, new_dead_fns, "unused buildWhereFilters/buildUrl removal")

apply(
    '''var _btnClear=document.getElementById('btn-clear');if(_btnClear)_btnClear.addEventListener('click',clearAll);\n''',
    '',
    "dead btn-clear listener removal",
)

with open(PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Patched {changed} location(s) in {PATH}")
