#!/usr/bin/env python3
"""
Fix: "Taxpayer" search in Explorer only matched the legal taxpayer_name field,
so a search like "Postino" missed franchise locations filed under unrelated
LLC names (e.g. "POSTINO WINE CAFE" filed under "XYZ HOLDINGS LLC"). This
widens the search to match taxpayer_name OR location_name, and relabels the
field so the behavior is clear.

Run from the repo root: python patch_taxpayer_search.py
"""
import re
import sys

PATH = "static/texas_alcohol_explorer.html"

with open(PATH, "r", encoding="utf-8") as f:
    html = f.read()

changed = 0

# 1) Live query path (baseFilters(), used by runQuery()) — widen match to
#    taxpayer_name OR location_name.
old_live = '''    if (taxpayer) w.push("upper(taxpayer_name) like '%"+taxpayer.toUpperCase().replace(/'/g,"''")+ "%'");'''
new_live = '''    if (taxpayer) { var tUp = taxpayer.toUpperCase().replace(/'/g,"''"); w.push("(upper(taxpayer_name) like '%"+tUp+"%' OR upper(location_name) like '%"+tUp+"%')"); }'''
if old_live not in html:
    sys.exit("ABORT: live taxpayer filter line not found (baseFilters). No changes written.")
html = html.replace(old_live, new_live, 1)
changed += 1

# 2) Legacy/unused buildWhereFilters() — fix for consistency in case it's
#    ever wired back up (also matches taxpayer_name OR location_name).
old_dead = '''  if (taxpayer) where.push("upper(taxpayer_name) like '%" + taxpayer.toUpperCase().replace(/'/g,"''") + "%'");'''
new_dead = '''  if (taxpayer) { var tUp2 = taxpayer.toUpperCase().replace(/'/g,"''"); where.push("(upper(taxpayer_name) like '%" + tUp2 + "%' OR upper(location_name) like '%" + tUp2 + "%')"); }'''
if old_dead not in html:
    sys.exit("ABORT: legacy taxpayer filter line not found (buildWhereFilters). No changes written.")
html = html.replace(old_dead, new_dead, 1)
changed += 1

# 3) Relabel the field + placeholder so behavior matches expectation.
old_label = '''          <div class="flabel">Taxpayer</div>
          <input id="f-taxpayer" type="text" placeholder="e.g. FB SOCIETY" autocomplete="off" autocorrect="off" autocapitalize="characters" />'''
new_label = '''          <div class="flabel">Taxpayer / Business Name</div>
          <input id="f-taxpayer" type="text" placeholder="e.g. FB SOCIETY or POSTINO" autocomplete="off" autocorrect="off" autocapitalize="characters" />'''
if old_label not in html:
    sys.exit("ABORT: taxpayer field label/placeholder not found. No changes written.")
html = html.replace(old_label, new_label, 1)
changed += 1

with open(PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Patched {changed} location(s) in {PATH}")
