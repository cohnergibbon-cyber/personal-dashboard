#!/usr/bin/env python3
"""
History + Openings: recognise venues that are really older than their mixed-beverage (MB) permit.

Case that prompted this: UCHI DALLAS shows "opened Feb 2026" because the receipts data only covers MB
(mixed beverage) permits. The venue held a beer & wine (BG) license at the same address since 2014 and
just ADDED an MB license. Nothing was renewed - the older license simply isn't in the receipts data.

1. History popup
   - "Operating since ..." line from the license registry when the venue held an older license here.
   - If a previous owner filed MB receipts for the same venue name at the same street address, those
     earlier periods are joined to the new owner's history (only periods BEFORE the new owner's first one,
     so nothing is double counted).
   - The history fallback now matches the street address ignoring the suite wording (STE vs SUITE).
2. Openings
   - License matching ignores suite wording (STE 110 == SUITE 110) and uses street + suite compatibility.
   - A new MB license whose venue previously held a non-MB license is treated as an existing venue
     ("ADDED MB LICENSE"), hidden by default together with ownership changes.

Run from the repo root: python patch_history_lump.py
"""
import sys

PATH = "static/texas_alcohol_explorer.html"
with open(PATH, "r", encoding="utf-8", newline="") as f:
    html = f.read()
crlf = "\r\n" in html
html = html.replace("\r\n", "\n")
changed = 0


def apply(old, new, label):
    global html, changed
    n = html.count(old)
    if n != 1:
        sys.exit(f"ABORT: expected 1 occurrence of [{label}], found {n}. No changes written.")
    html = html.replace(old, new)
    changed += 1


# ── 1. markup: a line under "Permit issued" ────────────────────────────────
apply(
    '<div class="modal-permit" id="modal-permit"></div>',
    '<div class="modal-permit" id="modal-permit"></div>\n'
    '    <div class="modal-permit" id="modal-since" style="margin-top:-8px;line-height:1.5;"></div>',
    "modal markup",
)

# ── 2. modal helpers + sequence guard ──────────────────────────────────────
apply(
    "// ---- Modal ----\nfunction openHistory(locationName, taxpayerName, rowPeriod, locationCity, locationZip, locationAddress) {\n"
    "  document.getElementById('modal-overlay').classList.add('open');\n",
    r"""// ---- Modal ----
var modalSeq = 0, modalSinceNote = '', modalStitchNote = '';

function opPaintSince(seq) {
  if (seq !== modalSeq) return;
  var el = document.getElementById('modal-since');
  if (!el) return;
  el.innerHTML = [modalSinceNote, modalStitchNote].filter(Boolean).map(opEsc).join('<br>');
}

// "Operating since": the venue's oldest license at this address (any type) vs. its first MB permit.
function opLoadSince(seq, name, owner, zip, addr) {
  if (!addr || !zip) return;
  var street = opStreetKey(addr);
  if (!street) return;
  var url = LICENSE_API + '?$limit=300&$select=license_id,license_type,trade_name,owner,address,zip,original_issue_date,primary_status&$where='
    + encodeURIComponent("upper(address) like '" + street.replace(/'/g, "''") + "%' AND starts_with(zip,'" + String(zip).slice(0, 5).replace(/'/g, "''") + "')");
  fetch(url).then(function(r) { return r.ok ? r.json() : []; }).then(function(rows) {
    if (seq !== modalSeq) return;
    var mine = rows.filter(function(o) {
      return opStreetKey(o.address) === street && o.original_issue_date
        && (opSameName(o.trade_name, name) || (opSuiteOk(o.address, addr) && opSameOwner(o.owner, owner)));
    });
    var mb = mine.filter(function(o) { return o.license_type === 'MB'; });
    if (!mb.length) return;
    var asc = function(x, y) { return x.original_issue_date < y.original_issue_date ? -1 : 1; };
    mine.sort(asc); mb.sort(asc);
    var first = mine[0], firstMb = mb[0];
    var gapDays = (Date.parse(String(firstMb.original_issue_date).slice(0, 10)) - Date.parse(String(first.original_issue_date).slice(0, 10))) / 864e5;
    if (!(gapDays > 60)) return;
    modalSinceNote = 'Operating since ' + opFmtDate(first.original_issue_date) + ' (first license here: ' + opTypeLabel(first.license_type)
      + (first.owner && !opSameOwner(first.owner, owner) ? ', ' + first.owner : '') + '). '
      + 'Mixed-beverage permit issued ' + opFmtDate(firstMb.original_issue_date) + ' - liquor receipts on file start then.';
    opPaintSince(seq);
  }).catch(function() { /* optional enhancement */ });
}

// Join receipts filed under a previous owner (same venue name, same street address) ahead of this owner's first period.
function opStitchHistory(data, name, owner, zip, addr, seq) {
  modalStitchNote = '';
  if (!data.length || !name || !zip || !addr) return Promise.resolve(data);
  var street = opStreetKey(addr);
  if (!street) return Promise.resolve(data);
  var first = '';
  data.forEach(function(r) { var d = String(r.obligation_end_date_yyyymmdd).slice(0, 10); if (!first || d < first) first = d; });
  var where = "starts_with(location_zip,'" + String(zip).slice(0, 5).replace(/'/g, "''") + "')"
    + " AND upper(location_address) like '" + street.replace(/'/g, "''") + "%'"
    + " AND upper(taxpayer_name)!='" + String(owner).toUpperCase().replace(/'/g, "''") + "'"
    + " AND obligation_end_date_yyyymmdd<'" + first + "T00:00:00.000'";
  var url = API + '?$limit=5000&$order=obligation_end_date_yyyymmdd+DESC&$select=location_name,location_address,taxpayer_name,obligation_end_date_yyyymmdd,total_receipts,liquor_receipts,wine_receipts,beer_receipts,responsibility_begin_date_yyyymmdd&$where=' + encodeURIComponent(where);
  return fetch(url).then(function(r) { return r.ok ? r.json() : []; }).then(function(rows) {
    var prev = rows.filter(function(r) { return opStreetKey(r.location_address) === street && opSameName(r.location_name, name); });
    if (!prev.length) return data;
    var last = '', firstPrev = '', owners = {};
    prev.forEach(function(r) {
      var d = String(r.obligation_end_date_yyyymmdd).slice(0, 10);
      if (!last || d > last) last = d;
      if (!firstPrev || d < firstPrev) firstPrev = d;
      owners[r.taxpayer_name] = 1;
    });
    // an unrelated gap this long means a different business that happened to share a name
    if ((Date.parse(first) - Date.parse(last)) / 864e5 > 1100) return data;
    var mm = function(d) { return d.slice(5, 7) + '/' + d.slice(0, 4); };
    modalStitchNote = 'Includes ' + prev.length + ' earlier period' + (prev.length === 1 ? '' : 's') + ' (' + mm(firstPrev) + ' - ' + mm(last)
      + ') filed by the previous owner: ' + Object.keys(owners).join(', ') + '.';
    return data.concat(prev);
  }).catch(function() { return data; });
}

function openHistory(locationName, taxpayerName, rowPeriod, locationCity, locationZip, locationAddress) {
  var seq = ++modalSeq; modalSinceNote = ''; modalStitchNote = '';
  var usedFallback = false;
  var sinceEl0 = document.getElementById('modal-since'); if (sinceEl0) sinceEl0.textContent = '';
  document.getElementById('modal-overlay').classList.add('open');
""",
    "modal helpers",
)

# kick off the license lookup, flag the fallback, stitch, paint
apply(
    '  var where="upper(taxpayer_name)=\'"+taxpayerName.toUpperCase()',
    '  opLoadSince(seq, locationName, taxpayerName, locationZip, locationAddress);\n'
    '  var where="upper(taxpayer_name)=\'"+taxpayerName.toUpperCase()',
    "since kickoff",
)
apply(
    "      if (locationAddress) w2+=\" AND upper(location_address)='\"+locationAddress.toUpperCase().replace(/\\s+/g,' ').trim().replace(/'/g,\"''\")+\"'\";\n",
    "      if (locationAddress && opStreetKey(locationAddress)) w2+=\" AND upper(location_address) like '\"+opStreetKey(locationAddress).replace(/'/g,\"''\")+\"%'\";\n",
    "fallback address match",
)
apply(
    "      return fetch(url2).then(function(res){return res.json();});\n    })\n",
    "      usedFallback = true;\n      return fetch(url2).then(function(res){return res.json();});\n    })\n"
    "    .then(function(data){\n"
    "      if (usedFallback) return data;\n"
    "      return opStitchHistory(data, locationName, taxpayerName, locationZip, locationAddress, seq);\n"
    "    })\n",
    "stitch step",
)
apply(
    "      if(!data.length){document.getElementById('modal-body').innerHTML='<div class=\"modal-loading\">No history found.</div>';return;}\n",
    "      opPaintSince(seq);\n"
    "      if(!data.length){document.getElementById('modal-body').innerHTML='<div class=\"modal-loading\">No history found.</div>';return;}\n",
    "paint + empty",
)

# ── 3. Openings classification ─────────────────────────────────────────────
start = html.find("function opClassify(newRows, closedRows) {")
end = html.find("function opShowTransfers() {")
if start < 0 or end < 0 or html.count("function opClassify(newRows, closedRows) {") != 1 or end < start:
    sys.exit("ABORT: could not locate opClassify block. No changes written.")

NEW_CLASSIFY = r"""// Street address with the suite stripped ("2817 MAPLE AVE STE 110" -> "2817 MAPLE AVE"), plus the suite id.
function opStreetKey(a) {
  return String(a || '').toUpperCase().replace(/\s+/g, ' ')
    .replace(/\s+(STE|SUITE|UNIT|APT|BLDG|FLOOR|RM|ROOM|FL)\b.*$/, '')
    .replace(/\s*#.*$/, '').replace(/,.*$/, '').trim();
}
function opSuiteKey(a) {
  var s = String(a || '').toUpperCase();
  var m = /\s(?:STE|SUITE|UNIT|APT|BLDG|FLOOR|RM|ROOM|FL)\b\.?\s*#?\s*([A-Z0-9-]+)/.exec(s) || /#\s*([A-Z0-9-]+)/.exec(s);
  return m ? m[1] : '';
}
function opSuiteOk(a, b) {
  var sa = opSuiteKey(a), sb = opSuiteKey(b);
  return !sa || !sb || sa === sb;
}
function opTypeLabel(c) {
  var m = { MB: 'mixed beverage', BG: 'beer & wine retailer' };
  return m[c] || (c ? 'type ' + c : 'other');
}

function opClassify(newRows, closedRows) {
  opClassifyFailed = false;
  var seen = {}, streets = [];
  newRows.concat(closedRows).forEach(function(r) {
    var s = opStreetKey(r.address);
    if (s && !seen[s]) { seen[s] = 1; streets.push(s); }
  });
  var chunks = [];
  for (var i = 0; i < streets.length; i += 15) chunks.push(streets.slice(i, i + 15));
  return Promise.all(chunks.map(function(ch) {
    var like = ch.map(function(s) { return "upper(address) like '" + s.replace(/'/g, "''") + "%'"; });
    var url = LICENSE_API + '?$limit=5000&$select=license_id,license_type,trade_name,owner,address,zip,original_issue_date,primary_status&$where='
      + encodeURIComponent(like.join(' OR '));
    return fetch(url).then(function(r) { if (!r.ok) throw new Error('lookup ' + r.status); return r.json(); });
  })).then(function(parts) {
    var byStreet = {};
    [].concat.apply([], parts).forEach(function(o) {
      var k = opStreetKey(o.address) + '|' + String(o.zip || '').slice(0, 5);
      (byStreet[k] = byStreet[k] || []).push(o);
    });
    var nearby = function(r) {
      var k = opStreetKey(r.address) + '|' + String(r.zip || '').slice(0, 5);
      return (byStreet[k] || []).filter(function(o) { return o.license_id !== r.license_id; });
    };
    var asc = function(x, y) { return x.original_issue_date < y.original_issue_date ? -1 : 1; };

    newRows.forEach(function(r) {
      r._kind = 'new'; r._note = ''; r._histOwner = ''; r._sub = '';
      var priors = nearby(r).filter(function(o) { return o.original_issue_date && o.original_issue_date < r.original_issue_date; });
      if (!priors.length) return;
      var same = priors.filter(function(o) {
        return opSameName(o.trade_name, r.trade_name) || (opSuiteOk(o.address, r.address) && opSameOwner(o.owner, r.owner));
      });
      if (same.length) {
        same.sort(asc);
        var f = same[0];
        r._kind = 'transfer';
        if (f.license_type && f.license_type !== 'MB') {
          // Same venue, older non-MB license (e.g. beer & wine): it just ADDED a mixed-beverage license.
          r._sub = 'upgrade';
          r._note = 'Open since ' + f.original_issue_date.slice(0, 4) + ' - added a mixed-beverage license (was ' + opTypeLabel(f.license_type) + ')';
        } else {
          r._note = 'Existing venue since ' + f.original_issue_date.slice(0, 4) + ' (new license, likely ownership change)';
          r._histOwner = f.owner || '';
        }
      } else {
        // Only call it a replacement when the earlier venue is no longer active; an ACTIVE license at
        // the same street address is usually just another tenant of the same building/mall.
        var gone = priors.filter(function(o) { return opSuiteOk(o.address, r.address) && o.primary_status && o.primary_status !== 'Active'; });
        if (gone.length) {
          gone.sort(function(x, y) { return x.original_issue_date < y.original_issue_date ? 1 : -1; });
          r._kind = 'replaced';
          r._note = 'Replaces ' + (gone[0].trade_name || 'a prior venue');
        }
      }
    });

    closedRows.forEach(function(r) {
      r._kind = 'closed'; r._note = ''; r._sub = '';
      var sc = String(r.status_change_date || '').slice(0, 10);
      if (!sc) return;
      var cutoff = new Date(Date.parse(sc) - 90 * 864e5).toISOString().slice(0, 10);
      var succ = nearby(r).filter(function(o) {
        return o.original_issue_date
          && o.original_issue_date.slice(0, 10) >= cutoff
          && o.original_issue_date >= (r.original_issue_date || '')
          && opSuiteOk(o.address, r.address);
      });
      if (!succ.length) return;
      var same = succ.filter(function(o) { return opSameName(o.trade_name, r.trade_name) || opSameOwner(o.owner, r.owner); });
      if (same.length) { r._kind = 'transfer'; r._note = 'Same venue, new license' + (same[0].owner ? ' (' + same[0].owner + ')' : ''); }
      else { r._note = 'Replaced by ' + (succ[0].trade_name || 'another venue'); }
    });
    return true;
  }).catch(function() { opClassifyFailed = true; return false; });
}

"""
html = html[:start] + NEW_CLASSIFY + html[end:]
changed += 1

# ── 4. wording ─────────────────────────────────────────────────────────────
apply(
    "return r._kind === 'transfer' ? '<span class=\"op-badge muted\">OWNERSHIP CHANGE</span>' : '';",
    "return r._kind === 'transfer' ? '<span class=\"op-badge muted\">' + (r._sub === 'upgrade' ? 'ADDED MB LICENSE' : 'OWNERSHIP CHANGE') + '</span>' : '';",
    "badge",
)
apply(
    "'Include ownership changes (' + transfers + ' hidden by default — same venue, new license)'",
    "'Include existing venues (' + transfers + ' hidden by default — ownership changes and venues that just added a mixed-beverage license)'",
    "toggle label",
)

if crlf:
    html = html.replace("\n", "\r\n")
with open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print(f"Patched {changed} location(s) in {PATH}")
