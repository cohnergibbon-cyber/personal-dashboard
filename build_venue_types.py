"""
build_venue_types.py
Tags TABC venues as hotel / stadium / entertainment by cross-referencing each
venue's address against OpenStreetMap (free, no API key, redistributable under
ODbL - attribution: (c) OpenStreetMap contributors).

Why OSM and not Yelp/Google: Yelp Fusion and Google Places need API keys and
their terms restrict storing/caching results, so we could not ship the tags in
a static file. OSM data can be stored and reused.

How it works
  1. Downloads every Texas hotel/motel/resort, stadium/arena, and
     entertainment feature (theatre, cinema, casino, events venue, museum,
     zoo, theme park, bowling, ...) from the public Overpass API in 16 map
     tiles (cached in %TEMP%, so re-runs are fast and resumable).
  2. Loads every distinct TABC (name, address) and the coordinates from
     static/tx_venues_geo.json.
  3. A venue gets a type when its point falls inside / right next to the OSM
     feature's bounding box, OR the OSM feature carries the same street
     address, OR the names clearly match (within a larger radius).
     ZIP-centroid "approximate" coordinates are only trusted with an address
     or name match.
  4. Writes static/tx_venue_types.json: {"ADDR|CITY|ZIP5": "h"|"s"|"e"}.
     Venues not listed are restaurants/bars (the default). The app combines
     this with its name-keyword heuristic.

Run from the repo root:   python build_venue_types.py
Requirements: pip install requests
"""
import json, os, sys, time, math, re, collections
import requests

ROOT = os.path.dirname(os.path.abspath(__file__))
GEO_PATH = os.path.join(ROOT, 'static', 'tx_venues_geo.json')
OUT_PATH = os.path.join(ROOT, 'static', 'tx_venue_types.json')
CACHE_DIR = os.path.join(os.environ.get('TEMP', ROOT), 'tabc_osm_cache')
TABC_API = 'https://data.texas.gov/resource/naix-2893.json'
HEADERS = {'User-Agent': 'tabc-explorer/1.0 (personal research tool; venue type tagging)'}
MIRRORS = ['https://overpass-api.de/api/interpreter',
           'https://overpass.private.coffee/api/interpreter',
           'https://overpass.kumi.systems/api/interpreter']
BBOX = (25.8, -106.7, 36.6, -93.5)   # S, W, N, E  (Texas)
TILES = 4

CATS = {
    'h': ('hotel',
          'nwr[tourism~"^(hotel|motel|resort)$"];nwr[building=hotel];'),
    's': ('stadium',
          'nwr[leisure=stadium];nwr[building=stadium];'
          'nwr[leisure=sports_centre][name~"Arena|Stadium|Coliseum|Dome",i];'),
    'e': ('entertainment',
          'nwr[amenity~"^(theatre|cinema|casino|events_venue|arts_centre|conference_centre|music_venue)$"];'
          'nwr[tourism~"^(theme_park|zoo|aquarium|museum|attraction)$"];'
          'nwr[leisure~"^(bowling_alley|water_park|amusement_arcade|miniature_golf)$"];'),
}
# margin (meters) around a feature's bounding box inside which a venue counts as "at" the feature
MARGIN = {'h': 30, 's': 60, 'e': 40}
NAME_MARGIN_MULT = 4          # larger margin when the names also match
MAX_DIAG_M = {'h': 1500, 's': 1500, 'e': 4000}   # ignore absurdly large bounding boxes (campuses, parks)


def log(*a):
    print(*a, flush=True)


# ── Overpass download (tiled, cached, mirror failover) ──────────────────────
def tile_boxes():
    s, w, n, e = BBOX
    dl, dn = (n - s) / TILES, (e - w) / TILES
    for i in range(TILES):
        for j in range(TILES):
            yield (round(s + i * dl, 4), round(w + j * dn, 4), round(s + (i + 1) * dl, 4), round(w + (j + 1) * dn, 4))


def overpass(query):
    last = None
    for attempt in range(6):
        url = MIRRORS[attempt % len(MIRRORS)]
        try:
            r = requests.post(url, data={'data': query}, headers=HEADERS, timeout=240)
            if r.status_code == 200 and r.text.lstrip().startswith('{'):
                return r.json()
            last = 'HTTP %s' % r.status_code
        except Exception as ex:
            last = str(ex)[:120]
        wait = 10 * (attempt + 1)
        log('    retry in %ds (%s via %s)' % (wait, last, url.split('/')[2]))
        time.sleep(wait)
    raise RuntimeError('Overpass failed: %s' % last)


def download_features():
    os.makedirs(CACHE_DIR, exist_ok=True)
    feats = {}
    boxes = list(tile_boxes())
    for code, (label, body) in CATS.items():
        for n, (s, w, nn, e) in enumerate(boxes, 1):
            cache = os.path.join(CACHE_DIR, '%s_%d.json' % (code, n))
            if os.path.exists(cache):
                data = json.load(open(cache))
            else:
                q = '[out:json][timeout:200][bbox:%s,%s,%s,%s];(%s);out tags bb center;' % (s, w, nn, e, body)
                log('  %s tile %d/%d ...' % (label, n, len(boxes)))
                data = overpass(q)
                json.dump(data, open(cache, 'w'))
                time.sleep(3)
            for el in data.get('elements', []):
                b = el.get('bounds')
                c = el.get('center') or ({'lat': el.get('lat'), 'lon': el.get('lon')} if 'lat' in el else None)
                if not c or c.get('lat') is None:
                    continue
                if b:
                    box = (b['minlat'], b['minlon'], b['maxlat'], b['maxlon'])
                else:
                    box = (c['lat'], c['lon'], c['lat'], c['lon'])
                tags = el.get('tags', {})
                feats[(code, el['type'], el['id'])] = {
                    'cat': code, 'box': box, 'name': tags.get('name', ''),
                    'num': tags.get('addr:housenumber', ''), 'street': tags.get('addr:street', ''),
                }
        log('  %s: %d features so far' % (label, sum(1 for k in feats if k[0] == code)))
    return list(feats.values())


# ── Geometry helpers ────────────────────────────────────────────────────────
M_PER_DEG_LAT = 111320.0


def dist_to_box_m(lat, lon, box):
    minlat, minlon, maxlat, maxlon = box
    mlon = M_PER_DEG_LAT * math.cos(math.radians(lat))
    dy = 0.0 if minlat <= lat <= maxlat else (minlat - lat if lat < minlat else lat - maxlat) * M_PER_DEG_LAT
    dx = 0.0 if minlon <= lon <= maxlon else (minlon - lon if lon < minlon else lon - maxlon) * mlon
    return math.hypot(dx, dy)


def diag_m(box):
    minlat, minlon, maxlat, maxlon = box
    mlon = M_PER_DEG_LAT * math.cos(math.radians((minlat + maxlat) / 2))
    return math.hypot((maxlat - minlat) * M_PER_DEG_LAT, (maxlon - minlon) * mlon)


# ── Name / address matching ─────────────────────────────────────────────────
LEGAL = {'THE', 'LLC', 'INC', 'LP', 'LTD', 'LLP', 'CO', 'CORP', 'DBA', 'PLLC', 'AND'}
GENERIC = {'BAR', 'GRILL', 'RESTAURANT', 'RESTAURANTS', 'CAFE', 'KITCHEN', 'TAVERN', 'PUB', 'LOUNGE', 'BISTRO',
           'CANTINA', 'TEXAS', 'TX', 'HOUSE', 'EATERY', 'BREWING', 'COMPANY', 'PARTNERS', 'HOLDINGS', 'HOLDING',
           'GROUP', 'BEVERAGE', 'BEVERAGES', 'ENTERPRISES', 'INTERNATIONAL', 'HOTEL', 'HOTELS', 'INN', 'SUITES',
           'RESORT', 'CENTER', 'CENTRE', 'STADIUM', 'ARENA', 'THEATER', 'THEATRE', 'CINEMA', 'MUSEUM', 'CONVENTION',
           'N', 'S', 'E', 'W', 'NORTH', 'SOUTH', 'EAST', 'WEST', 'BY', 'AT', 'OF'}


def core_tokens(s):
    toks = re.sub(r'[^A-Z0-9 ]+', ' ', s.upper().replace('&', ' AND ')).split()
    return {t for t in toks if len(t) >= 3 and t not in LEGAL and t not in GENERIC and not t.isdigit()}


def names_match(venue_names, feat_name):
    fa = core_tokens(feat_name)
    if not fa:
        return False
    for vn in venue_names:
        va = core_tokens(vn)
        if va and len(va & fa) / min(len(va), len(fa)) >= 0.6:
            return True
    return False


SUFFIX = {'ST', 'STREET', 'AVE', 'AVENUE', 'BLVD', 'BOULEVARD', 'RD', 'ROAD', 'DR', 'DRIVE', 'LN', 'LANE', 'PKWY',
          'PARKWAY', 'HWY', 'HIGHWAY', 'CT', 'COURT', 'PL', 'PLACE', 'WAY', 'TRL', 'TRAIL', 'CIR', 'CIRCLE', 'FWY',
          'FREEWAY', 'N', 'S', 'E', 'W', 'NORTH', 'SOUTH', 'EAST', 'WEST', 'NE', 'NW', 'SE', 'SW', 'LOOP', 'EXPY'}


def addr_parts(addr):
    a = re.sub(r'\b(STE|SUITE|UNIT|BLDG|FL|RM|#)\b.*$', '', addr.upper()).strip()
    m = re.match(r'(\d+)\s+(.*)$', a)
    if not m:
        return None, set()
    words = {w for w in re.sub(r'[^A-Z0-9 ]+', ' ', m.group(2)).split() if w not in SUFFIX}
    return m.group(1), words


def address_match(venue_addr, feat):
    if not feat['num'] or not feat['street']:
        return False
    num, words = addr_parts(venue_addr)
    if not num or num != feat['num'].strip() or not words:
        return False
    fwords = {w for w in re.sub(r'[^A-Z0-9 ]+', ' ', feat['street'].upper()).split() if w not in SUFFIX}
    return bool(words & fwords)


# ── Main ────────────────────────────────────────────────────────────────────
def fetch_venue_names():
    names = collections.defaultdict(set)
    offset, limit = 0, 10000
    while True:
        url = (TABC_API + '?$limit=%d&$offset=%d&$select=location_name,location_address,location_city,location_zip'
               '&$group=location_name,location_address,location_city,location_zip&$order=location_zip,location_address,location_name' % (limit, offset))
        batch = requests.get(url, headers=HEADERS, timeout=60).json()
        if not batch:
            break
        for v in batch:
            k = '%s|%s|%s' % ((v.get('location_address') or '').upper().strip(),
                              (v.get('location_city') or '').upper().strip(), (v.get('location_zip') or '')[:5])
            if v.get('location_name'):
                names[k].add(v['location_name'])
        log('  venue names: %d addresses so far' % len(names))
        if len(batch) < limit:
            break
        offset += limit
        time.sleep(0.3)
    return names


def main():
    log('Loading geo file...')
    geo = json.load(open(GEO_PATH))
    log('  %d geocoded addresses' % len(geo))
    share = collections.Counter(tuple(v) for v in geo.values())
    approx = {k for k, v in geo.items() if share[tuple(v)] >= 5}     # ZIP-centroid fallbacks share coordinates
    log('  %d look like ZIP-centroid approximations' % len(approx))

    log('Downloading OSM features (cached in %s)...' % CACHE_DIR)
    feats = download_features()
    log('  %d OSM features total' % len(feats))

    # spatial grid over feature bounding boxes (cell ~0.01 deg)
    CELL = 0.01
    grid = collections.defaultdict(list)
    for f in feats:
        if diag_m(f['box']) > MAX_DIAG_M[f['cat']]:
            continue
        minlat, minlon, maxlat, maxlon = f['box']
        for gy in range(int((minlat - 0.003) / CELL) - 1, int((maxlat + 0.003) / CELL) + 2):
            for gx in range(int((minlon - 0.003) / CELL) - 1, int((maxlon + 0.003) / CELL) + 2):
                grid[(gy, gx)].append(f)

    log('Fetching TABC venue names...')
    names = fetch_venue_names()

    log('Matching venues to OSM features...')
    result, why = {}, collections.Counter()
    for key, (lat, lon) in geo.items():
        addr = key.split('|')[0]
        vnames = names.get(key, ())
        best = None
        for f in grid.get((int(lat / CELL), int(lon / CELL)), ()):
            d = dist_to_box_m(lat, lon, f['box'])
            if d > MARGIN[f['cat']] * NAME_MARGIN_MULT:
                continue
            a_ok = address_match(addr, f)
            n_ok = bool(vnames) and names_match(vnames, f['name'])
            close = d <= MARGIN[f['cat']] and key not in approx
            if not (a_ok or n_ok or close):
                continue
            score = (0 if a_ok else 1, 0 if n_ok else 1, d / MARGIN[f['cat']])
            if best is None or score < best[0]:
                best = (score, f['cat'], 'address' if a_ok else 'name' if n_ok else 'proximity')
        if best:
            result[key] = best[1]
            why[best[2]] += 1

    counts = collections.Counter(result.values())
    log('Tagged %d of %d addresses: hotel %d, stadium %d, entertainment %d  (by %s)' % (
        len(result), len(geo), counts['h'], counts['s'], counts['e'], dict(why)))
    with open(OUT_PATH, 'w') as f:
        json.dump(result, f, separators=(',', ':'), sort_keys=True)
    log('Wrote %s (%d bytes)' % (OUT_PATH, os.path.getsize(OUT_PATH)))
    log("\nDeploy with: git add static/tx_venue_types.json && git commit -m 'Update venue types' && git push")


if __name__ == '__main__':
    main()
