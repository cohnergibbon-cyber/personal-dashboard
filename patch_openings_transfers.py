#!/usr/bin/env python3
"""
Openings: stop showing ownership changes as "new" venues (and as closures).

Root cause: TABC issues a brand-new license (new license_id, new
original_issue_date) when an existing venue changes hands, and surrenders the
old one the same day. original_issue_date does NOT change on a plain renewal
(current_issued_date does), so these are not renewals - they are ownership
changes, but they look like "new permits" + "closures". Example: Twin Peaks,
1500 Market Pl, Irving - old license (2013) surrendered 2026-11-10, new
license to a new LLC issued 2026-11-10, 163 months of sales history.
In a 30-day sample, ~1 in 4 "new" permits had an earlier license at the
same address.

Fix: after fetching the new/closed lists, look up every other TABC license at
those addresses and classify each row:
  new       - no earlier license at the address
  replaced  - earlier, no-longer-active license at the address but a
              different concept (kept as new, with a "Replaces X" note)
  transfer  - earlier license at the address with a matching name or owner
              (new rows) / a newer license with a matching name or owner
              (closed rows) => same venue, new license. Hidden by default;
              a checkbox brings them back, flagged "Ownership change".
Also: the history modal falls back to venue name + address when the taxpayer
name has no history (new owner LLC), so ownership-change venues show their
real sales history instead of "No history found".

Run after patch_venue_types.py:  python patch_openings_transfers.py
"""
import sys

PATH = "static/texas_alcohol_explorer.html"
with open(PATH, "r", encoding="utf-8", newline="") as f:
    html = f.read()
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


# ── CSS ─────────────────────────────────────────────────────────────────
apply(
    '''.vt-line .vtag { margin-left:0; margin-top:3px; }''',
    '''.vt-line .vtag { margin-left:0; margin-top:3px; }
.op-toggle { display:flex; align-items:center; gap:8px; font-size:12px; color:var(--text2); margin-bottom:10px; cursor:pointer; }
.op-badge.muted { background:var(--text3); }
.venue-owner { white-space:normal; overflow:visible; text-overflow:clip; }''',
    "css",
)

# ── Markup: toggle ──────────────────────────────────────────────────────
apply(
    '''      <div id="tc-openings" class="type-chips" style="display:none;"></div>''',
    '''      <label class="op-toggle" id="op-transfer-wrap" style="display:none;"><input type="checkbox" id="op-show-transfers" onchange="opRerender()"> <span id="op-transfer-label"></span></label>
      <div id="tc-openings" class="type-chips" style="display:none;"></div>''',
    "toggle markup",
)

# ── Helpers ─────────────────────────────────────────────────────────────
apply(
    '''function opFmtDate(v) {''',
    r'''// ---- Ownership-change detection (see patch notes) ----
var opClassifyFailed = false;
var OP_LEGAL = {THE:1,LLC:1,INC:1,LP:1,LTD:1,LLP:1,CO:1,CORP:1,DBA:1,PLLC:1};
var OP_GENERIC = {BAR:1,GRILL:1,RESTAURANT:1,RESTAURANTS:1,CAFE:1,KITCHEN:1,TAVERN:1,PUB:1,LOUNGE:1,BISTRO:1,CANTINA:1,TEXAS:1,TX:1,HOUSE:1,EATERY:1,BREWING:1,COMPANY:1,PARTNERS:1,HOLDINGS:1,HOLDING:1,GROUP:1,BEVERAGE:1,BEVERAGES:1,ENTERPRISES:1,INTERNATIONAL:1,AND:1,N:1,S:1,E:1,W:1,NORTH:1,SOUTH:1,EAST:1,WEST:1,SPORTS:1};

function opTokens(s, dropGeneric) {
  return String(s || '').toUpperCase().replace(/&/g, ' AND ').replace(/[^A-Z0-9 ]+/g, ' ').split(/\s+/).filter(function(t) {
    return t && !OP_LEGAL[t] && !/^\d+$/.test(t) && !(dropGeneric && OP_GENERIC[t]);
  });
}

function opSameName(a, b) {
  var sa = opTokens(a, false).join(' '), sb = opTokens(b, false).join(' ');
  if (!sa || !sb) return false;
  if (sa === sb) return true;
  var long3 = function(t) { return t.length >= 3; };
  var ca = opTokens(a, true).filter(long3), cb = opTokens(b, true).filter(long3);
  if (!ca.length || !cb.length) return false;
  var shared = ca.filter(function(t) { return cb.indexOf(t) >= 0; }).length;
  return shared >= 1 && shared / Math.min(ca.length, cb.length) >= 0.6;
}

function opSameOwner(a, b) {
  var sa = opTokens(a, false).join(' '), sb = opTokens(b, false).join(' ');
  return !!sa && sa === sb;
}

function opAddrNorm(a) { return String(a || '').toUpperCase().replace(/\s+/g, ' ').trim(); }
function opAddrKey(r) { return opAddrNorm(r.address) + '|' + String(r.zip || '').slice(0, 5); }

function opClassify(newRows, closedRows) {
  opClassifyFailed = false;
  var seen = {}, addrs = [];
  newRows.concat(closedRows).forEach(function(r) {
    var a = opAddrNorm(r.address);
    if (a && !seen[a]) { seen[a] = 1; addrs.push(a); }
  });
  var chunks = [];
  for (var i = 0; i < addrs.length; i += 30) chunks.push(addrs.slice(i, i + 30));
  return Promise.all(chunks.map(function(ch) {
    var list = [];
    ch.forEach(function(a) { var e = a.replace(/'/g, "''"); list.push("'" + e + "'"); list.push("'" + e + " '"); });  // dataset has trailing-space variants
    var url = LICENSE_API + '?$limit=5000&$select=license_id,trade_name,owner,address,zip,original_issue_date,primary_status&$where='
      + encodeURIComponent('upper(address) in (' + list.join(',') + ')');
    return fetch(url).then(function(r) { if (!r.ok) throw new Error('lookup ' + r.status); return r.json(); });
  })).then(function(parts) {
    var byKey = {};
    [].concat.apply([], parts).forEach(function(o) { var k = opAddrKey(o); (byKey[k] = byKey[k] || []).push(o); });

    newRows.forEach(function(r) {
      r._kind = 'new'; r._note = ''; r._histOwner = '';
      var priors = (byKey[opAddrKey(r)] || []).filter(function(o) {
        return o.license_id !== r.license_id && o.original_issue_date && o.original_issue_date < r.original_issue_date;
      });
      if (!priors.length) return;
      var same = priors.filter(function(o) { return opSameName(o.trade_name, r.trade_name) || opSameOwner(o.owner, r.owner); });
      if (same.length) {
        same.sort(function(x, y) { return x.original_issue_date < y.original_issue_date ? -1 : 1; });
        r._kind = 'transfer';
        r._note = 'Existing venue since ' + same[0].original_issue_date.slice(0, 4) + ' (new license, likely ownership change)';
        r._histOwner = same[0].owner || '';
      } else {
        // Only call it a replacement when the earlier venue is no longer active; an ACTIVE license at
        // the same street address is usually just another tenant of the same building/mall.
        var gone = priors.filter(function(o) { return o.primary_status && o.primary_status !== 'Active'; });
        if (gone.length) {
          gone.sort(function(x, y) { return x.original_issue_date < y.original_issue_date ? 1 : -1; });
          r._kind = 'replaced';
          r._note = 'Replaces ' + (gone[0].trade_name || 'a prior venue');
        }
      }
    });

    closedRows.forEach(function(r) {
      r._kind = 'closed'; r._note = '';
      var sc = String(r.status_change_date || '').slice(0, 10);
      if (!sc) return;
      var cutoff = new Date(Date.parse(sc) - 90 * 864e5).toISOString().slice(0, 10);
      var succ = (byKey[opAddrKey(r)] || []).filter(function(o) {
        return o.license_id !== r.license_id && o.original_issue_date
          && o.original_issue_date.slice(0, 10) >= cutoff
          && o.original_issue_date >= (r.original_issue_date || '');
      });
      if (!succ.length) return;
      var same = succ.filter(function(o) { return opSameName(o.trade_name, r.trade_name) || opSameOwner(o.owner, r.owner); });
      if (same.length) { r._kind = 'transfer'; r._note = 'Same venue, new license' + (same[0].owner ? ' (' + same[0].owner + ')' : ''); }
      else { r._note = 'Replaced by ' + (succ[0].trade_name || 'another venue'); }
    });
    return true;
  }).catch(function() { opClassifyFailed = true; return false; });
}

function opShowTransfers() {
  var cb = document.getElementById('op-show-transfers');
  return !!(cb && cb.checked);
}

function opVisible(rows) {
  if (opShowTransfers()) return rows;
  return rows.filter(function(r) { return r._kind !== 'transfer'; });
}

function opRerender() {
  renderOpenings(document.getElementById('op-month').value, document.getElementById('op-year').value);
}

function opUpdateSummary() {
  var transfers = opNewRows.concat(opClosedRows).filter(function(r) { return r._kind === 'transfer'; }).length;
  var wrap = document.getElementById('op-transfer-wrap');
  wrap.style.display = transfers ? 'flex' : 'none';
  document.getElementById('op-transfer-label').textContent = 'Include ownership changes (' + transfers + ' hidden by default — same venue, new license)';
  var cap = (opNewRows.length >= 5000 || opClosedRows.length >= 5000) ? ' · capped at 5,000' : '';
  var fail = opClassifyFailed ? ' · ownership-change check unavailable' : '';
  document.getElementById('op-summary').textContent = opVisible(opNewRows).length + ' new · ' + opVisible(opClosedRows).length + ' closed' + cap + fail;
}

function opNoteHtml(r) {
  var parts = [];
  if (r.owner) parts.push(r.owner);
  if (r._note) parts.push(r._note);
  return parts.length ? '<div class="venue-owner">' + opEsc(parts.join(' · ')) + '</div>' : '';
}

function opKindBadge(r) {
  return r._kind === 'transfer' ? '<span class="op-badge muted">OWNERSHIP CHANGE</span>' : '';
}

function opFmtDate(v) {''',
    "helpers",
)

# ── opView now respects the ownership-change toggle ────────────────────
apply(
    '''function opView(rows) {
  var f = _vtFilter.openings;
  return f === 'all' ? rows : rows.filter(function(r) { return vtRow(r, 'openings') === f; });
}''',
    '''function opView(rows) {
  var f = _vtFilter.openings;
  var vis = opVisible(rows);
  return f === 'all' ? vis : vis.filter(function(r) { return vtRow(r, 'openings') === f; });
}''',
    "opView",
)

# ── Queries + flow ──────────────────────────────────────────────────────
apply(
    "&$select=trade_name,owner,address,city,zip,original_issue_date&$where=",
    "&$select=license_id,trade_name,owner,address,city,zip,original_issue_date&$where=",
    "new select",
)
apply(
    "&$select=trade_name,owner,address,city,zip,primary_status,status_change_date&$where=",
    "&$select=license_id,trade_name,owner,address,city,zip,original_issue_date,primary_status,status_change_date&$where=",
    "closed select",
)
apply(
    '''    var opCapped = opNewRows.length >= 5000 || opClosedRows.length >= 5000;
    document.getElementById('op-summary').textContent = opNewRows.length + ' new · ' + opClosedRows.length + ' closed' + (opCapped ? ' · capped at 5,000' : '');
    renderOpenings(month, year);
    document.getElementById('op-results').style.display = 'block';
  }).catch(function(e) {''',
    '''    document.getElementById('op-summary').textContent = 'Checking for ownership changes…';
    document.getElementById('op-show-transfers').checked = false;
    return opClassify(opNewRows, opClosedRows).then(function() {
      renderOpenings(month, year);
      document.getElementById('op-results').style.display = 'block';
    });
  }).catch(function(e) {''',
    "runOpenings flow",
)
apply(
    '''  opNewRows = []; opClosedRows = []; _vtFilter.openings = 'all';''',
    '''  opNewRows = []; opClosedRows = []; _vtFilter.openings = 'all';
  document.getElementById('op-show-transfers').checked = false;
  document.getElementById('op-transfer-wrap').style.display = 'none';''',
    "clearOpenings",
)

# ── Rendering ───────────────────────────────────────────────────────────
apply(
    '''  vtRenderChips('openings', opNewRows.concat(opClosedRows));''',
    '''  opUpdateSummary();
  vtRenderChips('openings', opVisible(opNewRows).concat(opVisible(opClosedRows)));''',
    "render head",
)
apply(
    '''      var badge = (age !== null && age <= 30) ? '<span class="op-badge">NEW</span>' : '';''',
    '''      var badge = r._kind === 'transfer' ? opKindBadge(r) : ((age !== null && age <= 30) ? '<span class="op-badge">NEW</span>' : '');''',
    "new badge",
)
apply(
    '''        + (r.owner ? '<div class="venue-owner">' + opEsc(r.owner) + '</div>' : '')''',
    '''        + opNoteHtml(r)''',
    "note lines",
    count=2,
)
apply(
    '''opEsc(r.trade_name || '—') + vtTag(vtRow(r, 'openings')) + '</div>\'''',
    '''opEsc(r.trade_name || '—') + vtTag(vtRow(r, 'openings')) + opKindBadge(r) + '</div>\'''',
    "closed badge",
)
apply(
    '''      if (r) openHistory(r.trade_name||'', r.owner||'', '', r.city||'', (r.zip||'').slice(0,5), r.address||'');''',
    '''      if (r) openHistory(r.trade_name||'', r._histOwner || r.owner||'', '', r.city||'', (r.zip||'').slice(0,5), r.address||'');''',
    "wire history owner",
)

# ── CSV Note column ─────────────────────────────────────────────────────
apply("? ['Location','City','Address','ZIP','Issue Date','Owner','Type']", "? ['Location','City','Address','ZIP','Issue Date','Owner','Type','Note']", "csv hdr new")
apply(": ['Location','City','Address','ZIP','Status','Status Change Date','Owner','Type'];", ": ['Location','City','Address','ZIP','Status','Status Change Date','Owner','Type','Note'];", "csv hdr closed")
apply("r.owner||'', vtLabel(vtRow(r,'openings'))]);", "r.owner||'', vtLabel(vtRow(r,'openings')), r._note||'']);", "csv rows", count=2)

# ── History modal fallback: venue name + address when taxpayer has none ─
apply(
    '''  fetch(url)
    .then(function(res){return res.json();})
    .then(function(data){
      if(!data.length){document.getElementById('modal-body').innerHTML='<div class="modal-loading">No history found.</div>';return;}''',
    '''  fetch(url)
    .then(function(res){return res.json();})
    .then(function(data){
      if (data.length || !locationName || !locationZip) return data;
      // Ownership changes get a new taxpayer name (new LLC) but keep the venue, so fall back to
      // venue name + ZIP (+ address when known) to find the history filed under the previous owner.
      var w2="upper(location_name)='"+locationName.toUpperCase().replace(/'/g,"''")+"' AND starts_with(location_zip,'"+String(locationZip).slice(0,5).replace(/'/g,"''")+"')";
      if (locationAddress) w2+=" AND upper(location_address)='"+locationAddress.toUpperCase().replace(/\\s+/g,' ').trim().replace(/'/g,"''")+"'";
      var url2=API+'?$limit=5000&$order=obligation_end_date_yyyymmdd+DESC&$select=obligation_end_date_yyyymmdd,total_receipts,liquor_receipts,wine_receipts,beer_receipts,responsibility_begin_date_yyyymmdd&$where='+encodeURIComponent(w2);
      return fetch(url2).then(function(res){return res.json();});
    })
    .then(function(data){
      if(!data.length){document.getElementById('modal-body').innerHTML='<div class="modal-loading">No history found.</div>';return;}''',
    "modal fallback",
)

if crlf:
    html = html.replace("\n", "\r\n")
with open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print(f"Patched {changed} location(s) in {PATH}")
