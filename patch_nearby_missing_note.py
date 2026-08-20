#!/usr/bin/env python3
"""
Follow-up to patch_nearby_and_cleanup.py:

1. Surfaces ungeocoded/dropped venues in the Nearby UI instead of only
   logging them to the browser console — e.g. "171 venues within 2 mi
   · Jun 2026 · 3 not shown (not yet mapped)". Makes a stale/incomplete
   geo file visible immediately instead of looking like a mystery bug.

2. Fixes a residual bug from the multi-city radius change: the prior-year
   comparison fetch in both Nearby entry points still filtered by the
   single reverse-geocoded city, so venues in a neighboring city (now
   correctly included in the current-year results) never got their
   prior-year total/variance. Both PY queries now use the same
   multi-city where clause as the current-year query.

Run from the repo root: python patch_nearby_missing_note.py
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
    html = html.replace(old, new, count)
    changed += 1


# ── 1) Track missing count in a module-level var ────────────────────────
apply(
    '''var _nearbyGeocoded = [];\nvar _currentRadius = 1;''',
    '''var _nearbyGeocoded = [];\nvar _nearbyMissingCount = 0;\nvar _currentRadius = 1;''',
    "add _nearbyMissingCount",
)

# ── 2) Surface it in renderNearbyCards' status line ─────────────────────
apply(
    '''  status.textContent=filtered.length+' venue'+(filtered.length!==1?'s':'')+' within '+maxMi+' mi \xb7 '+periodLabel;''',
    '''  var missingNote = _nearbyMissingCount>0 ? ' \xb7 '+_nearbyMissingCount+' not shown (not yet mapped)' : '';\n  status.textContent=filtered.length+' venue'+(filtered.length!==1?'s':'')+' within '+maxMi+' mi \xb7 '+periodLabel+missingNote;''',
    "renderNearbyCards status line",
)

# ── 3) findNearbyByAddress: record the count + fix PY city scope ───────
apply(
    '''          if (missing) console.log('[Nearby] '+missing+' venues missing from geo lookup');''',
    '''          if (missing) console.log('[Nearby] '+missing+' venues missing from geo lookup');\n          _nearbyMissingCount = missing;''',
    "findNearbyByAddress: record missing count",
)
apply(
    '''          var pyWhere=[\n            "upper(location_city)='"+city.replace(/'/g,"''")+"'",\n            "obligation_end_date_yyyymmdd>='"+pyY+'-'+pyM+"-01T00:00:00.000'",\n            "obligation_end_date_yyyymmdd<'"+pyNy+'-'+pyPad+"-01T00:00:00.000'"\n          ];\n          var pyUrl='https://data.texas.gov/resource/naix-2893.json?$limit=500&$select=location_name,location_address,location_zip,total_receipts&$where='+encodeURIComponent(pyWhere.join(' AND '));\n          return fetch(pyUrl).then(function(r){return r.json();}).then(function(pyVenues){\n            var pyMap={};\n            (pyVenues||[]).forEach(function(p){\n              var k=(p.location_name||'')+'|'+(p.location_zip||'');\n              pyMap[k]=parseFloat(p.total_receipts)||0;\n            });\n            geocoded.forEach(function(v){\n              var k=(v.record.location_name||'')+'|'+(v.record.location_zip||'');\n              if (pyMap[k]!==undefined) v.record._py_total=pyMap[k];\n            });\n            _nearbyGeocoded=geocoded;\n            renderNearbyCards(geocoded, radiusMi);\n          });''',
    '''          var pyWhere=[\n            cityWhereClause(nearCities),\n            "obligation_end_date_yyyymmdd>='"+pyY+'-'+pyM+"-01T00:00:00.000'",\n            "obligation_end_date_yyyymmdd<'"+pyNy+'-'+pyPad+"-01T00:00:00.000'"\n          ];\n          var pyUrl='https://data.texas.gov/resource/naix-2893.json?$limit=3000&$select=location_name,location_address,location_zip,total_receipts&$where='+encodeURIComponent(pyWhere.join(' AND '));\n          return fetch(pyUrl).then(function(r){return r.json();}).then(function(pyVenues){\n            var pyMap={};\n            (pyVenues||[]).forEach(function(p){\n              var k=(p.location_name||'')+'|'+(p.location_zip||'');\n              pyMap[k]=parseFloat(p.total_receipts)||0;\n            });\n            geocoded.forEach(function(v){\n              var k=(v.record.location_name||'')+'|'+(v.record.location_zip||'');\n              if (pyMap[k]!==undefined) v.record._py_total=pyMap[k];\n            });\n            _nearbyGeocoded=geocoded;\n            renderNearbyCards(geocoded, radiusMi);\n          });''',
    "findNearbyByAddress: PY multi-city where",
)

# ── 4) findNearby (use-my-location): same two changes ───────────────────
apply(
    '''          if(missing) console.log('[Nearby] '+missing+' venues missing from geo lookup');''',
    '''          if(missing) console.log('[Nearby] '+missing+' venues missing from geo lookup');\n          _nearbyMissingCount = missing;''',
    "findNearby: record missing count",
)
apply(
    '''          var pyWhere=[\n            "upper(location_city)='"+city.replace(/'/g,"''")+"'",\n            "obligation_end_date_yyyymmdd>='"+pyY+'-'+pyM+"-01T00:00:00.000'",\n            "obligation_end_date_yyyymmdd<'"+pyNy+'-'+pyPad+"-01T00:00:00.000'"\n          ];\n          var pyUrl='https://data.texas.gov/resource/naix-2893.json?$limit=500&$select=location_name,location_address,location_zip,total_receipts&$where='+encodeURIComponent(pyWhere.join(' AND '));\n          return fetch(pyUrl).then(function(r){return r.json();}).then(function(pyVenues){\n            var pyMap={};\n            (pyVenues||[]).forEach(function(p){\n              var k=(p.location_name||'')+'|'+(p.location_zip||'');\n              pyMap[k]=parseFloat(p.total_receipts)||0;\n            });\n            geocoded.forEach(function(v){\n              var k=(v.record.location_name||'')+'|'+(v.record.location_zip||'');\n              if(pyMap[k]!==undefined) v.record._py_total=pyMap[k];\n            });\n            _nearbyGeocoded=geocoded;\n            renderNearbyCards(geocoded, radiusMi);\n          }).catch(function(){\n            _nearbyGeocoded=geocoded;\n            renderNearbyCards(geocoded, radiusMi);\n          });''',
    '''          var pyWhere=[\n            cityWhereClause(nearCities),\n            "obligation_end_date_yyyymmdd>='"+pyY+'-'+pyM+"-01T00:00:00.000'",\n            "obligation_end_date_yyyymmdd<'"+pyNy+'-'+pyPad+"-01T00:00:00.000'"\n          ];\n          var pyUrl='https://data.texas.gov/resource/naix-2893.json?$limit=3000&$select=location_name,location_address,location_zip,total_receipts&$where='+encodeURIComponent(pyWhere.join(' AND '));\n          return fetch(pyUrl).then(function(r){return r.json();}).then(function(pyVenues){\n            var pyMap={};\n            (pyVenues||[]).forEach(function(p){\n              var k=(p.location_name||'')+'|'+(p.location_zip||'');\n              pyMap[k]=parseFloat(p.total_receipts)||0;\n            });\n            geocoded.forEach(function(v){\n              var k=(v.record.location_name||'')+'|'+(v.record.location_zip||'');\n              if(pyMap[k]!==undefined) v.record._py_total=pyMap[k];\n            });\n            _nearbyGeocoded=geocoded;\n            renderNearbyCards(geocoded, radiusMi);\n          }).catch(function(){\n            _nearbyGeocoded=geocoded;\n            renderNearbyCards(geocoded, radiusMi);\n          });''',
    "findNearby: PY multi-city where",
)

with open(PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Patched {changed} location(s) in {PATH}")
