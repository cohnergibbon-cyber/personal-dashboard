import re, sys

path = r'C:\Users\CohnerGibbons\personal-dashboard\static\texas_alcohol_explorer.html'

with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

print('File size before:', len(c))
changes = 0

# ── 1. Fix Next/Prev buttons with direct onclick
m = re.search(r'<button[^>]*id="btn-next"[^>]*>', c)
if m:
    old = m.group()
    if 'onclick' not in old:
        new = old.replace('id="btn-next"', 'id="btn-next" onclick="if(allRows.length&&page<Math.ceil(allRows.length/PER)){page++;renderTable();}"')
        c = c.replace(old, new); print('1. btn-next: added'); changes += 1
    else:
        print('1. btn-next: already has onclick')

m2 = re.search(r'<button[^>]*id="btn-prev"[^>]*>', c)
if m2:
    old2 = m2.group()
    if 'onclick' not in old2:
        new2 = old2.replace('id="btn-prev"', 'id="btn-prev" onclick="if(page>1){page--;renderTable();}"')
        c = c.replace(old2, new2); print('2. btn-prev: added'); changes += 1
    else:
        print('2. btn-prev: already has onclick')

# ── 2. Add address input if missing
if 'addr-input' not in c:
    addr_css = """
.or-divider{display:flex;align-items:center;gap:10px;margin:12px 0;}
.or-divider::before,.or-divider::after{content:'';flex:1;height:1px;background:var(--border2);}
.or-divider span{font-size:11px;font-family:var(--mono);color:var(--text3);text-transform:uppercase;letter-spacing:0.06em;}
.addr-row{display:flex;gap:8px;margin-bottom:4px;}
.addr-input{flex:1;height:40px;padding:0 12px;border:1.5px solid var(--border2);border-radius:var(--r-sm);background:var(--s1);color:var(--text);font-size:13px;font-family:var(--font);outline:none;transition:border-color 0.15s;}
.addr-input:focus{border-color:var(--accent);}
.addr-input::placeholder{color:var(--text3);}
.addr-btn{height:40px;padding:0 16px;background:var(--s2);border:1.5px solid var(--border2);border-radius:var(--r-sm);color:var(--text2);font-size:12px;font-family:var(--mono);font-weight:600;cursor:pointer;transition:all 0.15s;}
.addr-btn:hover{border-color:var(--accent);color:var(--accent);}
"""
    c = c.replace('</style>', addr_css + '</style>', 1)

    # Find the loc-btn closing tag and insert after it
    loc_end = c.find('</button>', c.find('id="loc-btn"'))
    if loc_end < 0:
        loc_end = c.find('</button>', c.find('class="loc-btn"'))
    if loc_end >= 0:
        insert_pos = loc_end + len('</button>')
        addr_html = """
      <div class="or-divider"><span>or</span></div>
      <div class="addr-row">
        <input type="text" id="addr-input" class="addr-input" placeholder="Enter address, city, or ZIP"
               onkeydown="if(event.key==='Enter')findNearbyByAddress()">
        <button class="addr-btn" onclick="findNearbyByAddress()">Search</button>
      </div>"""
        c = c[:insert_pos] + addr_html + c[insert_pos:]
        print('3. Address input HTML: added'); changes += 1
    else:
        print('3. Address input: loc-btn not found')
else:
    print('3. Address input: already present')

# ── 3. Replace entire findNearby + runNearbySearch block with clean version
# Find findNearby start
fn_start = c.find('function findNearby(){')
# Find end of runNearbySearch (last function before Tab switching)
tab_start = c.find('// Tab switching')
if tab_start < 0:
    tab_start = c.find('function switchTab')

if fn_start >= 0 and tab_start > fn_start:
    print(f'4. Replacing nearby JS block: {fn_start}-{tab_start}')

    new_nearby_js = """function findNearbyByAddress() {
  var query = (document.getElementById('addr-input').value || '').trim();
  if (!query) return;
  var status = document.getElementById('map-status');
  var results = document.getElementById('map-results');
  _nearbyGeocoded = [];
  status.style.display = 'block';
  status.textContent = 'Geocoding address\u2026';
  results.innerHTML = '';
  var q = encodeURIComponent(query + ', Texas, USA');
  fetch('https://nominatim.openstreetmap.org/search?q=' + q + '&format=json&limit=1&countrycodes=us',
    { headers: { 'Accept-Language': 'en' } })
  .then(function(r) { return r.json(); })
  .then(function(data) {
    if (!data || !data.length) { status.textContent = 'Address not found.'; return; }
    var lat = parseFloat(data[0].lat), lng = parseFloat(data[0].lon);
    status.textContent = 'Searching near ' + data[0].display_name.split(',').slice(0,2).join(',') + '\u2026';
    runNearbySearch(lat, lng);
  })
  .catch(function(e) { status.textContent = 'Error: ' + e.message; });
}

function findNearby(){
  var status=document.getElementById('map-status');
  var results=document.getElementById('map-results');
  _nearbyGeocoded=[];
  status.style.display='block';
  status.textContent='Getting your location\u2026';
  results.innerHTML='';
  if(!navigator.geolocation){status.textContent='Location not supported.';return;}
  navigator.geolocation.getCurrentPosition(function(pos){
    runNearbySearch(pos.coords.latitude, pos.coords.longitude);
  },function(err){
    var msgs={1:'Location access denied.',2:'Position unavailable.',3:'Timed out.'};
    status.textContent=msgs[err.code]||'Location error.';
  },{timeout:15000,enableHighAccuracy:true});
}

function runNearbySearch(userLat, userLng){
  var status=document.getElementById('map-status');
  var radiusMi=_currentRadius||1;
  status.textContent='Loading venue coordinates\u2026';

  fetch('/tx_venues_geo.json')
  .then(function(r){
    if(!r.ok) throw new Error('tx_venues_geo.json not found');
    return r.json();
  })
  .then(function(geoLookup){
    status.textContent='Scanning addresses within '+radiusMi+' mi\u2026';

    // Scan entire geo lookup — no city filter
    var nearbyCoords={};
    Object.keys(geoLookup).forEach(function(key){
      var coord=geoLookup[key];
      var dist=haverDist(userLat,userLng,coord[0],coord[1]);
      if(dist<=5) nearbyCoords[key]={lat:coord[0],lng:coord[1],dist:dist};
    });

    var nearCount=Object.keys(nearbyCoords).length;
    if(!nearCount){status.textContent='No geocoded venues within 5 miles.';return;}
    status.textContent='Found '+nearCount+' addresses, fetching sales\u2026';

    // Period dates
    var _d=new Date(); _d.setMonth(_d.getMonth()-2);
    var month=String(_d.getMonth()+1).padStart(2,'0');
    var year=String(_d.getFullYear());
    var nm=parseInt(month)===12?1:parseInt(month)+1;
    var ny=parseInt(month)===12?parseInt(year)+1:parseInt(year);
    var pad=nm<10?'0'+nm:String(nm);
    var dateWhere=[
      "obligation_end_date_yyyymmdd>='"+year+'-'+month+"-01T00:00:00.000'",
      "obligation_end_date_yyyymmdd<'"+ny+'-'+pad+"-01T00:00:00.000'"
    ];

    // Build address filters from geo keys (ADDR|CITY|ZIP)
    var addrFilters=[], seen={};
    Object.keys(nearbyCoords).forEach(function(key){
      var parts=key.split('|');
      var addr=parts[0], zip=(parts[2]||'').slice(0,5);
      var uk=addr+'|'+zip;
      if(!seen[uk]){
        seen[uk]=true;
        var safe=addr.replace(/'/g,"''");
        addrFilters.push(zip?"(upper(location_address)='"+safe+"' AND location_zip='"+zip+"')"
                           :"upper(location_address)='"+safe+"'");
      }
    });

    // Batch fetch (50 addresses per request to stay under URL limits)
    var BATCH=50, allVenues=[], batches=[];
    for(var i=0;i<addrFilters.length;i+=BATCH) batches.push(addrFilters.slice(i,i+BATCH));

    function fetchBatch(idx){
      if(idx>=batches.length){finalize(allVenues);return;}
      var where=['('+batches[idx].join(' OR ')+')'].concat(dateWhere);
      var url='https://data.texas.gov/resource/naix-2893.json?$limit=500&$select=location_name,location_address,location_city,location_zip,total_receipts,obligation_end_date_yyyymmdd,taxpayer_name&$where='+encodeURIComponent(where.join(' AND '));
      fetch(url).then(function(r){return r.json();}).then(function(v){
        if(v&&v.length) allVenues=allVenues.concat(v);
        status.textContent='Loading ('+(idx+1)+'/'+batches.length+' batches, '+allVenues.length+' found)\u2026';
        fetchBatch(idx+1);
      }).catch(function(){fetchBatch(idx+1);});
    }

    function finalize(venues){
      if(!venues.length){status.textContent='No sales data found for nearby venues.';return;}
      var geocoded=[];
      venues.forEach(function(v){
        var key=addrKey(v.location_address||'',v.location_city||'',v.location_zip||'');
        var geo=nearbyCoords[key];
        if(geo) geocoded.push({record:v,lat:geo.lat,lng:geo.lng,dist:geo.dist});
      });

      // PY fetch (first batch only for speed)
      var pyM=parseInt(month)===1?12:parseInt(month)-1;
      var pyY=parseInt(month)===1?parseInt(year)-1:parseInt(year);
      var pyMs=String(pyM).padStart(2,'0'), pyYs=String(pyY);
      var pyNm=pyM===12?1:pyM+1, pyNy=pyM===12?pyY+1:pyY;
      var pyPad=pyNm<10?'0'+pyNm:String(pyNm);
      var pyWhere=['('+addrFilters.slice(0,50).join(' OR ')+')',
        "obligation_end_date_yyyymmdd>='"+pyYs+'-'+pyMs+"-01T00:00:00.000'",
        "obligation_end_date_yyyymmdd<'"+pyNy+'-'+pyPad+"-01T00:00:00.000'"
      ];
      fetch('https://data.texas.gov/resource/naix-2893.json?$limit=500&$select=location_name,location_address,location_zip,total_receipts&$where='+encodeURIComponent(pyWhere.join(' AND ')))
      .then(function(r){return r.json();})
      .then(function(py){
        var pyMap={};
        (py||[]).forEach(function(p){pyMap[(p.location_name||'')+'|'+(p.location_zip||'')]=parseFloat(p.total_receipts)||0;});
        geocoded.forEach(function(v){
          var k=(v.record.location_name||'')+'|'+(v.record.location_zip||'');
          if(pyMap[k]!==undefined) v.record._py_total=pyMap[k];
        });
        _nearbyGeocoded=geocoded;
        renderNearbyCards(geocoded,radiusMi);
      }).catch(function(){_nearbyGeocoded=geocoded;renderNearbyCards(geocoded,radiusMi);});
    }

    fetchBatch(0);
  })
  .catch(function(e){status.textContent='Error: '+e.message;});
}

"""
    c = c[:fn_start] + new_nearby_js + c[tab_start:]
    print('4. Nearby JS block: replaced'); changes += 1
else:
    print('4. Could not find nearby JS boundaries')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

print('File size after:', len(c))
print('Changes made:', changes)
print('Done.')
