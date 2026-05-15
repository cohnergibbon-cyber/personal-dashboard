import re

path = r'C:\Users\CohnerGibbons\personal-dashboard\static\texas_alcohol_explorer.html'

with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

print('File size before:', len(c))
changes = 0

# ── 1. Add $25k filter to the main TABC query in runQuery()
# Find the where clause builder in runQuery
old_where_build = '"total_receipts>0"'
new_where_build = '"total_receipts>=25000"'

if old_where_build in c:
    c = c.replace(old_where_build, new_where_build)
    print('1. $25k filter: added to runQuery'); changes += 1
else:
    # Try alternate forms
    alt = 'total_receipts>0'
    if alt in c:
        c = c.replace(alt, 'total_receipts>=25000', 1)
        print('1. $25k filter: added (alt form)'); changes += 1
    else:
        print('1. $25k filter: pattern not found - checking query build')
        idx = c.find('function runQuery')
        print(repr(c[idx:idx+800]))

# ── 2. Add footnote below the results pager
if '$25,000' not in c:
    old_pager_end = '</div>\n    </div>\n  </div>\n</div>\n\n<!-- ──'
    new_pager_end = '</div>\n      <div class="results-note">Showing venues with \u2265$25,000 monthly alcohol sales</div>\n    </div>\n  </div>\n</div>\n\n<!-- ──'
    if old_pager_end in c:
        c = c.replace(old_pager_end, new_pager_end)
        print('2. Footnote HTML: added'); changes += 1
    else:
        # Try simpler approach - add after pager div
        old_pager = '<div class="pager">'
        # Find the pager closing
        pager_idx = c.find(old_pager)
        pager_end = c.find('</div>', pager_idx) + 6
        note = '\n      <div class="results-note">Showing venues with \u2265$25,000 monthly alcohol sales</div>'
        c = c[:pager_end] + note + c[pager_end:]
        print('2. Footnote HTML: added (alt)'); changes += 1
else:
    print('2. Footnote: already present')

# ── 3. Add footnote CSS
if 'results-note' not in c:
    note_css = '\n.results-note { font-size: 11px; color: var(--text3); font-family: var(--mono); margin-top: 8px; padding: 0 2px; }'
    c = c.replace('</style>', note_css + '\n</style>', 1)
    print('3. Footnote CSS: added'); changes += 1
else:
    print('3. Footnote CSS: already present')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

print('File size after:', len(c))
print('Changes made:', changes)
print('Done.')
