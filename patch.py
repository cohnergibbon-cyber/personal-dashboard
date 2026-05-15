import re

path = r'C:\Users\CohnerGibbons\personal-dashboard\static\texas_alcohol_explorer.html'

with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

print('File size before:', len(c))
changes = 0

# 1. Modal CSS
old = '.modal { background: var(--s1); border-radius: var(--r); max-width: 860px; margin: 0 auto; padding: 20px; position: relative; border: 1px solid var(--border); }'
new = '.modal { background: var(--s1); border-radius: var(--r); max-width: 860px; width: 100%; margin: 0 auto; padding: 16px; position: relative; border: 1px solid var(--border); box-sizing: border-box; overflow-x: hidden; }'
if old in c: c = c.replace(old, new); print('1. modal CSS: fixed'); changes += 1
else: print('1. modal CSS: not found')

# 2. Overlay CSS
old2 = '.modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 500; overflow-y: auto; padding: 20px 14px; }'
new2 = '.modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 500; overflow-y: auto; padding: 8px; -webkit-overflow-scrolling: touch; }'
if old2 in c: c = c.replace(old2, new2); print('2. overlay CSS: fixed'); changes += 1
else: print('2. overlay CSS: not found')

# 3. Mobile media query
if '@media (max-width: 640px)' not in c:
    mobile = """
@media (max-width: 640px) {
  .modal-overlay { padding: 0 !important; }
  .modal { border-radius: 0; min-height: 100vh; border-left: none; border-right: none; }
  .modal-cmp-tbl td, .modal-cmp-tbl th { font-size: 11px; padding: 5px 3px; }
  .modal-hist-tbl td, .modal-hist-tbl th { font-size: 11px; padding: 5px 3px; }
  .modal-cards { grid-template-columns: repeat(2,1fr); }
  .modal-name { font-size: 18px; padding-right: 36px; }
}
"""
    c = c.replace('</style>', mobile + '</style>', 1); print('3. Mobile media query: added'); changes += 1
else: print('3. Mobile media query: already present')

# 4. City table columns
old4 = "'<table class=\"city-tbl\"><thead><tr><th>City</th><th>CY</th><th>PY</th><th>$ Var</th><th>% Var</th></tr></thead><tbody>'"
new4 = """'<table class="city-tbl"><thead><tr>'
    +'<th style="text-align:left;width:42%">City</th>'
    +'<th style="text-align:right;width:20%">CY</th>'
    +'<th style="text-align:right;width:22%">$ Var</th>'
    +'<th style="text-align:right;width:16%">%</th>'
    +'</tr></thead><tbody>'"""
if old4 in c: c = c.replace(old4, new4); print('4. City cols: fixed'); changes += 1
else: print('4. City cols: not found')

# 5. City scroll wrap
old5 = "document.getElementById('city-table-wrap').innerHTML = html;"
new5 = "document.getElementById('city-table-wrap').innerHTML = '<div style=\"overflow-x:auto;-webkit-overflow-scrolling:touch\">'+html+'</div>';"
if old5 in c: c = c.replace(old5, new5); print('5. City scroll: added'); changes += 1
else: print('5. City scroll: already wrapped or not found')

# 6. Card variance color
old6 = "varHtml='<div class=\"venue-stat '+cls+'\">'+(varAmt>=0?'+':'')+fmtMoney(varAmt,false)+' ('+fmtPct(varPct)+')</div>';}"
new6 = "varHtml='<div class=\"venue-stat '+cls+'\" style=\"color:'+(varAmt>=0?'var(--pos)':'var(--neg)')+'\">'+(varAmt>=0?'+':'')+fmtMoney(varAmt,false)+' ('+fmtPct(varPct)+')</div>';}"
if old6 in c: c = c.replace(old6, new6); print('6. Card variance color: fixed'); changes += 1
else: print('6. Card variance color: not found (varClass may handle it)')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print('File size after:', len(c))
print('Changes made:', changes)
print('Done.')
