import re

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
        c = c.replace(old, new)
        print('1. btn-next onclick: added'); changes += 1
    else:
        print('1. btn-next: already has onclick')

m2 = re.search(r'<button[^>]*id="btn-prev"[^>]*>', c)
if m2:
    old2 = m2.group()
    if 'onclick' not in old2:
        new2 = old2.replace('id="btn-prev"', 'id="btn-prev" onclick="if(page>1){page--;renderTable();}"')
        c = c.replace(old2, new2)
        print('2. btn-prev onclick: added'); changes += 1
    else:
        print('2. btn-prev: already has onclick')

# ── 2. Replace entire runNearbySearch function
# Find its boundaries
fn_start = c.find('function runNearbySearch(userLat, userLng){')
if fn_start < 0:
    fn_start = c.find('function runNearbySearch(userLat,userLng){')

if fn_start >= 0:
    # Find the closing brace by counting braces
    depth = 0
    fn_end = fn_start
    for i, ch in enumerate(c[fn_start:]):
        if ch == '{': depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                fn_end = fn_start + i + 1
                break

    print(f'2. runNearbySearch found: chars {fn_start}-{fn_end}')

    new_fn = """function runNearbySearch(userLat, userLng){
  var status=document.getElementById('map-status');
  var results=document.getElementById('map-results');
  status.textContent='Loading venue coordinates\u2026';

  fetch('/tx_venues_geo.json')
  .then(function(r){
    if(!r.ok) throw new Error('tx_venues_geo.json not found \u2014 run geocode_tabc.py first');
    return r.json();
  })
  .then(function(geoLookup){
    status.textContent='Scanning nearby addresses\u2026';

    // Find all geo-coded addresses within 5 miles — no city filter at all
    var nearbyCoords={};
    Object.keys(geoLookup).forEach(function(key){
      var coord=geoLookup[key];
      var dist=haverDist(userLat,userLng,coord[0],coord[1]);
      if(dist<=5) nearbyCoords[key]={lat:coord[0],lng:coord[1],dist:dist};
    });

    var nearCount=Object.keys(nearbyCoords).length;
    if(!nearCount){ status.textContent='No geocoded venues found within 5 miles.'; return; }
    status.textContent='Found '+nearCount+' nearby addresses, fetching sales data\u2026';

    // Get period dates
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

    // Extract unique addresses and zip codes from nearby keys (format: ADDR|CITY|ZIP)
    var addrFilters=[];
    var seenAddrs={};
    Object.keys(nearbyCoords).forEach(function(key){
      var parts=key.split('|');
      var addr=parts[0], zip=parts[2]||'';
      var akey=addr+'|'+zip;
      if(!seenAddrs[akey]){
        seenAddrs[akey]=true;
        var safe=addr.replace(/'/g,"''");
        if(zip) addrFilters.push("(upper(location_address)='"+safe+"' AND location_zip='"+zip+"')");
        else addrFilters.push("upper(location_address)='"+safe+"'");
      }
    });

    // TABC API has URL length limits — batch into groups of 50 addresses
    var BATCH=50;
    var batches=[];
    for(var i=0;i<addrFilters.length;i+=BATCH) batches.push(addrFilters.slice(i,i+BATCH));

    var allVenues=[];
    function fetchBatch(idx){
      if(idx>=batches.length){
        finalize(allVenues);
        return;
      }
      var where=['('+batches[idx].join(' OR ')+')'].concat(dateWhere);
      var url='https://data.texas.gov/resource/naix-2893.json?$limit=500&$select=location_name,location_address,location_city,location_zip,total_receipts,obligation_end_date_yyyymmdd,taxpayer_name&$where='+encodeURIComponent(where.join(' AND '));
      fetch(url).then(function(r){return r.json();}).then(function(venues){
        if(venues&&venues.length) allVenues=allVenues.concat(venues);
        status.textContent='Fetching batch '+(idx+1)+'/'+batches.length+' ('+allVenues.length+' so far)\u2026';
        fetchBatch(idx+1);
      }).catch(function(){ fetchBatch(idx+1); });
    }

    function finalize(venues){
      if(!venues.length){ status.textContent='No sales data found for nearby venues.'; return; }

      // Join with geo coordinates
      var geocoded=[];
      venues.forEach(function(v){
        var key=addrKey(v.location_address||'',v.location_city||'',v.location_zip||'');
        var geo=nearbyCoords[key];
        if(geo) geocoded.push({record:v,lat:geo.lat,lng:geo.lng,dist:geo.dist});
      });

      // Fetch PY data
      var pyMonth=parseInt(month)===1?12:parseInt(month)-1;
      var pyYear=parseInt(month)===1?parseInt(year)-1:parseInt(year);
      var pyM=String(pyMonth).padStart(2,'0');
      var pyY=String(pyYear);
      var pyNm=pyMonth===12?1:pyMonth+1;
      var pyNy=pyMonth===12?pyYear+1:pyYear;
      var pyPad=pyNm<10?'0'+pyNm:String(pyNm);
      var pyBatch=addrFilters.slice(0,BATCH);
      var pyWhere=['('+pyBatch.join(' OR ')+')',
        "obligation_end_date_yyyymmdd>='"+pyY+'-'+pyM+"-01T00:00:00.000'",
        "obligation_end_date_yyyymmdd<'"+pyNy+'-'+pyPad+"-01T00:00:00.000'"
      ];
      var pyUrl='https://data.texas.gov/resource/naix-2893.json?$limit=500&$select=location_name,location_address,location_zip,total_receipts&$where='+encodeURIComponent(pyWhere.join(' AND '));
      fetch(pyUrl).then(function(r){return r.json();}).then(function(pyVenues){
        var pyMap={};
        (pyVenues||[]).forEach(function(p){
          var k=(p.location_name||'')+'|'+(p.location_zip||'');
          pyMap[k]=parseFloat(p.total_receipts)||0;
        });
        geocoded.forEach(function(v){
          var k=(v.record.location_name||'')+'|'+(v.record.location_zip||'');
          if(pyMap[k]!==undefined) v.record._py_total=pyMap[k];
        });
        _nearbyGeocoded=geocoded;
        renderNearbyCards(geocoded,_currentRadius||1);
      }).catch(function(){
        _nearbyGeocoded=geocoded;
        renderNearbyCards(geocoded,_currentRadius||1);
      });
    }

    fetchBatch(0);
  })
  .catch(function(e){ status.textContent='Error: '+e.message; });
}"""

    c = c[:fn_start] + new_fn + c[fn_end:]
    print('3. runNearbySearch: replaced with address-only lookup'); changes += 1
else:
    print('3. runNearbySearch: function not found')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

print('File size after:', len(c))
print('Changes made:', changes)
print('Done.')
