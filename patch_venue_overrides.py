#!/usr/bin/env python3
"""
Venue types, round 3: a hand-verified override list.
static/tx_venue_overrides.json maps "ADDR|CITY|ZIP5" -> h (hotel) / s (stadium) / e (entertainment) / r (restaurant).
An override beats the name rules and the OpenStreetMap lookup. Also adds BILLY BOB to the entertainment name rule.
Run from the repo root: python patch_venue_overrides.py
"""
import sys
PATH = "static/texas_alcohol_explorer.html"
with open(PATH, "r", encoding="utf-8", newline="") as f:
    html = f.read()
crlf = "\r\n" in html
html = html.replace("\r\n", "\n")
changed = 0
def apply(old, new, label):
    global html, changed
    n = html.count(old)
    if n != 1:
        sys.exit(f"ABORT: expected 1 occurrence of [{label}], found {n}. No changes written.")
    html = html.replace(old, new); changed += 1

apply("var VT_ENTERTAINMENT = /\\b(PAVILION|", "var VT_ENTERTAINMENT = /\\b(BILLY BOB|PAVILION|", "billy bob")
apply("var _vtMap = null, VT_VER = 0;\nvar VT_CODE = {h:'hotel', s:'stadium', e:'entertainment'};",
      "var _vtMap = null, _vtOv = null, VT_VER = 0;\nvar VT_CODE = {h:'hotel', s:'stadium', e:'entertainment', r:'restaurant'};", "decls")
apply("  // A name keyword is the strongest signal...\n",
      "  // Hand-verified overrides win over everything\n  if (_vtOv && key && _vtOv[key] && VT_CODE[_vtOv[key]]) return VT_CODE[_vtOv[key]];\n  // A name keyword is the strongest signal...\n", "override check")
apply("  .catch(function() { /* optional enhancement - name rules still apply */ });",
      "  .catch(function() { /* optional enhancement - name rules still apply */ });\n\n"
      "fetch('/static/tx_venue_overrides.json')\n"
      "  .then(function(r) { return r.ok ? r.json() : null; })\n"
      "  .then(function(m) { if (m) { _vtOv = m; VT_VER++; vtRefreshViews(); } })\n"
      "  .catch(function() { /* optional */ });", "override loader")
if crlf: html = html.replace("\n", "\r\n")
with open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print(f"Patched {changed} location(s) in {PATH}")
