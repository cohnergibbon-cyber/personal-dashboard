import re, sys, os

path = r'C:\Users\CohnerGibbons\personal-dashboard\static\texas_alcohol_explorer.html'

with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

print('File size before:', len(c))

# 1. Add pill HTML if missing
if 'setRadius(1)' not in c:
    old = '''<div class="map-fcard">
      <div class="section-label">Find nearby</div>
      <button class="loc-btn" onclick="findNearby()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 2v3m0 14v3M2 12h3m14 0h3"/></svg>
        Use my location
      </button>
    </div>'''
    new = '''<div class="map-fcard">
      <div class="section-label">Find nearby</div>
      <button class="loc-btn" id="loc-btn" onclick="findNearby()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M12 2v3m0 14v3M2 12h3m14 0h3"/></svg>
        Use my location
      </button>
      <div class="radius-row">
        <div class="radius-label-row">
          <span class="radius-lbl">Radius</span>
          <span class="radius-val" id="radius-val">1 mi</span>
        </div>
        <div class="radius-pills">
          <button class="radius-pill active" onclick="setRadius(1)">1 mi</button>
          <button class="radius-pill" onclick="setRadius(2)">2 mi</button>
          <button class="radius-pill" onclick="setRadius(3)">3 mi</button>
          <button class="radius-pill" onclick="setRadius(4)">4 mi</button>
          <button class="radius-pill" onclick="setRadius(5)">5 mi</button>
        </div>
      </div>
    </div>'''
    if old in c:
        c = c.replace(old, new)
        print('Pill HTML: added')
    else:
        print('Pill HTML: fcard not found, skipping')
else:
    print('Pill HTML: already present')

# 2. Add pill CSS if missing
if '.radius-pill {' not in c:
    pill_css = '''
.radius-row { margin-top: 14px; }
.radius-label-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.radius-lbl { font-size: 11px; font-family: var(--mono); text-transform: uppercase; letter-spacing: 0.08em; color: var(--text3); }
.radius-val { font-size: 12px; font-weight: 700; color: var(--accent); font-family: var(--mono); }
.radius-pills { display: flex; gap: 6px; }
.radius-pill { flex: 1; height: 36px; border: 1.5px solid var(--border2); border-radius: 20px; background: transparent; color: var(--text2); font-size: 12px; font-family: var(--mono); font-weight: 600; cursor: pointer; transition: all 0.15s; -webkit-tap-highlight-color: transparent; }
.radius-pill.active { background: var(--accent); border-color: var(--accent); color: #F5F0E8; }
.radius-pill:hover:not(.active) { border-color: var(--accent); color: var(--accent); }
.radius-pill:active { opacity: 0.75; }
'''
    c = c.replace('</style>', pill_css + '</style>', 1)
    print('Pill CSS: added')
else:
    print('Pill CSS: already present')

# 3. Fix next button - ensure results div shown on every renderTable call
if "getElementById('results').style.display='block'" not in c:
    c = c.replace(
        'function renderTable() {\n  var start=(page-1)*PER',
        "function renderTable() {\n  document.getElementById('results').style.display='block';\n  var start=(page-1)*PER"
    )
    # Also try isMobile variant
    c = c.replace(
        'function renderTable() {\n  var isMobile',
        "function renderTable() {\n  document.getElementById('results').style.display='block';\n  var isMobile"
    )
    print('Next button fix: added')
else:
    print('Next button fix: already present')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

print('File size after:', len(c))
print('Done - file patched in place')
