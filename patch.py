import re

path = r'C:\Users\CohnerGibbons\personal-dashboard\static\texas_alcohol_explorer.html'

with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

print('File size before:', len(c))
changes = 0

# 1. City table header - responsive (2 cols mobile, 4 cols desktop)
old_hdr = "'<table class=\"city-tbl\"><thead><tr><th>City</th><th>CY</th><th>PY</th><th>$ Var</th><th>% Var</th></tr></thead><tbody>'"
new_hdr = """(function(){var isMob=window.innerWidth<640; return '<table class=\"city-tbl\"><thead><tr><th style=\"text-align:left\">City</th><th style=\"text-align:right\">CY</th>'+(isMob?'':'<th style=\"text-align:right\">$ Var</th><th style=\"text-align:right\">%</th>')+'</tr></thead><tbody>';})()"""
if old_hdr in c: c = c.replace(old_hdr, new_hdr); print('1. City header: fixed'); changes += 1
else: print('1. City header: not found')

# 2. Add isMob var before top.forEach loop
old_loop = '  top.forEach(function(r, i) {'
new_loop = '  var isMob = window.innerWidth < 640;\n  top.forEach(function(r, i) {'
if old_loop in c and 'var isMob' not in c[c.find('top.forEach')-60:c.find('top.forEach')]:
    c = c.replace(old_loop, new_loop, 1); print('2. isMob var: added'); changes += 1
else: print('2. isMob var: already present or loop not found')

# 3. City rows - show var cols only on desktop, fix city ellipsis
old_row = """html += '<tr>'+
      '<td><span style="color:#999;font-size:9px;margin-right:4px;">'+(i+1)+'</span>'+city+'</td>'+
      '<td>'+cm(r.cy)+'</td>'+
      '<td>'+(r.py?cm(r.py):'—')+'</td>'+
      '<td class="'+(r.varAmt>=0?'pos':'neg')+'">'+(r.varAmt>=0?'+':'')+cm(r.varAmt)+'</td>'+
      '<td class="'+(r.varPct!==null?r.varPct>=0?'pos':'neg':'')+'\">'+(r.varPct!==null?(r.varPct>=0?'+':'')+r.varPct.toFixed(1)+'%':'—')+'</td>'+
      '</tr>';"""
new_row = """html += '<tr>'+
      '<td style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:120px"><span style="color:#999;font-size:9px;margin-right:4px;">'+(i+1)+'</span>'+city+'</td>'+
      '<td style="text-align:right">'+cm(r.cy)+'</td>'+
      (isMob?'':'<td style="text-align:right" class="'+(r.varAmt>=0?'pos':'neg')+'">'+(r.varAmt>=0?'+':'')+cm(r.varAmt)+'</td>'+
      '<td style="text-align:right" class="'+(r.varPct!==null?r.varPct>=0?'pos':'neg':'')+'\">'+(r.varPct!==null?(r.varPct>=0?'+':'')+r.varPct.toFixed(1)+'%':'—')+'</td>')+
      '</tr>';"""
if old_row in c: c = c.replace(old_row, new_row); print('3. City rows: fixed'); changes += 1
else: print('3. City rows: not found - may already be fixed')

# 4. History table scroll
old_hist = 'Full history</div><div class="hist-wrap"><table>'
new_hist = 'Full history</div><div class="hist-wrap" style="overflow-x:auto;-webkit-overflow-scrolling:touch"><table style="min-width:420px">'
if old_hist in c: c = c.replace(old_hist, new_hist); print('4. History scroll: fixed'); changes += 1
else: print('4. History scroll: already fixed or not found')

# 5. city-tbl remove fixed layout
c = c.replace(
    '.city-tbl { width: 100%; border-collapse: collapse; table-layout: fixed; }',
    '.city-tbl { width: 100%; border-collapse: collapse; }'
)
print('5. city-tbl CSS: updated')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)
print('File size after:', len(c))
print('Changes made:', changes)
print('Done.')
