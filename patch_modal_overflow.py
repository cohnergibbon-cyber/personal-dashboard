#!/usr/bin/env python3
"""
Fix: the history modal's "Period comparison" table had no horizontal-
scroll wrapper, unlike the "Full history" table right below it. A global
CSS rule (`table { min-width: 480px }`, meant for the desktop Explorer
results table) forces every <table> on the page to be at least 480px
wide. On a phone viewport that's wider than the modal's available space,
and with nothing local to catch the overflow, the whole page gets
dragged into horizontal scroll instead of just that one table —
producing the shifted/cut-off modal seen on mobile.

Run from the repo root: python patch_modal_overflow.py
"""
import sys

PATH = "static/texas_alcohol_explorer.html"

with open(PATH, "r", encoding="utf-8") as f:
    html = f.read()

old = '''      html+='<div class="comp-section"><div class="comp-title">Period comparison — '+mLabel+'</div>';
      html+='<table class="comp-table"><thead><tr><th></th><th>CY ('+refPeriod.year+')</th><th>PY ('+(refPeriod.year-1)+')</th><th>$ Variance</th><th>% Variance</th></tr></thead><tbody>';'''
new = '''      html+='<div class="comp-section"><div class="comp-title">Period comparison — '+mLabel+'</div>';
      html+='<div style="overflow-x:auto;-webkit-overflow-scrolling:touch"><table class="comp-table"><thead><tr><th></th><th>CY ('+refPeriod.year+')</th><th>PY ('+(refPeriod.year-1)+')</th><th>$ Variance</th><th>% Variance</th></tr></thead><tbody>';'''

n = html.count(old)
if n != 1:
    sys.exit(f"ABORT: expected 1 occurrence of the comp-table open, found {n}. No changes written.")
html = html.replace(old, new, 1)

old2 = '''      html+='</tbody></table></div>';

      html+='<div class="hist-section">'''
new2 = '''      html+='</tbody></table></div></div>';

      html+='<div class="hist-section">'''

n2 = html.count(old2)
if n2 != 1:
    sys.exit(f"ABORT: expected 1 occurrence of the comp-table close, found {n2}. No changes written.")
html = html.replace(old2, new2, 1)

with open(PATH, "w", encoding="utf-8") as f:
    f.write(html)

print("Patched 2 location(s) in " + PATH)
