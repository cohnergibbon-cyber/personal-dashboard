#!/usr/bin/env python3
"""
Venue types, round 2: use an address cross-reference, not just names.

1. The app loads static/tx_venue_types.json (built by build_venue_types.py from
   OpenStreetMap) - {"ADDR|CITY|ZIP5": "h"|"s"|"e"} - and uses it for any venue
   whose NAME doesn't already give the type away. So "HOSPITALITY INTERNATIONAL,
   INC." at a hotel's address becomes a Hotel, a venue inside a stadium
   becomes a Stadium, and so on. A name keyword (e.g. HOTEL) still wins.
2. More name rules for the misses seen in the Explorer's top venues:
   ALAMODOME / DOME / FIELD (anywhere in the name) and the big sports-venue
   concessionaires (Levy, Aramark Sports, Delaware North, Sportservice,
   Centerplate) -> Stadium; PAVILION / TEXAS LIVE / MUSIC VENUE -> Entertainment;
   GAYLORD -> Hotel.
3. The map loads in the background; when it arrives, any results already on
   screen re-render with the better types.

Run from the repo root: python patch_venue_type_lookup.py
"""
import sys

PATH = "static/texas_alcohol_explorer.html"
with open(PATH, "r", encoding="utf-8", newline="") as f:
    html = f.read()
crlf = "\r\n" in html
html = html.replace("\r\n", "\n")
changed = 0


def apply(old, new, label, count=1):
    global html, changed
    n = html.count(old)
    if n != count:
        sys.exit(f"ABORT: expected {count} occurrence(s) of [{label}], found {n}. No changes written.")
    html = html.replace(old, new)
    changed += 1


# ── Name-rule additions ─────────────────────────────────────────────────
apply(
    "var VT_STADIUM = /\\b(STADIUM|",
    "var VT_STADIUM = /\\b(STADIUM|ALAMODOME|DOME|FIELD|LEVY RESTAURANTS|ARAMARK SPORTS|DELAWARE NORTH|SPORTSERVICE|CENTERPLATE|",
    "stadium names",
)
apply(")\\b|\\bFIELD$/;", ")\\b/;", "stadium tail")
apply("var VT_HOTEL = /\\b(HOTEL|", "var VT_HOTEL = /\\b(GAYLORD|HOTEL|", "hotel names")
apply(
    "var VT_ENTERTAINMENT = /\\b(THEATER|",
    "var VT_ENTERTAINMENT = /\\b(PAVILION|TEXAS LIVE|MUSIC VENUE|THEATER|",
    "entertainment names",
)

# ── Lookup + versioned cache ────────────────────────────────────────────
apply(
    '''function vtGetType(name, owner) {
  var n = vtNorm(name).replace(/\\bPIZZA INN\\b/g, 'PIZZA'), o = vtNorm(owner);  // "Pizza Inn" is not a hotel
  if (VT_STADIUM.test(n)) return 'stadium';
  if (VT_HOTEL.test(n) || VT_HOTEL_OWNER.test(o)) return 'hotel';
  if (VT_ENTERTAINMENT.test(n)) return 'entertainment';
  return 'restaurant';
}

function vtRow(r, scope) {
  if (r._vt) return r._vt;
  r._vt = scope === 'openings' ? vtGetType(r.trade_name, r.owner) : vtGetType(r.location_name, r.taxpayer_name);
  return r._vt;
}''',
    '''// Address cross-reference built from OpenStreetMap (see build_venue_types.py). Loaded in the background.
var _vtMap = null, VT_VER = 0;
var VT_CODE = {h:'hotel', s:'stadium', e:'entertainment'};

function vtKeyOf(addr, city, zip) {
  return (String(addr || '').toUpperCase().trim() + '|' + String(city || '').toUpperCase().trim() + '|' + String(zip || '').slice(0, 5));
}

function vtGetType(name, owner, key) {
  var n = vtNorm(name).replace(/\\bPIZZA INN\\b/g, 'PIZZA'), o = vtNorm(owner);  // "Pizza Inn" is not a hotel
  // A name keyword is the strongest signal...
  if (VT_STADIUM.test(n)) return 'stadium';
  if (VT_HOTEL.test(n) || VT_HOTEL_OWNER.test(o)) return 'hotel';
  if (VT_ENTERTAINMENT.test(n)) return 'entertainment';
  // ...otherwise ask where the venue actually is
  if (_vtMap && key && _vtMap[key] && VT_CODE[_vtMap[key]]) return VT_CODE[_vtMap[key]];
  return 'restaurant';
}

function vtRow(r, scope) {
  if (r._vt && r._vtv === VT_VER) return r._vt;
  if (scope === 'openings') r._vt = vtGetType(r.trade_name, r.owner, vtKeyOf(r.address, r.city, r.zip));
  else r._vt = vtGetType(r.location_name, r.taxpayer_name, vtKeyOf(r.location_address, r.location_city, r.location_zip));
  r._vtv = VT_VER;
  return r._vt;
}

function vtRefreshViews() {
  try {
    if (allRows && allRows.length && document.getElementById('results').style.display !== 'none') renderTable();
    if (_nearbyGeocoded && _nearbyGeocoded.length) renderNearbyCards(_nearbyGeocoded, _currentRadius);
    if ((opNewRows && opNewRows.length) || (opClosedRows && opClosedRows.length)) opRerender();
  } catch (e) { /* views not ready yet - they will pick up the map on their next render */ }
}

fetch('/static/tx_venue_types.json')
  .then(function(r) { return r.ok ? r.json() : null; })
  .then(function(m) { if (m) { _vtMap = m; VT_VER++; vtRefreshViews(); } })
  .catch(function() { /* optional enhancement - name rules still apply */ });''',
    "vtGetType/vtRow + loader",
)

# modal header uses the address too
apply(
    "vtTag(vtGetType(locationName, taxpayerName))",
    "vtTag(vtGetType(locationName, taxpayerName, vtKeyOf(locationAddress, locationCity, locationZip)))",
    "modal tag key",
)

if crlf:
    html = html.replace("\n", "\r\n")
with open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print(f"Patched {changed} location(s) in {PATH}")
