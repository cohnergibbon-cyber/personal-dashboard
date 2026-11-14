#!/usr/bin/env python3
"""
Mobile: the history popup's two tables (Period comparison, Full history) fit the phone screen - no sideways scroll.
- tables in the popup drop the global 480px/420px minimum width on phones, with tighter padding and a font size
  that scales with the screen width
- comparison row labels stack on two lines ("R12" over its date range); "$ Variance"/"% Variance" headers shorten
- popup uses a little more of the screen width on phones
Desktop is unchanged. Run from the repo root: python patch_mobile_modal.py
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

apply("@media (max-width: 500px) { .modal-cards { grid-template-columns: repeat(2,1fr); } }\n",
      "@media (max-width: 500px) { .modal-cards { grid-template-columns: repeat(2,1fr); } }\n"
      "@media (max-width: 640px) {\n"
      "  .modal-overlay { padding: 12px 8px; }\n"
      "  .modal { padding: 16px 12px; }\n"
      "  #modal-body table { min-width: 0 !important; font-size: clamp(9px, 2.75vw, 11.5px); }\n"
      "  #modal-body thead th { padding: 7px 3px; font-size: 8px; letter-spacing: 0.03em; }\n"
      "  #modal-body tbody td { padding: 8px 3px; font-size: inherit; }\n"
      "  #modal-body tbody td.num { font-size: inherit; letter-spacing: -0.03em; }\n"
      "  #modal-body table.comp-table { font-size: clamp(8.5px, 2.5vw, 11px); }\n"
      "  #modal-body .comp-table th, #modal-body .comp-table td { padding-left: 2px; padding-right: 2px; }\n"
      "  #modal-body .comp-table td { font-variant-numeric: tabular-nums; letter-spacing: -0.02em; }\n"
      "  #modal-body .comp-table td:first-child { white-space: normal; line-height: 1.25; font-weight: 500; }\n"
      "  #modal-body .comp-sub { display: block; font-size: 0.8em; font-weight: 400; color: var(--text3); white-space: nowrap; }\n"
      "  #modal-body .m-hide { display: none; }\n"
      "}\n",
      "mobile modal css")
apply("<th>$ Variance</th><th>% Variance</th></tr></thead><tbody>';\n      html+='<tr><td>'+mLabel+'</td>'+",
      "<th>$ Var<span class=\"m-hide\">iance</span></th><th>% <span class=\"m-hide\">Variance</span></th></tr></thead><tbody>';\n      html+='<tr><td>'+mLabel+'</td>'+",
      "comparison headers")
apply("html+='<tr><td>YTD (thru '+mLabel+')</td>'+",
      "html+='<tr><td>YTD <span class=\"comp-sub\">(thru '+mLabel+')</span></td>'+",
      "ytd label")
apply("html+='<tr><td>R12 ('+r12Label+')</td>'+",
      "html+='<tr><td>R12 <span class=\"comp-sub\">('+r12Label+')</span></td>'+",
      "r12 label")
if crlf: html = html.replace("\n", "\r\n")
with open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print(f"Patched {changed} location(s) in {PATH}")
