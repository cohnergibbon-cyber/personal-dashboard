#!/usr/bin/env python3
"""
Openings tab upgrade (branch: feature/openings-tracker)

1. Replaces the New Permits / Recently Closed tables with the same card
   system the Nearby tab uses (.venue-card): name, address line, permit
   date (+ "N days ago" and a NEW badge for permits <= 30 days old), owner.
2. Adds a rolling-window selector (Last 7 / 14 / 30 days, or a specific
   month) in the spirit of texasnewopenings.com. TABC License Information
   data is current through yesterday, so the tab now defaults to the last
   30 days instead of "2 months ago" (that default only made sense for the
   lagging receipts dataset).
3. HTML-escapes API strings before injecting them into cards.
4. Raises row caps so large result sets are not silently cut off:
   Openings $limit 1000 -> 5000 (with a visible note if hit), and the four
   Nearby TABC receipts queries $limit 3000 -> 10000.
5. CSV export file names reflect the rolling window.

Run from the repo root: python patch_openings_cards.py
"""
import sys

PATH = "static/texas_alcohol_explorer.html"
with open(PATH, "r", encoding="utf-8", newline="") as f:
    html = f.read()

# Normalise to LF for matching; restore CRLF at the end if the file used it.
crlf = "\r\n" in html
html = html.replace("\r\n", "\n")
changed = 0


def apply(old, new, label, count=1):
    global html, changed
    n = html.count(old)
    if n != count:
        sys.exit(f"ABORT: expected {count} occurrence(s) of [{label}], found {n}. No changes written.")
    html = html.replace(old, new)
    changed += 1


# ── 1) Markup: tables -> card containers ────────────────────────────────
apply(
    '''      <div class="tbl-wrap">
        <table>
          <thead><tr><th>Location</th><th>City</th><th>Address</th><th>Issue Date</th><th>Owner</th></tr></thead>
          <tbody id="op-new-tbody"></tbody>
        </table>
      </div>''',
    '''      <div id="op-new-cards"></div>''',
    "new-permits table",
)
apply(
    '''      <div class="tbl-wrap">
        <table>
          <thead><tr><th>Location</th><th>City</th><th>Address</th><th>Status</th><th>Status Change Date</th><th>Owner</th></tr></thead>
          <tbody id="op-closed-tbody"></tbody>
        </table>
      </div>''',
    '''      <div id="op-closed-cards"></div>''',
    "closed table",
)

# ── 2) Markup: window selector ──────────────────────────────────────────
apply(
    '''      <div style="margin-bottom:12px;">
        <div class="flabel">Period</div>
        <div class="period-row">
          <select id="op-month" class="sel">''',
    '''      <div style="margin-bottom:12px;">
        <div class="flabel">Window</div>
        <select id="op-window" class="sel" style="width:100%" onchange="opWindowChanged()">
          <option value="30">Last 30 days</option>
          <option value="14">Last 14 days</option>
          <option value="7">Last 7 days</option>
          <option value="month">Specific month</option>
        </select>
      </div>
      <div style="margin-bottom:12px;" id="op-period-wrap">
        <div class="flabel">Period</div>
        <div class="period-row">
          <select id="op-month" class="sel">''',
    "window selector markup",
)

# ── 3) CSS for cards ────────────────────────────────────────────────────
apply(
    '''.venue-stat strong { color: var(--text); font-weight: 500; }''',
    '''.venue-stat strong { color: var(--text); font-weight: 500; }
.venue-owner { font-size: 11px; color: var(--text3); margin-top: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.op-badge { display: inline-block; margin-left: 8px; padding: 1px 7px; border-radius: 10px; font-family: var(--mono); font-size: 9px; font-weight: 600; letter-spacing: 0.06em; background: var(--pos); color: #fff; vertical-align: middle; }
.op-empty { padding: 18px 14px; font-size: 12px; color: var(--text3); text-align: center; border: 1px dashed var(--border2); border-radius: var(--r-sm); margin-bottom: 8px; }''',
    "card css",
)

# ── 4) Default period: current month; window defaults to 30 days ───────
apply(
    '''  // Default to 2 months ago, matching Explorer's default (data updates daily,
  // but 2-months-back keeps a full month's worth of issuances/closures visible by default)
  var now = new Date();
  now.setMonth(now.getMonth() - 2);''',
    '''  // License data updates daily (newest records are from yesterday), unlike the lagging
  // receipts dataset, so default the month picker to the current month. The tab itself
  // defaults to a rolling 30-day window (see #op-window).
  var now = new Date();''',
    "default period",
)
apply(
    '''    citySel.appendChild(opt);
  });
})();

function opFmtDate(v) {''',
    '''    citySel.appendChild(opt);
  });
  opWindowChanged();
})();

function opWindowChanged() {
  var rolling = document.getElementById('op-window').value !== 'month';
  document.getElementById('op-period-wrap').style.display = rolling ? 'none' : 'block';
}

function opEsc(s) {
  return String(s == null ? '' : s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function opAddrLine(r) {
  var tail = [r.city || '', (r.zip || '').slice(0,5)].join(' ').trim();
  return [r.address || '', tail].filter(Boolean).join(', ');
}

function opDaysAgo(v) {
  if (!v) return null;
  var p = String(v).replace(/T.*/,'').split('-');
  if (p.length !== 3) return null;
  var d = new Date(parseInt(p[0],10), parseInt(p[1],10)-1, parseInt(p[2],10));
  var t = new Date(); t = new Date(t.getFullYear(), t.getMonth(), t.getDate());
  return Math.max(0, Math.round((t - d) / 86400000));
}

function opAgeLabel(n) {
  if (n === 0) return 'today';
  if (n === 1) return 'yesterday';
  if (n < 60) return n + ' days ago';
  return Math.round(n / 30) + ' mo ago';
}

function wireOpCards(boxId, rows) {
  document.getElementById(boxId).querySelectorAll('.venue-card').forEach(function(card) {
    card.addEventListener('click', function() {
      var r = rows[parseInt(this.getAttribute('data-idx'), 10)];
      // trade_name/owner -> locationName/taxpayerName is a name-matching heuristic across two
      // independently-maintained datasets (license registry vs. receipts), not a guaranteed exact join.
      if (r) openHistory(r.trade_name||'', r.owner||'', '', r.city||'', (r.zip||'').slice(0,5), r.address||'');
    });
  });
}

function opFmtDate(v) {''',
    "helpers + window init",
)

# ── 5) clearOpenings ────────────────────────────────────────────────────
apply(
    '''  ['op-month','op-year'].forEach(function(id){ document.getElementById(id).selectedIndex = 0; });''',
    '''  var _n = new Date();
  document.getElementById('op-year').value = String(_n.getFullYear());
  document.getElementById('op-month').value = String(_n.getMonth() + 1).padStart(2, '0');
  document.getElementById('op-window').value = '30';
  opWindowChanged();''',
    "clearOpenings reset",
)

# ── 6) Date range honours rolling window ───────────────────────────────
apply(
    '''function opDateRange(month, year) {
  var y = parseInt(year, 10), m = parseInt(month, 10);''',
    '''function opDateRange(month, year) {
  var win = document.getElementById('op-window').value;
  if (win !== 'month') {
    var nDays = parseInt(win, 10);
    var fmt = function(d) {
      return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0') + 'T00:00:00.000';
    };
    var endD = new Date(); endD.setDate(endD.getDate() + 1);              // include today
    var startD = new Date(); startD.setDate(startD.getDate() - nDays + 1);
    return { start: fmt(startD), end: fmt(endD) };
  }
  var y = parseInt(year, 10), m = parseInt(month, 10);''',
    "opDateRange window",
)

# ── 7) Row caps ─────────────────────────────────────────────────────────
apply("?$limit=1000&$order=original_issue_date+DESC", "?$limit=5000&$order=original_issue_date+DESC", "new limit")
apply("?$limit=1000&$order=status_change_date+DESC", "?$limit=5000&$order=status_change_date+DESC", "closed limit")
apply(
    '''    document.getElementById('op-summary').textContent = opNewRows.length + ' new · ' + opClosedRows.length + ' closed';''',
    '''    var opCapped = opNewRows.length >= 5000 || opClosedRows.length >= 5000;
    document.getElementById('op-summary').textContent = opNewRows.length + ' new · ' + opClosedRows.length + ' closed' + (opCapped ? ' · capped at 5,000' : '');''',
    "summary + cap note",
)
apply("naix-2893.json?$limit=3000&", "naix-2893.json?$limit=10000&", "nearby limits", count=4)

# ── 8) Rendering: cards instead of table rows ──────────────────────────
apply(
    '''  var periodLabel = mNames[parseInt(month,10)-1] + ' ' + year;''',
    '''  var opWin = document.getElementById('op-window').value;
  var periodLabel = opWin === 'month' ? (mNames[parseInt(month,10)-1] + ' ' + year) : ('last ' + opWin + ' days');''',
    "periodLabel",
)

start_marker = "  var newBody = document.getElementById('op-new-tbody');"
end_marker = "}\n\nfunction exportOpeningsCSV(section) {"
if html.count(start_marker) != 1 or html.count(end_marker) != 1:
    sys.exit("ABORT: renderOpenings body markers not found exactly once. No changes written.")
s = html.index(start_marker)
e = html.index(end_marker)
new_body = '''  var newBox = document.getElementById('op-new-cards');
  if (!opNewRows.length) {
    newBox.innerHTML = '<div class="op-empty">No new MB permits issued in ' + opEsc(periodLabel + filterSuffix) + '.</div>';
  } else {
    newBox.innerHTML = opNewRows.map(function(r, i) {
      var age = opDaysAgo(r.original_issue_date);
      var badge = (age !== null && age <= 30) ? '<span class="op-badge">NEW</span>' : '';
      return '<div class="venue-card" data-idx="' + i + '">'
        + '<div class="venue-name">' + opEsc(r.trade_name || '—') + badge + '</div>'
        + '<div class="venue-addr">' + opEsc(opAddrLine(r)) + '</div>'
        + '<div class="venue-stats">'
        + '<div class="venue-stat">Permit date <strong>' + opFmtDate(r.original_issue_date) + '</strong></div>'
        + (age !== null ? '<div class="venue-stat" style="color:var(--text3)">' + opAgeLabel(age) + '</div>' : '')
        + '</div>'
        + (r.owner ? '<div class="venue-owner">' + opEsc(r.owner) + '</div>' : '')
        + '</div>';
    }).join('');
    wireOpCards('op-new-cards', opNewRows);
  }

  var closedBox = document.getElementById('op-closed-cards');
  if (!opClosedRows.length) {
    closedBox.innerHTML = '<div class="op-empty">No closures in ' + opEsc(periodLabel + filterSuffix) + '.</div>';
  } else {
    closedBox.innerHTML = opClosedRows.map(function(r, i) {
      var age = opDaysAgo(r.status_change_date);
      return '<div class="venue-card" data-idx="' + i + '">'
        + '<div class="venue-name">' + opEsc(r.trade_name || '—') + '</div>'
        + '<div class="venue-addr">' + opEsc(opAddrLine(r)) + '</div>'
        + '<div class="venue-stats">'
        + '<div class="venue-stat neg">' + opEsc(r.primary_status || '—') + '</div>'
        + '<div class="venue-stat">Status date <strong>' + opFmtDate(r.status_change_date) + '</strong></div>'
        + (age !== null ? '<div class="venue-stat" style="color:var(--text3)">' + opAgeLabel(age) + '</div>' : '')
        + '</div>'
        + (r.owner ? '<div class="venue-owner">' + opEsc(r.owner) + '</div>' : '')
        + '</div>';
    }).join('');
    wireOpCards('op-closed-cards', opClosedRows);
  }
'''
html = html[:s] + new_body + html[e:]
changed += 1

# ── 9) CSV filename ─────────────────────────────────────────────────────
apply(
    '''  var month = document.getElementById('op-month').value, year = document.getElementById('op-year').value;
  downloadCSV(out, 'openings_'+section+'_'+year+'-'+month+'.csv');''',
    '''  var opWinSel = document.getElementById('op-window').value;
  var tag = opWinSel === 'month'
    ? document.getElementById('op-year').value + '-' + document.getElementById('op-month').value
    : 'last' + opWinSel + 'd';
  downloadCSV(out, 'openings_'+section+'_'+tag+'.csv');''',
    "csv filename",
)

if crlf:
    html = html.replace("\n", "\r\n")
with open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print(f"Patched {changed} location(s) in {PATH}")
