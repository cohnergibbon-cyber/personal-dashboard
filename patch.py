path = r'C:\Users\CohnerGibbons\personal-dashboard\static\texas_alcohol_explorer.html'

with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

print('File size before:', len(c))
changes = 0

# ── 1. Remove duplicate th addEventListener (onclick already handles sort)
old_th_listeners = """['location_name','location_city','total_receipts','py_total','var_amt','var_pct'].forEach(function(k){
  var th=document.getElementById('th-'+k);if(th)th.addEventListener('click',function(){sortBy(k);});
});"""
if old_th_listeners in c:
    c = c.replace(old_th_listeners, '// sort handled by onclick on th elements')
    print('1. Removed duplicate th sort listeners'); changes += 1
else:
    print('1. Duplicate th listeners: not found (may already be fixed)')

# ── 2. Fix Next button - wrap in explicit handler that logs
old_next = "document.getElementById('btn-next').addEventListener('click',function(){page=Math.min(Math.ceil(allRows.length/PER),page+1);renderTable();});"
new_next = """document.getElementById('btn-next').addEventListener('click',function(){
  var tp=Math.ceil(allRows.length/PER)||1;
  if(page<tp){ page++; renderTable(); }
});"""
if old_next in c:
    c = c.replace(old_next, new_next)
    print('2. Next button: rewritten with explicit guard'); changes += 1
else:
    print('2. Next button: not found in expected form')

# ── 3. Fix Prev button similarly
old_prev = "document.getElementById('btn-prev').addEventListener('click',function(){page=Math.max(1,page-1);renderTable();});"
new_prev = """document.getElementById('btn-prev').addEventListener('click',function(){
  if(page>1){ page--; renderTable(); }
});"""
if old_prev in c:
    c = c.replace(old_prev, new_prev)
    print('3. Prev button: rewritten with explicit guard'); changes += 1
else:
    print('3. Prev button: not found in expected form')

# ── 4. Ensure results div shown at start of renderTable (not mid-function)
fn_start = c.find('function renderTable()')
fn_body = c[fn_start:fn_start+100]
if "getElementById('results').style.display='block'" not in fn_body:
    # Move the results show to the very top of the function
    c = c.replace(
        "function renderTable() {\n  var isMobile",
        "function renderTable() {\n  document.getElementById('results').style.display='block';\n  var isMobile"
    )
    print('4. results show moved to top of renderTable'); changes += 1
else:
    print('4. results show: already at top')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

print('File size after:', len(c))
print('Changes made:', changes)
print('Done.')
