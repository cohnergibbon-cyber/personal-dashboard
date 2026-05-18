"""
patch_compare.py
Fixes Compare tab on the original texas_alcohol_explorer.html:
- 5 venue input boxes with live dropdowns (unchanged)
- Selecting a venue turns its box green and enables Compare button
- Compare button stays disabled until 2+ venues are selected
- Shows selected count next to button

Run from personal-dashboard root: python patch_compare.py
"""
import sys, os

HTML_PATH = os.path.join("static", "texas_alcohol_explorer.html")

PATCHES = [
    # 1. Button row: add disabled + sel-count
    (
        '''      <div style="display:flex;gap:8px;margin-top:14px">
        <button class="btn-run" id="cmp-run-btn" onclick="runComparison()">Compare</button>
        <button class="btn-clear" onclick="clearComparison()">Clear</button>
      </div>''',
        '''      <div style="display:flex;align-items:center;gap:10px;margin-top:14px">
        <button class="btn-run" id="cmp-run-btn" onclick="runComparison()" disabled>Compare</button>
        <button class="btn-clear" onclick="clearComparison()">Clear</button>
        <span id="cmp-sel-count" style="font-family:var(--mono);font-size:11px;color:var(--text3);"></span>
      </div>'''
    ),
    # 2. Confirmed CSS
    (
        '.cmp-venue-input:focus { border-color:var(--accent); }',
        '.cmp-venue-input:focus { border-color:var(--accent); }\n.cmp-venue-input.cmp-confirmed { border-color:var(--pos); background:var(--pos-dim); }'
    ),
    # 3. cmpSelectVenue + updateCmpBtn
    (
        '''function cmpSelectVenue(slot, venue) {
  cmpVenues[slot] = venue;
}''',
        '''function cmpSelectVenue(slot, venue) {
  cmpVenues[slot] = venue;
  var inputs = document.querySelectorAll(\'.cmp-venue-input\');
  if (inputs[slot]) inputs[slot].classList.add('cmp-confirmed');
  updateCmpBtn();
}

function updateCmpBtn() {
  var count = cmpVenues.filter(function(v){ return v !== null; }).length;
  var btn = document.getElementById('cmp-run-btn');
  var lbl = document.getElementById('cmp-sel-count');
  btn.disabled = count < 2;
  lbl.textContent = count >= 2 ? count + ' selected' : (count === 1 ? '1 selected \u2014 need 1 more' : '');
}'''
    ),
    # 4. clearComparison reset
    (
        '''function clearComparison() {
  cmpVenues = [null,null,null,null,null];
  document.querySelectorAll(\'.cmp-venue-input\').forEach(function(i){i.value='';});
  document.querySelectorAll(\'.cmp-suggestions\').forEach(function(s){s.style.display='none';});
  document.getElementById('cmp-result').style.display='none';
  document.getElementById('cmp-status').style.display='none';
  cmpHistory = {};
}''',
        '''function clearComparison() {
  cmpVenues = [null,null,null,null,null];
  cmpHistory = {};
  document.querySelectorAll(\'.cmp-venue-input\').forEach(function(i){ i.value=''; i.classList.remove('cmp-confirmed'); });
  document.querySelectorAll(\'.cmp-suggestions\').forEach(function(s){s.style.display='none';});
  document.getElementById('cmp-result').style.display='none';
  document.getElementById('cmp-status').style.display='none';
  document.getElementById('cmp-run-btn').disabled = true;
  document.getElementById('cmp-sel-count').textContent = '';
}'''
    ),
    # 5. Re-type clears slot
    (
        '  if (q.length < 2) { sugBox.style.display = \'none\'; return; }',
        '''  if (cmpVenues[slot]) { cmpVenues[slot] = null; input.classList.remove('cmp-confirmed'); updateCmpBtn(); }
  if (q.length < 2) { sugBox.style.display = \'none\'; return; }'''
    ),
    # 6. runComparison guard
    (
        '''function runComparison() {
  var status = document.getElementById('cmp-status');
  status.style.display = 'block';
  status.textContent = 'Resolving venues\u2026';''',
        '''function runComparison() {
  var selected = cmpVenues.filter(function(v){return v!==null;});
  if (selected.length < 2) return;
  var status = document.getElementById('cmp-status');
  status.style.display = 'block';
  status.textContent = 'Fetching history for ' + selected.length + ' venue(s)\u2026';'''
    ),
]

def main():
    if not os.path.exists(HTML_PATH):
        print(f"ERROR: {HTML_PATH} not found. Run from personal-dashboard root.")
        sys.exit(1)
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    print(f"Patching {HTML_PATH} ({len(content):,} chars)...")
    changes = 0
    for i, (old, new) in enumerate(PATCHES, 1):
        if old in content:
            content = content.replace(old, new, 1)
            changes += 1
            print(f"  [OK] Patch {i} applied")
        else:
            print(f"  [SKIP] Patch {i} already applied or not found")
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Done. {changes} change(s) applied.")

if __name__ == "__main__":
    main()
