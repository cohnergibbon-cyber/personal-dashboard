import re

path = r'C:\Users\CohnerGibbons\personal-dashboard\static\texas_alcohol_explorer.html'

with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

print('File size before:', len(c))
changes = 0

# ── 1. Wrap ALL bottom addEventListener calls in null checks
old_wire = """var _btnRun=document.getElementById('btn-run'); if(_btnRun)_btnRun.addEventListener('click',runQuery);
document.getElementById('btn-clear').addEventListener('click',clearAll);
document.getElementById('btn-prev').addEventListener('click',function(){
  if(page>1){ page--; renderTable(); }
});
document.getElementById('btn-next').addEventListener('click',function(){
  var tp=Math.ceil(allRows.length/PER)||1;
  if(page<tp){ page++; renderTable(); }
});"""

new_wire = """(function(){
  var btnRun=document.getElementById('btn-run');
  var btnClear=document.getElementById('btn-clear');
  var btnPrev=document.getElementById('btn-prev');
  var btnNext=document.getElementById('btn-next');
  if(btnRun) btnRun.addEventListener('click',runQuery);
  if(btnClear) btnClear.addEventListener('click',clearAll);
  if(btnPrev) btnPrev.addEventListener('click',function(){ if(page>1){page--;renderTable();} });
  if(btnNext) btnNext.addEventListener('click',function(){ var tp=Math.ceil(allRows.length/PER)||1; if(page<tp){page++;renderTable();} });
})();"""

if old_wire in c:
    c = c.replace(old_wire, new_wire)
    print('1. All button listeners null-guarded'); changes += 1
else:
    # Try to find and fix just the btn-clear line
    old_clear = "document.getElementById('btn-clear').addEventListener('click',clearAll);"
    new_clear = "var _bc=document.getElementById('btn-clear'); if(_bc)_bc.addEventListener('click',clearAll);"
    if old_clear in c:
        c = c.replace(old_clear, new_clear)
        print('1. btn-clear null guard added'); changes += 1
    else:
        print('1. btn-clear pattern not found - checking what is there')
        idx = c.find('btn-clear')
        while idx > 0:
            print(' ', repr(c[idx-10:idx+80]))
            idx = c.find('btn-clear', idx+1)

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

print('File size after:', len(c))
print('Changes made:', changes)
print('Done.')
