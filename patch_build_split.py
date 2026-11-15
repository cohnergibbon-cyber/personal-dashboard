#!/usr/bin/env python3
"""build_venue_types.py: when a map tile keeps timing out on the Overpass servers, split it into 4 smaller boxes
(cached separately, up to 2 levels deep) instead of aborting. Run from the repo root: python patch_build_split.py"""
import sys
PATH = "build_venue_types.py"
with open(PATH, "r", encoding="utf-8", newline="") as f:
    src = f.read()
crlf = "\r\n" in src
src = src.replace("\r\n", "\n")
def apply(old, new, label):
    global src
    if src.count(old) != 1:
        sys.exit(f"ABORT: expected 1 occurrence of [{label}], found {src.count(old)}. No changes written.")
    src = src.replace(old, new)

apply('''def download_features():
''', '''def fetch_box(body, box, key, depth):
    """Fetch one bounding box. If the servers keep timing out, split it into 4 smaller boxes (each cached)."""
    s, w, n, e = box
    prefix = 'part_%s.' % key
    have_parts = any(f.startswith(prefix) for f in os.listdir(CACHE_DIR))
    if not have_parts:
        q = '[out:json][timeout:200][bbox:%s,%s,%s,%s];(%s);out tags bb center;' % (s, w, n, e, body)
        try:
            data = overpass(q)
            time.sleep(3)
            return data
        except RuntimeError:
            if depth >= 2:
                raise
        log('    splitting %s into 4 smaller boxes' % key)
    ml, mo = round((s + n) / 2, 4), round((w + e) / 2, 4)
    els = []
    for k, sub in enumerate([(s, w, ml, mo), (s, mo, ml, e), (ml, w, n, mo), (ml, mo, n, e)]):
        sk = '%s.%d' % (key, k)
        cache = os.path.join(CACHE_DIR, 'part_%s.json' % sk)
        if os.path.exists(cache):
            d = json.load(open(cache))
        else:
            log('    part %s ...' % sk)
            d = fetch_box(body, sub, sk, depth + 1)
            json.dump(d, open(cache, 'w'))
        els.extend(d.get('elements', []))
    return {'elements': els}


def download_features():
''', "add fetch_box")
apply('''                q = '[out:json][timeout:200][bbox:%s,%s,%s,%s];(%s);out tags bb center;' % (s, w, nn, e, body)
                log('  %s tile %d/%d ...' % (label, n, len(boxes)))
                data = overpass(q)
                json.dump(data, open(cache, 'w'))
                time.sleep(3)
''', '''                log('  %s tile %d/%d ...' % (label, n, len(boxes)))
                data = fetch_box(body, (s, w, nn, e), '%s_%d' % (code, n), 0)
                json.dump(data, open(cache, 'w'))
''', "use fetch_box")
if crlf: src = src.replace("\n", "\r\n")
with open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(src)
print("Patched " + PATH)
