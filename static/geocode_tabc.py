import re

path = r'C:\Users\CohnerGibbons\personal-dashboard\static\texas_alcohol_explorer.html'

with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

print('File size before:', len(c))
changes = 0

# ── 1. Fix modal to not bleed off screen on mobile
old_modal = '.modal { background: var(--s1); border-radius: var(--r); max-width: 860px; margin: 0 auto; padding: 20px; position: relative; border: 1px solid var(--border); }'
new_modal = '.modal { background: var(--s1); border-radius: var(--r); max-width: 860px; width: 100%; margin: 0 auto; padding: 16px; position: relative; border: 1px solid var(--border); box-sizing: border-box; overflow-x: hidden; }'
if old_modal in c:
    c = c.replace(old_modal, new_modal); print('1. Modal CSS fixed'); changes += 1
else:
    print('1. Modal CSS: not found')

old_overlay = '.modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 500; overflow-y: auto; padding: 20px 14px; }'
new_overlay = '.modal-overlay { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 500; overflow-y: auto; padding: 8px; -webkit-overflow-scrolling: touch; }'
if old_overlay in c:
    c = c.replace(old_overlay, new_overlay); print('2. Overlay CSS fixed'); changes += 1
else:
    print('2. Overlay CSS: not found')

# ── 2. Fix modal inner tables to not overflow
if 'modal-cmp-tbl' in c and 'table-layout: fixed' not in c[c.find('.modal-cmp-tbl'):c.find('.modal-cmp-tbl')+200]:
    c = c.replace(
        '.modal-cmp-tbl { width: 100%; border-collapse: collapse;',
        '.modal-cmp-tbl { width: 100%; border-collapse: collapse; table-layout: fixed; overflow-x: hidden;'
    )
    print('3. modal-cmp-tbl fixed'); changes += 1
else:
    print('3. modal-cmp-tbl: already fixed or not found')

# Add mobile modal override in media query
mobile_modal_css = """
@media (max-width: 640px) {
  .modal-overlay { padding: 0; }
  .modal { border-radius: 0; min-height: 100vh; border: none; }
  .modal-cmp-tbl td, .modal-cmp-tbl th { font-size: 11px; padding: 6px 4px; }
  .modal-hist-tbl td, .modal-hist-tbl th { font-size: 11px; padding: 6px 4px; }
  .modal-name { font-size: 18px; }
  .modal-cards { grid-template-columns: repeat(2,1fr); }
}
"""
if '@media (max-width: 640px)' not in c:
    c = c.replace('</style>', mobile_modal_css + '</style>', 1)
    print('4. Mobile modal media query: added'); changes += 1
else:
    print('4. Mobile media query: already present')

# ── 3. Fix city summary table - make it only 3 columns, scrollable
old_city_build = """  function cm(v) {
    var n=parseFloat(v); if(isNaN(n)||n===0) return n===0?'$0':'—';
    if(Math.abs(n)>=1000000) return '$'+(n/1000000).toFixed(1)+'M';
    return '$'+Math.round(n/1000)+'K';
  }
  var html = '<table class="city-tbl"><thead><tr>'
    +'<th style="text-align:left;width:38%">City</th>'
    +'<th style="text-align:right">CY</th>'
    +'<th style="text-align:right">$ Var</th>'
    +'<th style="text-align:right">% Var</th>'
    +'</tr></thead><tbody>';"""

new_city_build = """  function cm(v) {
    var n=parseFloat(v); if(isNaN(n)||n===0) return n===0?'$0':'—';
    if(Math.abs(n)>=1000000) return '$'+(n/1000000).toFixed(1)+'M';
    return '$'+Math.round(n/1000)+'K';
  }
  var html = '<table class="city-tbl"><thead><tr>'
    +'<th style="text-align:left;width:40%;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">City</th>'
    +'<th style="text-align:right;width:22%">CY</th>'
    +'<th style="text-align:right;width:22%">$ Var</th>'
    +'<th style="text-align:right;width:16%">%</th>'
    +'</tr></thead><tbody>';"""

if old_city_build in c:
    c = c.replace(old_city_build, new_city_build); print('5. City table cols fixed'); changes += 1
else:
    print('5. City table: pattern not found')

# Wrap city table in overflow-x:auto
old_city_wrap = "document.getElementById('city-table-wrap').innerHTML = '<div style=\"overflow-x:auto;-webkit-overflow-scrolling:touch;\">'+html+'</div>';"
if old_city_wrap not in c:
    old_city_set = "document.getElementById('city-table-wrap').innerHTML = html;"
    if old_city_set in c:
        c = c.replace(old_city_set, "document.getElementById('city-table-wrap').innerHTML = '<div style=\"overflow-x:auto;-webkit-overflow-scrolling:touch;\">'+html+'</div>';")
        print('6. City table scroll wrap: added'); changes += 1
    else:
        print('6. City table wrap: pattern not found')
else:
    print('6. City table scroll wrap: already present')

# ── 4. Fix PY data missing for some cards
# The issue: pyPromise uses same $limit=5000, but when all-cities query returns
# 5000 CY records, the PY query may miss some. 
# Fix: increase PY limit and ensure pyUrl always fetches when pyYear exists
old_py_null = 'var pyUrl = pyYear ? buildFetchUrl(pyYear, month, isYTD, isT12) : null;'
new_py_null = 'var pyUrl = buildFetchUrl(pyYear||String(parseInt(year)-1), month, isYTD, isT12);'
if old_py_null in c:
    c = c.replace(old_py_null, new_py_null); print('7. pyUrl always fetched'); changes += 1
else:
    print('7. pyUrl: not found')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

print('File size after:', len(c))
print('Changes made:', changes)
print('Done.')
