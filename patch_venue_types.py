#!/usr/bin/env python3
"""
Venue type tags + filter chips on every tab (Explorer, Nearby, Openings) and
in the history modal header.

Types: Restaurant / Bar, Hotel, Stadium, Entertainment.

TABC has no venue-type field, so the type is a NAME-KEYWORD HEURISTIC
(vtGetType): stadium keywords first, then hotel, then entertainment, and
anything that matches none of them is Restaurant / Bar (MB permits are
overwhelmingly restaurants and bars). It will occasionally mislabel a
venue (e.g. a restaurant with "Inn" in its name) - tune VT_* regexes.

Chips filter client-side on rows that are already loaded (no re-query), show
live counts, and the filter resets on each new query. CSV exports honour the
active filter and gain a Type column.

Run from the repo root: python patch_venue_types.py
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
    '''.sort-pill:hover:not(.active) { border-color:var(--accent); color:var(--accent); }''',
    '''.sort-pill:hover:not(.active) { border-color:var(--accent); color:var(--accent); }
.type-chips { display:flex; gap:6px; flex-wrap:wrap; margin-bottom:10px; }
.type-chips .sort-pill { height:28px; padding:0 11px; }
.type-chips .sort-pill.vt-zero { opacity:0.45; }
.vtag { display:inline-block; margin-left:8px; padding:1px 8px; border-radius:10px; border:1px solid; font-family:var(--mono); font-size:9px; font-weight:600; letter-spacing:0.05em; text-transform:uppercase; vertical-align:middle; white-space:nowrap; }
.vt-restaurant { color:#2d5a2d; border-color:rgba(45,90,45,0.35); background:rgba(45,90,45,0.08); }
.vt-hotel { color:#2f5d8a; border-color:rgba(47,93,138,0.35); background:rgba(47,93,138,0.08); }
.vt-stadium { color:#8f6210; border-color:rgba(143,98,16,0.38); background:rgba(143,98,16,0.09); }
.vt-entertainment { color:#7a3f8f; border-color:rgba(122,63,143,0.35); background:rgba(122,63,143,0.08); }
.vt-line .vtag { margin-left:0; margin-top:3px; }''',
    "css",
)

# ── Markup: chip containers ─────────────────────────────────────────────
apply(
    '''    <div id="results">
      <div class="tbl-hdr">
        <span class="tbl-hint">Tap any row for history</span>''',
    '''    <div id="results">
      <div id="tc-explorer" class="type-chips" style="display:none;"></div>
      <div class="tbl-hdr">
        <span class="tbl-hint">Tap any row for history</span>''',
    "explorer chips markup",
)
apply(
    '''    <div id="sort-row-wrap" style="display:none;" class="sort-row">''',
    '''    <div id="tc-nearby" class="type-chips" style="display:none;"></div>
    <div id="sort-row-wrap" style="display:none;" class="sort-row">''',
    "nearby chips markup",
)
apply(
    '''    <div id="op-results" style="display:none;">
      <div class="tbl-hdr">
        <span class="tbl-hint" id="op-new-hint">''',
    '''    <div id="op-results" style="display:none;">
      <div id="tc-openings" class="type-chips" style="display:none;"></div>
      <div class="tbl-hdr">
        <span class="tbl-hint" id="op-new-hint">''',
    "openings chips markup",
)

# ── Shared venue-type JS (inserted before the Openings section) ─────────
apply(
    '''// ---- Openings tracker ----''',
    r'''// ---- Venue types (name-keyword heuristic; TABC has no venue-type field) ----
var VTYPES = [
  {id:'restaurant', label:'Restaurant / Bar'},
  {id:'hotel', label:'Hotel'},
  {id:'stadium', label:'Stadium'},
  {id:'entertainment', label:'Entertainment'}
];
var VT_STADIUM = /\b(STADIUM|ARENA|BALLPARK|BALL PARK|COLISEUM|SPEEDWAY|RACEWAY|RACETRACK|RACE TRACK|AT&T STADIUM|GLOBE LIFE|MINUTE MAID PARK|KYLE FIELD|DELL DIAMOND|TOYOTA CENTER|AMERICAN AIRLINES CENTER|FROST BANK CENTER|MOODY CENTER|CIRCUIT OF THE AMERICAS)\b|\bFIELD$/;
var VT_HOTEL = /\b(HOTEL|HOTELS|MOTEL|INN|INNS|SUITES|RESORT|RESORTS|LODGING|HILTON|MARRIOTT|HYATT|SHERATON|WESTIN|OMNI|WYNDHAM|DOUBLETREE|RITZ CARLTON|FOUR SEASONS|KIMPTON|INTERCONTINENTAL|CROWNE PLAZA|BEST WESTERN|LA QUINTA|DRURY|HAWTHORN|STAYBRIDGE|CANDLEWOOD)\b/;
var VT_HOTEL_OWNER = /\b(HOTEL|HOTELS|RESORT|RESORTS|INN|HILTON|MARRIOTT|HYATT)\b/;
var VT_ENTERTAINMENT = /\b(THEATER|THEATRE|THEATRES|CINEMA|CINEMAS|DRAFTHOUSE|MOVIE|MOVIES|AMC|CINEMARK|REGAL|BOWLING|LANES|TOPGOLF|GOLF|COUNTRY CLUB|CASINO|ARCADE|DAVE & BUSTERS|DAVE AND BUSTERS|MAIN EVENT|MUSEUM|ZOO|AQUARIUM|AMPHITHEATER|AMPHITHEATRE|CONCERT|MUSIC HALL|COMEDY|CONVENTION CENTER|CIVIC CENTER|FAIRGROUNDS|SKATING|TRAMPOLINE|KARTING|GO KARTS|ESCAPE ROOM|PLAYHOUSE|AUDITORIUM|THEME PARK|WATER PARK|SIX FLAGS|EVENT CENTER|EVENT VENUE|WEDDING VENUE|ENTERTAINMENT|BILLIARDS|POOL HALL|LIVE MUSIC|DANCE HALL|HONKY TONK)\b/;
var _vtFilter = {explorer:'all', nearby:'all', openings:'all'};

function vtNorm(s) { return String(s || '').toUpperCase().replace(/[^A-Z0-9& ]+/g, ' ').replace(/\s+/g, ' ').trim(); }

function vtGetType(name, owner) {
  var n = vtNorm(name).replace(/\bPIZZA INN\b/g, 'PIZZA'), o = vtNorm(owner);  // "Pizza Inn" is not a hotel
  if (VT_STADIUM.test(n)) return 'stadium';
  if (VT_HOTEL.test(n) || VT_HOTEL_OWNER.test(o)) return 'hotel';
  if (VT_ENTERTAINMENT.test(n)) return 'entertainment';
  return 'restaurant';
}

function vtRow(r, scope) {
  if (r._vt) return r._vt;
  r._vt = scope === 'openings' ? vtGetType(r.trade_name, r.owner) : vtGetType(r.location_name, r.taxpayer_name);
  return r._vt;
}

function vtLabel(id) {
  for (var i = 0; i < VTYPES.length; i++) if (VTYPES[i].id === id) return VTYPES[i].label;
  return id;
}

function vtTag(id) { return '<span class="vtag vt-' + id + '">' + vtLabel(id) + '</span>'; }

function vtRenderChips(scope, rows) {
  var el = document.getElementById('tc-' + scope);
  if (!el) return;
  if (!rows || !rows.length) { el.style.display = 'none'; el.innerHTML = ''; return; }
  var counts = {all: rows.length};
  VTYPES.forEach(function(t) { counts[t.id] = 0; });
  rows.forEach(function(x) { counts[vtRow(scope === 'nearby' ? x.record : x, scope)]++; });
  var cur = _vtFilter[scope];
  var chip = function(id, label) {
    return '<button class="sort-pill' + (cur === id ? ' active' : '') + (counts[id] === 0 ? ' vt-zero' : '') + '" onclick="vtSetFilter(\'' + scope + '\',\'' + id + '\')">'
      + label + ' <span style="opacity:0.7">' + counts[id].toLocaleString() + '</span></button>';
  };
  el.innerHTML = chip('all', 'All') + VTYPES.map(function(t) { return chip(t.id, t.label); }).join('');
  el.style.display = 'flex';
}

function vtSetFilter(scope, id) {
  _vtFilter[scope] = id;
  if (scope === 'explorer') {
    page = 1;
    var v = explorerRows();
    setMetrics(v);
    renderTable();
    if (v.length) buildCitySummary(v, pyMap);
  } else if (scope === 'nearby') {
    renderNearbyCards(_nearbyGeocoded, _currentRadius);
  } else if (scope === 'openings') {
    renderOpenings(document.getElementById('op-month').value, document.getElementById('op-year').value);
  }
}

function explorerRows() {
  var f = _vtFilter.explorer;
  return f === 'all' ? allRows : allRows.filter(function(r) { return vtRow(r, 'explorer') === f; });
}

function opView(rows) {
  var f = _vtFilter.openings;
  return f === 'all' ? rows : rows.filter(function(r) { return vtRow(r, 'openings') === f; });
}

// ---- Openings tracker ----''',
    "shared venue-type js",
)

# ── Explorer ────────────────────────────────────────────────────────────
apply(
    '''      allRows = cyData; sortKey = 'total_receipts'; sortDir = 'desc'; page = 1;''',
    '''      allRows = cyData; sortKey = 'total_receipts'; sortDir = 'desc'; page = 1; _vtFilter.explorer = 'all';''',
    "explorer filter reset on query",
)
apply(
    '''  var start=(page-1)*PER, slice=allRows.slice(start,start+PER);''',
    '''  var rowsV=explorerRows(); vtRenderChips('explorer', allRows);
  var start=(page-1)*PER, slice=rowsV.slice(start,start+PER);''',
    "renderTable slice",
)
apply(
    '''        '<div class="venue-name">'+(r.location_name||'—')+'</div>'+''',
    '''        '<div class="venue-name">'+(r.location_name||'—')+vtTag(vtRow(r,'explorer'))+'</div>'+''',
    "explorer mobile card tag",
)
apply(
    '''        '<td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;font-weight:500">'+(r.location_name||'—')+'</td>'+
        '<td>'+city+'</td>'+''',
    '''        '<td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;font-weight:500">'+(r.location_name||'—')+'<div class="vt-line">'+vtTag(vtRow(r,'explorer'))+'</div></td>'+
        '<td>'+city+'</td>'+''',
    "explorer table cell tag",
)
apply(
    '''  var total=allRows.length,tp=Math.ceil(total/PER)||1;''',
    '''  if(!slice.length){
    var emptyMsg='No venues of this type in these results.';
    if(isMobile && cardList) cardList.innerHTML='<div class="op-empty">'+emptyMsg+'</div>';
    else tbody.innerHTML='<tr><td colspan="6" class="dim">'+emptyMsg+'</td></tr>';
  }
  var total=rowsV.length,tp=Math.ceil(total/PER)||1;''',
    "renderTable total + empty",
)
apply(
    '''(start+1)+'–'+Math.min(start+PER,total)''',
    '''(total?start+1:0)+'–'+Math.min(start+PER,total)''',
    "page-range zero",
)
apply(
    '''  allRows=[];pyMap={};page=1;selectedMonth='';selectedYear='';''',
    '''  allRows=[];pyMap={};page=1;selectedMonth='';selectedYear='';_vtFilter.explorer='all';''',
    "clearAll reset",
)
apply(
    '''  allRows.forEach(function(r) {
    var c = r.location_city||'UNKNOWN';
    if (r._py_total !== null && r._py_total !== undefined) {''',
    '''  cyData.forEach(function(r) {
    var c = r.location_city||'UNKNOWN';
    if (r._py_total !== null && r._py_total !== undefined) {''',
    "city summary PY uses passed rows",
)
apply(
    '''  var headers = ['Location','City','Address','ZIP','Period','CY Total','PY Total','$ Variance','% Variance'];
  var rows = [headers];
  allRows.forEach(function(r) {''',
    '''  var headers = ['Location','City','Address','ZIP','Period','CY Total','PY Total','$ Variance','% Variance','Type'];
  var rows = [headers];
  explorerRows().forEach(function(r) {''',
    "explorer csv rows + header",
)
apply(
    '''fmtDate(r.obligation_end_date_yyyymmdd),Math.round(cyVal),pyVal!==''?Math.round(pyVal):'',varAmt,varPct]);''',
    '''fmtDate(r.obligation_end_date_yyyymmdd),Math.round(cyVal),pyVal!==''?Math.round(pyVal):'',varAmt,varPct,vtLabel(vtRow(r,'explorer'))]);''',
    "explorer csv type col",
)

# ── Nearby ──────────────────────────────────────────────────────────────
apply(
    '''  var filtered=geocoded.filter(function(v){return v.dist<=maxMi;});''',
    '''  var inRadius=geocoded.filter(function(v){return v.dist<=maxMi;});
  vtRenderChips('nearby', inRadius);
  var filtered=_vtFilter.nearby==='all' ? inRadius : inRadius.filter(function(v){return vtRow(v.record,'nearby')===_vtFilter.nearby;});''',
    "nearby type filter",
)
apply(
    '''    status.textContent='No venues within '+maxMi+' mi — try a larger radius.';''',
    '''    status.textContent=inRadius.length ? 'No '+vtLabel(_vtFilter.nearby)+' venues within '+maxMi+' mi.' : 'No venues within '+maxMi+' mi — try a larger radius.';''',
    "nearby empty message",
)
apply(
    '''      +'<div class="venue-name">'+(r.location_name||'')+'</div>\'''',
    '''      +'<div class="venue-name">'+(r.location_name||'')+vtTag(vtRow(r,'nearby'))+'</div>\'''',
    "nearby card tag",
)

# ── Modal header ────────────────────────────────────────────────────────
apply(
    '''  document.getElementById('modal-title').textContent=locationName;''',
    '''  document.getElementById('modal-title').textContent=locationName;
  document.getElementById('modal-title').insertAdjacentHTML('beforeend', vtTag(vtGetType(locationName, taxpayerName)));''',
    "modal tag",
)

# ── Openings ────────────────────────────────────────────────────────────
apply(
    '''    opNewRows = results[0];''',
    '''    _vtFilter.openings = 'all';
    opNewRows = results[0];''',
    "openings filter reset",
)
apply(
    '''  opNewRows = []; opClosedRows = [];
  document.getElementById('op-results').style.display = 'none';''',
    '''  opNewRows = []; opClosedRows = []; _vtFilter.openings = 'all';
  document.getElementById('op-results').style.display = 'none';''',
    "clearOpenings filter reset",
)
apply(
    '''  var newBox = document.getElementById('op-new-cards');
  if (!opNewRows.length) {''',
    '''  vtRenderChips('openings', opNewRows.concat(opClosedRows));
  var opNewV = opView(opNewRows), opClosedV = opView(opClosedRows);
  var typeSfx = _vtFilter.openings === 'all' ? '' : ' (' + vtLabel(_vtFilter.openings) + ')';
  var newBox = document.getElementById('op-new-cards');
  if (!opNewV.length) {''',
    "openings render head",
)
apply(
    '''No new MB permits issued in ' + opEsc(periodLabel + filterSuffix) + '.''',
    '''No new MB permits issued in ' + opEsc(periodLabel + filterSuffix + typeSfx) + '.''',
    "openings new empty msg",
)
apply("newBox.innerHTML = opNewRows.map(function(r, i) {", "newBox.innerHTML = opNewV.map(function(r, i) {", "new map")
apply("wireOpCards('op-new-cards', opNewRows);", "wireOpCards('op-new-cards', opNewV);", "new wire")
apply(
    '''+ opEsc(r.trade_name || '—') + badge + '</div>\'''',
    '''+ opEsc(r.trade_name || '—') + vtTag(vtRow(r, 'openings')) + badge + '</div>\'''',
    "openings new tag",
)
apply("  if (!opClosedRows.length) {", "  if (!opClosedV.length) {", "closed empty check")
apply(
    '''No closures in ' + opEsc(periodLabel + filterSuffix) + '.''',
    '''No closures in ' + opEsc(periodLabel + filterSuffix + typeSfx) + '.''',
    "openings closed empty msg",
)
apply("closedBox.innerHTML = opClosedRows.map(function(r, i) {", "closedBox.innerHTML = opClosedV.map(function(r, i) {", "closed map")
apply("wireOpCards('op-closed-cards', opClosedRows);", "wireOpCards('op-closed-cards', opClosedV);", "closed wire")
apply(
    '''+ opEsc(r.trade_name || '—') + '</div>\'''',
    '''+ opEsc(r.trade_name || '—') + vtTag(vtRow(r, 'openings')) + '</div>\'''',
    "openings closed tag",
)
apply(
    '''  var rows = section === 'new' ? opNewRows : opClosedRows;''',
    '''  var rows = opView(section === 'new' ? opNewRows : opClosedRows);''',
    "openings csv rows",
)
apply("? ['Location','City','Address','ZIP','Issue Date','Owner']", "? ['Location','City','Address','ZIP','Issue Date','Owner','Type']", "csv hdr new")
apply(
    ": ['Location','City','Address','ZIP','Status','Status Change Date','Owner'];",
    ": ['Location','City','Address','ZIP','Status','Status Change Date','Owner','Type'];",
    "csv hdr closed",
)
apply(
    "opFmtDate(r.original_issue_date), r.owner||'']);",
    "opFmtDate(r.original_issue_date), r.owner||'', vtLabel(vtRow(r,'openings'))]);",
    "csv row new",
)
apply(
    "r.primary_status||'', opFmtDate(r.status_change_date), r.owner||'']);",
    "r.primary_status||'', opFmtDate(r.status_change_date), r.owner||'', vtLabel(vtRow(r,'openings'))]);",
    "csv row closed",
)

if crlf:
    html = html.replace("\n", "\r\n")
with open(PATH, "w", encoding="utf-8", newline="") as f:
    f.write(html)
print(f"Patched {changed} location(s) in {PATH}")
