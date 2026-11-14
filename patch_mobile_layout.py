#!/usr/bin/env python3
"""
Mobile layout fixes (phones):
1. Top-10 cities table: a global `table { min-width: 480px }` stopped it shrinking to its card, so the $ Var / %
   columns ran off the right edge (and could make Safari zoom the whole page out). The table now fits its card.
2. Pagination ("Next") was hidden behind the bottom tab bar: extra bottom padding on phones so the last row of
   every tab scrolls fully clear of the bar.
Run from the repo root: python patch_mobile_layout.py
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

apply(".city-tbl { width: 100%; border-collapse: collapse; table-layout: fixed; }",
      ".city-tbl { width: 100%; min-width: 0; border-collapse: collapse; table-layout: fixed; }",
      "city table min-width")
apply(".page.active { display: block; }\n",
      ".page.active { display: block; }\n"
      "@media (max-width: 640px) {\n"
      "  html, body { overflow-x: hidden; }\n"
      "  body { padding-bottom: calc(var(--tab-h) + var(--safe) + 84px); }\n"
      "}\n",
      "mobile bottom padding")
if crlf: html = html.replace("\n", "\r\n")
with open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print(f"Patched {changed} location(s) in {PATH}")
