#!/usr/bin/env python3
"""build_venue_types.py: stricter matching to cut false tags (restaurants next to a hotel/attraction).
- entertainment: needs an address or name match (no "it's nearby" matches); generic tourism=attraction landmarks ignored
- hotel: a proximity match needs the venue to sit inside the hotel's footprint, not just near it
- stadium: unchanged (concession stands often have their own address)
Run from the repo root: python patch_build_strict.py"""
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

apply("""                    'num': tags.get('addr:housenumber', ''), 'street': tags.get('addr:street', ''),
                }""", """                    'num': tags.get('addr:housenumber', ''), 'street': tags.get('addr:street', ''),
                    'tourism': tags.get('tourism', ''),
                }""", "keep tourism tag")
apply("""        if diag_m(f['box']) > MAX_DIAG_M[f['cat']]:
            continue
""", """        if diag_m(f['box']) > MAX_DIAG_M[f['cat']]:
            continue
        if f['cat'] == 'e' and f.get('tourism') == 'attraction':
            continue      # generic landmarks (historic buildings etc.) - too many restaurants sit in or next to them
""", "skip attractions")
apply("""            close = d <= MARGIN[f['cat']] and key not in approx
""", """            # proximity alone: stadiums within the margin; hotels only when the venue sits inside the footprint;
            # never for entertainment (too many restaurants sit next to a theatre or museum)
            close = key not in approx and ((f['cat'] == 's' and d <= MARGIN['s']) or (f['cat'] == 'h' and d == 0))
""", "stricter proximity")
if crlf: src = src.replace("\r\n", "\n")
with open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(src)
print("Patched " + PATH)
