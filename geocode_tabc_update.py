"""
geocode_tabc_update.py
Fetches all current TABC venues from the API and geocodes any addresses
NOT already in tx_venues_geo.json, then merges them in.

Run from personal-dashboard root:
    python geocode_tabc_update.py

Requirements: pip install requests

Changes from the previous version:
  - Strips suite/unit numbers (STE, SUITE, UNIT, #, BLDG, FL, RM, and
    compound cases like "STE 100 & 300") before geocoding — Nominatim
    frequently fails to parse addresses with trailing unit info even
    when the base street address is well-mapped.
  - Falls back to a ZIP-code centroid when the exact address still
    can't be found. OpenStreetMap's US coverage has real house-number
    gaps (confirmed: several real, currently-operating Carrollton/Dallas
    addresses returned zero results even with suite stripping and even
    against the Census Bureau's geocoder as a cross-check) — a venue
    positioned at its ZIP centroid is far more useful for a "venues
    within N miles" feature than a venue that's invisible entirely.
    These are tagged '~approx' in the progress output so you can see
    how many are exact vs. approximate.
  - All Nominatim calls (exact-address attempts AND zip-centroid
    fallbacks) now go through one rate-limited helper, so the 1 req/sec
    budget is respected across both call types, not just per-venue.
    ZIP centroid lookups are cached in-memory so venues sharing a ZIP
    only pay for one extra request.
"""

import json, time, os, re
import requests

GEO_PATH = os.path.join('static', 'tx_venues_geo.json')
NOMINATIM = 'https://nominatim.openstreetmap.org/search'
TABC_API  = 'https://data.texas.gov/resource/naix-2893.json'
HEADERS   = {'User-Agent': 'tabc-explorer/1.0 (personal research tool)'}

def addr_key(addr, city, zip_):
    return f"{(addr or '').upper().strip()}|{(city or '').upper().strip()}|{(zip_ or '')[:5]}"

# ── Rate limiting: one choke point for every Nominatim request ─────────────
_last_request_time = [0.0]
def _nominatim_get(params):
    elapsed = time.time() - _last_request_time[0]
    if elapsed < 1.1:
        time.sleep(1.1 - elapsed)
    r = requests.get(NOMINATIM, params=params, headers=HEADERS, timeout=10)
    _last_request_time[0] = time.time()
    return r

# ── Suite/unit stripping ────────────────────────────────────────────────────
SUITE_RE = re.compile(
    r'\s*[,#]?\s*(STE|SUITE|UNIT|BLDG|BUILDING|FL|FLOOR|RM|ROOM|#)\.?\s*[\w-]*\s*(&\s*[\w-]*)?\s*$',
    re.IGNORECASE
)
def strip_suite(addr):
    prev = None
    a = addr or ''
    while prev != a:
        prev = a
        a = SUITE_RE.sub('', a).strip()
    return a

# ── ZIP centroid fallback (cached — many venues share a ZIP) ───────────────
_zip_cache = {}
def geocode_zip_centroid(zip_):
    if not zip_:
        return None
    if zip_ in _zip_cache:
        return _zip_cache[zip_]
    coords = None
    try:
        r = _nominatim_get({'q': f"{zip_}, TX, USA", 'format': 'json', 'limit': 1, 'countrycodes': 'us'})
        data = r.json()
        if data:
            coords = [float(data[0]['lat']), float(data[0]['lon'])]
    except Exception:
        pass
    _zip_cache[zip_] = coords
    return coords

def geocode(addr, city, zip_):
    """Returns (coords, method). method is 'exact', 'zip_fallback', or None."""
    stripped = strip_suite(addr)
    q = f"{stripped}, {city}, TX {zip_}, USA"
    try:
        r = _nominatim_get({'q': q, 'format': 'json', 'limit': 1, 'countrycodes': 'us'})
        data = r.json()
        if data:
            return [float(data[0]['lat']), float(data[0]['lon'])], 'exact'
    except Exception:
        pass
    coords = geocode_zip_centroid(zip_)
    if coords:
        return coords, 'zip_fallback'
    return None, None

# ── Load existing geo file ──────────────────────────────────────────────────
print(f"Loading {GEO_PATH}...")
if os.path.exists(GEO_PATH):
    with open(GEO_PATH, 'r') as f:
        geo = json.load(f)
else:
    geo = {}
print(f"  {len(geo):,} existing keys")

# ── Fetch all current venues from TABC API ──────────────────────────────────
print("\nFetching distinct venue addresses from TABC API...")
all_venues = []
offset = 0
limit = 5000
while True:
    # Use $group to get distinct address combos only — avoids pulling all 1M+ historical rows
    url = (f"{TABC_API}?$limit={limit}&$offset={offset}"
           f"&$select=location_address,location_city,location_zip"
           f"&$group=location_address,location_city,location_zip"
           f"&$having=count(*)>0"
           f"&$order=location_zip,location_address")
    r = requests.get(url, headers=HEADERS, timeout=30)
    batch = r.json()
    if not batch:
        break
    all_venues.extend(batch)
    print(f"  Fetched {len(all_venues):,} unique addresses...")
    if len(batch) < limit:
        break
    offset += limit
    time.sleep(0.3)

print(f"  Total unique addresses: {len(all_venues):,}")

# ── Dedupe by address key ───────────────────────────────────────────────────
unique = {}
for v in all_venues:
    k = addr_key(v.get('location_address',''), v.get('location_city',''), v.get('location_zip',''))
    if k not in unique:
        unique[k] = v
print(f"  Unique addresses: {len(unique):,}")

# ── Find missing ones ───────────────────────────────────────────────────────
missing = {k: v for k, v in unique.items() if k not in geo}
print(f"  Missing from geo file: {len(missing):,}")

if not missing:
    print("\nNothing to geocode — geo file is up to date!")
else:
    print(f"\nGeocoding {len(missing):,} new addresses (1 req/sec, exact match with ZIP-centroid fallback)...")
    added = 0
    approx = 0
    failed = 0
    keys = list(missing.keys())

    for i, k in enumerate(keys):
        v = missing[k]
        addr = v.get('location_address', '')
        city = v.get('location_city', '')
        zip_ = v.get('location_zip', '')

        coords, method = geocode(addr, city, zip_)
        if coords:
            geo[k] = coords
            added += 1
            if method == 'zip_fallback':
                approx += 1
        else:
            failed += 1

        if (i + 1) % 50 == 0:
            # Save progress every 50
            with open(GEO_PATH, 'w') as f:
                json.dump(geo, f)
            print(f"  [{i+1}/{len(keys)}] Added: {added} ({approx} approx via ZIP), Failed: {failed} — saved")

    # Final save
    with open(GEO_PATH, 'w') as f:
        json.dump(geo, f)

    print(f"\nDone! Added {added} new coords ({approx} approximate via ZIP centroid), {failed} failed to geocode entirely.")
    print(f"Geo file now has {len(geo):,} keys.")
    print(f"\nDeploy with: git add static/tx_venues_geo.json && git commit -m 'Update geo file' && git push")
