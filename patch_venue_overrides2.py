#!/usr/bin/env python3
"""Venue overrides, round 2: overrides can also be keyed by owner ("owner:NORMALIZED OWNER") or venue name ("name:NORMALIZED NAME").
Run from the repo root: python patch_venue_overrides2.py"""
import sys
PATH = "static/texas_alcohol_explorer.html"
with open(PATH, "r", encoding="utf-8", newline="") as f:
    html = f.read()
crlf = "\r\n" in html
html = html.replace("\r\n", "\n")
old = "  if (_vtOv && key && _vtOv[key] && VT_CODE[_vtOv[key]]) return VT_CODE[_vtOv[key]];\n"
new = ("  if (_vtOv) {\n"
       "    var ovc = (key && _vtOv[key]) || _vtOv['name:' + n] || (o && _vtOv['owner:' + o]);\n"
       "    if (ovc && VT_CODE[ovc]) return VT_CODE[ovc];\n"
       "  }\n")
if html.count(old) != 1:
    sys.exit(f"ABORT: expected 1 occurrence, found {html.count(old)}. No changes written.")
html = html.replace(old, new)
if crlf: html = html.replace("\n", "\r\n")
with open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print("Patched 1 location in " + PATH)
