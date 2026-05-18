"""
patch_cities_compare.py
Fixes two things on the original texas_alcohol_explorer.html:

1. CITY LIST — adds missing cities and fixes FT WORTH:
   - DFW: The Colony, Addison, Highland Park, Burleson, Coppell, Colleyville,
           Waxahachie, Duncanville, DeSoto, Rowlett, Wylie
   - Houston: Cypress, Webster, Kemah, Shenandoah, Tomball, Montgomery
   - Gulf Coast: South Padre Island
   - FT WORTH records now route to Fort Worth (not "All other cities")

2. COMPARE TAB — button stays disabled until 2+ venues selected from dropdown;
   selected inputs turn green to confirm; Clear resets everything properly.

Run from personal-dashboard root: python patch_cities_compare.py
"""
import sys, os
HTML_PATH = os.path.join("static", "texas_alcohol_explorer.html")

NEW_TOP50 = ("'DALLAS','FORT WORTH','FT WORTH','ARLINGTON','PLANO','IRVING','GARLAND','FRISCO',"
"'MCKINNEY','GRAND PRAIRIE','MESQUITE','DENTON','CARROLLTON','RICHARDSON','LEWISVILLE','ALLEN',"
"'GRAPEVINE','SOUTHLAKE','FLOWER MOUND','CEDAR HILL','MANSFIELD','EULESS','BEDFORD','HURST',"
"'KELLER','ROCKWALL','THE COLONY','ADDISON','HIGHLAND PARK','BURLESON','COPPELL','COLLEYVILLE',"
"'WAXAHACHIE','DUNCANVILLE','DESOTO','ROWLETT','WYLIE','FORNEY','HOUSTON','SUGAR LAND','PEARLAND',"
"'LEAGUE CITY','PASADENA','CONROE','THE WOODLANDS','BAYTOWN','FRIENDSWOOD','STAFFORD',"
"'MISSOURI CITY','KATY','SPRING','HUMBLE','CLEAR LAKE','CYPRESS','WEBSTER','KEMAH','SHENANDOAH',"
"'TOMBALL','MONTGOMERY','AUSTIN','ROUND ROCK','CEDAR PARK','PFLUGERVILLE','SAN MARCOS','KYLE',"
"'BUDA','GEORGETOWN','LAKEWAY','BEE CAVE','SAN ANTONIO','NEW BRAUNFELS','SCHERTZ','LIVE OAK',"
"'UNIVERSAL CITY','BOERNE','SEGUIN','MCALLEN','BROWNSVILLE','LAREDO','EDINBURG','MISSION',"
"'HARLINGEN','PHARR','WESLACO','CORPUS CHRISTI','BEAUMONT','PORT ARTHUR','GALVESTON','VICTORIA',"
"'PORT LAVACA','EL PASO','MIDLAND','ODESSA','ABILENE','SAN ANGELO','LUBBOCK','AMARILLO',"
"'WICHITA FALLS','WACO','COLLEGE STATION','TYLER','LONGVIEW','KILLEEN','TEMPLE','LUFKIN',"
"'NACOGDOCHES','TEXARKANA','SHERMAN','MARSHALL','KERRVILLE','FREDERICKSBURG','MARBLE FALLS',"
"'BASTROP','WIMBERLEY','GRANBURY','STEPHENVILLE','BRYAN','SOUTH PADRE ISLAND'")

OLD_TOP50 = ("'DALLAS','FORT WORTH','ARLINGTON','PLANO','IRVING','GARLAND','FRISCO','MCKINNEY',"
"'GRAND PRAIRIE','MESQUITE','DENTON','CARROLLTON','RICHARDSON','LEWISVILLE','ALLEN','GRAPEVINE',"
"'SOUTHLAKE','FLOWER MOUND','CEDAR HILL','MANSFIELD','EULESS','BEDFORD','HURST','KELLER',"
"'ROCKWALL','HOUSTON','SUGAR LAND','PEARLAND','LEAGUE CITY','PASADENA','CONROE','THE WOODLANDS',"
"'BAYTOWN','FRIENDSWOOD','STAFFORD','MISSOURI CITY','KATY','SPRING','HUMBLE','CLEAR LAKE',"
"'AUSTIN','ROUND ROCK','CEDAR PARK','PFLUGERVILLE','SAN MARCOS','KYLE','BUDA','GEORGETOWN',"
"'LAKEWAY','BEE CAVE','SAN ANTONIO','NEW BRAUNFELS','SCHERTZ','LIVE OAK','UNIVERSAL CITY',"
"'BOERNE','SEGUIN','MCALLEN','BROWNSVILLE','LAREDO','EDINBURG','MISSION','HARLINGEN','PHARR',"
"'WESLACO','CORPUS CHRISTI','BEAUMONT','PORT ARTHUR','GALVESTON','VICTORIA','PORT LAVACA',"
"'EL PASO','MIDLAND','ODESSA','ABILENE','SAN ANGELO','LUBBOCK','AMARILLO','WICHITA FALLS',"
"'WACO','COLLEGE STATION','TYLER','LONGVIEW','KILLEEN','TEMPLE','LUFKIN','NACOGDOCHES',"
"'TEXARKANA','SHERMAN','MARSHALL','KERRVILLE','FREDERICKSBURG','MARBLE FALLS','BASTROP',"
"'WIMBERLEY','GRANBURY','STEPHENVILLE','BRYAN'")

PATCHES = [
    # 1. top50 (appears twice)
    ("__TOP50__", None),  # handled specially below

    # 2. Named-only query: expand FT WORTH
    (
        "    } else if (namedCities.length > 0 && !hasOther) {\n"
        "      if (namedCities.length === 1) {\n"
        "        w.push(\"upper(location_city)='\"+namedCities[0]+\"'\");\n"
        "      } else {\n"
        "        w.push(\"upper(location_city) in ('\"+namedCities.join(\"','\")+\"')\");\n"
        "      }\n"
        "    }",
        "    } else if (namedCities.length > 0 && !hasOther) {\n"
        "      var expandedOnly = [];\n"
        "      namedCities.forEach(function(c){expandedOnly.push(c);if(c==='FORT WORTH')expandedOnly.push('FT WORTH');});\n"
        "      if (expandedOnly.length === 1) {\n"
        "        w.push(\"upper(location_city)='\"+expandedOnly[0]+\"'\");\n"
        "      } else {\n"
        "        w.push(\"upper(location_city) in ('\"+expandedOnly.join(\"','\")+\"')\");\n"
        "      }\n"
        "    }"
    ),

    # 3. CSS confirmed
    (
        ".cmp-venue-input:focus { border-color:var(--accent); }",
        ".cmp-venue-input:focus { border-color:var(--accent); }\n.cmp-venue-input.cmp-confirmed { border-color:var(--pos); background:var(--pos-dim); }"
    ),

    # 4. Compare button disabled + sel-count span
    (
        '      <div style="display:flex;gap:8px;margin-top:14px">\n'
        '        <button class="btn-run" id="cmp-run-btn" onclick="runComparison()">Compare</button>\n'
        '        <button class="btn-clear" onclick="clearComparison()">Clear</button>\n'
        '      </div>',
        '      <div style="display:flex;align-items:center;gap:10px;margin-top:14px">\n'
        '        <button class="btn-run" id="cmp-run-btn" onclick="runComparison()" disabled>Compare</button>\n'
        '        <button class="btn-clear" onclick="clearComparison()">Clear</button>\n'
        '        <span id="cmp-sel-count" style="font-family:var(--mono);font-size:11px;color:var(--text3);"></span>\n'
        '      </div>'
    ),

    # 5. cmpSelectVenue + updateCmpBtn
    (
        "function cmpSelectVenue(slot, venue) {\n  cmpVenues[slot] = venue;\n}",
        "function cmpSelectVenue(slot, venue) {\n"
        "  cmpVenues[slot] = venue;\n"
        "  var inputs = document.querySelectorAll('.cmp-venue-input');\n"
        "  if (inputs[slot]) inputs[slot].classList.add('cmp-confirmed');\n"
        "  updateCmpBtn();\n"
        "}\n\n"
        "function updateCmpBtn() {\n"
        "  var count = cmpVenues.filter(function(v){ return v !== null; }).length;\n"
        "  var btn = document.getElementById('cmp-run-btn');\n"
        "  var lbl = document.getElementById('cmp-sel-count');\n"
        "  btn.disabled = count < 2;\n"
        "  lbl.textContent = count >= 2 ? count + ' selected' : (count === 1 ? '1 selected \u2014 need 1 more' : '');\n"
        "}"
    ),

    # 6. clearComparison reset
    (
        "function clearComparison() {\n"
        "  cmpVenues = [null,null,null,null,null];\n"
        "  document.querySelectorAll('.cmp-venue-input').forEach(function(i){i.value='';});\n"
        "  document.querySelectorAll('.cmp-suggestions').forEach(function(s){s.style.display='none';});\n"
        "  document.getElementById('cmp-result').style.display='none';\n"
        "  document.getElementById('cmp-status').style.display='none';\n"
        "  cmpHistory = {};\n"
        "}",
        "function clearComparison() {\n"
        "  cmpVenues = [null,null,null,null,null];\n"
        "  cmpHistory = {};\n"
        "  document.querySelectorAll('.cmp-venue-input').forEach(function(i){ i.value=''; i.classList.remove('cmp-confirmed'); });\n"
        "  document.querySelectorAll('.cmp-suggestions').forEach(function(s){s.style.display='none';});\n"
        "  document.getElementById('cmp-result').style.display='none';\n"
        "  document.getElementById('cmp-status').style.display='none';\n"
        "  document.getElementById('cmp-run-btn').disabled = true;\n"
        "  document.getElementById('cmp-sel-count').textContent = '';\n"
        "}"
    ),

    # 7. Re-type clears slot
    (
        "  if (q.length < 2) { sugBox.style.display = 'none'; return; }",
        "  if (cmpVenues[slot]) { cmpVenues[slot] = null; input.classList.remove('cmp-confirmed'); updateCmpBtn(); }\n"
        "  if (q.length < 2) { sugBox.style.display = 'none'; return; }"
    ),

    # 8. runComparison guard
    (
        "function runComparison() {\n"
        "  var status = document.getElementById('cmp-status');\n"
        "  status.style.display = 'block';\n"
        "  status.textContent = 'Resolving venues\u2026';",
        "function runComparison() {\n"
        "  var selected = cmpVenues.filter(function(v){return v!==null;});\n"
        "  if (selected.length < 2) return;\n"
        "  var status = document.getElementById('cmp-status');\n"
        "  status.style.display = 'block';\n"
        "  status.textContent = 'Fetching history for ' + selected.length + ' venue(s)\u2026';"
    ),

    # 9. CITY_GROUPS DFW
    (
        '"dfw_metroplex": ["DALLAS", "FORT WORTH", "ARLINGTON", "PLANO", "IRVING", "GARLAND", "FRISCO", "MCKINNEY", "GRAND PRAIRIE", "MESQUITE", "DENTON", "CARROLLTON", "RICHARDSON", "LEWISVILLE", "ALLEN", "GRAPEVINE", "SOUTHLAKE", "FLOWER MOUND", "CEDAR HILL", "MANSFIELD", "EULESS", "BEDFORD", "HURST", "KELLER", "ROCKWALL"]',
        '"dfw_metroplex": ["DALLAS", "FORT WORTH", "ARLINGTON", "PLANO", "IRVING", "GARLAND", "FRISCO", "MCKINNEY", "GRAND PRAIRIE", "MESQUITE", "DENTON", "CARROLLTON", "RICHARDSON", "LEWISVILLE", "ALLEN", "GRAPEVINE", "SOUTHLAKE", "FLOWER MOUND", "CEDAR HILL", "MANSFIELD", "EULESS", "BEDFORD", "HURST", "KELLER", "ROCKWALL", "THE COLONY", "ADDISON", "HIGHLAND PARK", "BURLESON", "COPPELL", "COLLEYVILLE", "WAXAHACHIE", "DUNCANVILLE", "DESOTO", "ROWLETT", "WYLIE"]'
    ),

    # 10. CITY_GROUPS Houston
    (
        '"houston_metro": ["HOUSTON", "SUGAR LAND", "PEARLAND", "LEAGUE CITY", "PASADENA", "CONROE", "THE WOODLANDS", "BAYTOWN", "FRIENDSWOOD", "STAFFORD", "MISSOURI CITY", "KATY", "SPRING", "HUMBLE", "CLEAR LAKE"]',
        '"houston_metro": ["HOUSTON", "SUGAR LAND", "PEARLAND", "LEAGUE CITY", "PASADENA", "CONROE", "THE WOODLANDS", "BAYTOWN", "FRIENDSWOOD", "STAFFORD", "MISSOURI CITY", "KATY", "SPRING", "HUMBLE", "CLEAR LAKE", "CYPRESS", "WEBSTER", "KEMAH", "SHENANDOAH", "TOMBALL", "MONTGOMERY"]'
    ),

    # 11. CITY_GROUPS Gulf Coast
    (
        '"gulf_coast": ["CORPUS CHRISTI", "BEAUMONT", "PORT ARTHUR", "GALVESTON", "VICTORIA", "PORT LAVACA"]',
        '"gulf_coast": ["CORPUS CHRISTI", "BEAUMONT", "PORT ARTHUR", "GALVESTON", "VICTORIA", "PORT LAVACA", "SOUTH PADRE ISLAND"]'
    ),
]

# HTML city entries (added to CITY_OPTIONS_HTML string)
DFW_ANCHOR = '<div class=\\"city-opt\\" data-group=\\"dfw_metroplex\\"><input type=\\"checkbox\\" value=\\"ROCKWALL\\" onchange=\\"cityOptionChange()\\" />Rockwall</div>'
DFW_NEW = (DFW_ANCHOR +
    '<div class=\\"city-opt\\" data-group=\\"dfw_metroplex\\"><input type=\\"checkbox\\" value=\\"THE COLONY\\" onchange=\\"cityOptionChange()\\" />The Colony</div>' +
    '<div class=\\"city-opt\\" data-group=\\"dfw_metroplex\\"><input type=\\"checkbox\\" value=\\"ADDISON\\" onchange=\\"cityOptionChange()\\" />Addison</div>' +
    '<div class=\\"city-opt\\" data-group=\\"dfw_metroplex\\"><input type=\\"checkbox\\" value=\\"HIGHLAND PARK\\" onchange=\\"cityOptionChange()\\" />Highland Park</div>' +
    '<div class=\\"city-opt\\" data-group=\\"dfw_metroplex\\"><input type=\\"checkbox\\" value=\\"BURLESON\\" onchange=\\"cityOptionChange()\\" />Burleson</div>' +
    '<div class=\\"city-opt\\" data-group=\\"dfw_metroplex\\"><input type=\\"checkbox\\" value=\\"COPPELL\\" onchange=\\"cityOptionChange()\\" />Coppell</div>' +
    '<div class=\\"city-opt\\" data-group=\\"dfw_metroplex\\"><input type=\\"checkbox\\" value=\\"COLLEYVILLE\\" onchange=\\"cityOptionChange()\\" />Colleyville</div>' +
    '<div class=\\"city-opt\\" data-group=\\"dfw_metroplex\\"><input type=\\"checkbox\\" value=\\"WAXAHACHIE\\" onchange=\\"cityOptionChange()\\" />Waxahachie</div>' +
    '<div class=\\"city-opt\\" data-group=\\"dfw_metroplex\\"><input type=\\"checkbox\\" value=\\"DUNCANVILLE\\" onchange=\\"cityOptionChange()\\" />Duncanville</div>' +
    '<div class=\\"city-opt\\" data-group=\\"dfw_metroplex\\"><input type=\\"checkbox\\" value=\\"DESOTO\\" onchange=\\"cityOptionChange()\\" />DeSoto</div>' +
    '<div class=\\"city-opt\\" data-group=\\"dfw_metroplex\\"><input type=\\"checkbox\\" value=\\"ROWLETT\\" onchange=\\"cityOptionChange()\\" />Rowlett</div>' +
    '<div class=\\"city-opt\\" data-group=\\"dfw_metroplex\\"><input type=\\"checkbox\\" value=\\"WYLIE\\" onchange=\\"cityOptionChange()\\" />Wylie</div>'
)

HOU_ANCHOR = '<div class=\\"city-opt\\" data-group=\\"houston_metro\\"><input type=\\"checkbox\\" value=\\"CLEAR LAKE\\" onchange=\\"cityOptionChange()\\" />Clear Lake</div>'
HOU_NEW = (HOU_ANCHOR +
    '<div class=\\"city-opt\\" data-group=\\"houston_metro\\"><input type=\\"checkbox\\" value=\\"TOMBALL\\" onchange=\\"cityOptionChange()\\" />Tomball</div>' +
    '<div class=\\"city-opt\\" data-group=\\"houston_metro\\"><input type=\\"checkbox\\" value=\\"MONTGOMERY\\" onchange=\\"cityOptionChange()\\" />Montgomery</div>'
)

GULF_ANCHOR = '<div class=\\"city-opt\\" data-group=\\"gulf_coast\\"><input type=\\"checkbox\\" value=\\"PORT LAVACA\\" onchange=\\"cityOptionChange()\\" />Port Lavaca</div>'
GULF_NEW = (GULF_ANCHOR +
    '<div class=\\"city-opt\\" data-group=\\"gulf_coast\\"><input type=\\"checkbox\\" value=\\"SOUTH PADRE ISLAND\\" onchange=\\"cityOptionChange()\\" />South Padre Island</div>'
)

def main():
    if not os.path.exists(HTML_PATH):
        print(f"ERROR: {HTML_PATH} not found. Run from personal-dashboard root.")
        sys.exit(1)
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    print(f"Patching {HTML_PATH} ({len(content):,} chars)...")
    changes = 0

    # top50 (2 occurrences)
    old_top50 = ("'DALLAS','FORT WORTH','ARLINGTON','PLANO','IRVING','GARLAND','FRISCO','MCKINNEY','GRAND PRAIRIE','MESQUITE','DENTON','CARROLLTON','RICHARDSON','LEWISVILLE','ALLEN','GRAPEVINE','SOUTHLAKE','FLOWER MOUND','CEDAR HILL','MANSFIELD','EULESS','BEDFORD','HURST','KELLER','ROCKWALL','HOUSTON','SUGAR LAND','PEARLAND','LEAGUE CITY','PASADENA','CONROE','THE WOODLANDS','BAYTOWN','FRIENDSWOOD','STAFFORD','MISSOURI CITY','KATY','SPRING','HUMBLE','CLEAR LAKE','AUSTIN','ROUND ROCK','CEDAR PARK','PFLUGERVILLE','SAN MARCOS','KYLE','BUDA','GEORGETOWN','LAKEWAY','BEE CAVE','SAN ANTONIO','NEW BRAUNFELS','SCHERTZ','LIVE OAK','UNIVERSAL CITY','BOERNE','SEGUIN','MCALLEN','BROWNSVILLE','LAREDO','EDINBURG','MISSION','HARLINGEN','PHARR','WESLACO','CORPUS CHRISTI','BEAUMONT','PORT ARTHUR','GALVESTON','VICTORIA','PORT LAVACA','EL PASO','MIDLAND','ODESSA','ABILENE','SAN ANGELO','LUBBOCK','AMARILLO','WICHITA FALLS','WACO','COLLEGE STATION','TYLER','LONGVIEW','KILLEEN','TEMPLE','LUFKIN','NACOGDOCHES','TEXARKANA','SHERMAN','MARSHALL','KERRVILLE','FREDERICKSBURG','MARBLE FALLS','BASTROP','WIMBERLEY','GRANBURY','STEPHENVILLE','BRYAN'")
    new_top50 = ("'DALLAS','FORT WORTH','FT WORTH','ARLINGTON','PLANO','IRVING','GARLAND','FRISCO','MCKINNEY','GRAND PRAIRIE','MESQUITE','DENTON','CARROLLTON','RICHARDSON','LEWISVILLE','ALLEN','GRAPEVINE','SOUTHLAKE','FLOWER MOUND','CEDAR HILL','MANSFIELD','EULESS','BEDFORD','HURST','KELLER','ROCKWALL','THE COLONY','ADDISON','HIGHLAND PARK','BURLESON','COPPELL','COLLEYVILLE','WAXAHACHIE','DUNCANVILLE','DESOTO','ROWLETT','WYLIE','HOUSTON','SUGAR LAND','PEARLAND','LEAGUE CITY','PASADENA','CONROE','THE WOODLANDS','BAYTOWN','FRIENDSWOOD','STAFFORD','MISSOURI CITY','KATY','SPRING','HUMBLE','CLEAR LAKE','CYPRESS','WEBSTER','KEMAH','SHENANDOAH','TOMBALL','MONTGOMERY','AUSTIN','ROUND ROCK','CEDAR PARK','PFLUGERVILLE','SAN MARCOS','KYLE','BUDA','GEORGETOWN','LAKEWAY','BEE CAVE','SAN ANTONIO','NEW BRAUNFELS','SCHERTZ','LIVE OAK','UNIVERSAL CITY','BOERNE','SEGUIN','MCALLEN','BROWNSVILLE','LAREDO','EDINBURG','MISSION','HARLINGEN','PHARR','WESLACO','CORPUS CHRISTI','BEAUMONT','PORT ARTHUR','GALVESTON','VICTORIA','PORT LAVACA','EL PASO','MIDLAND','ODESSA','ABILENE','SAN ANGELO','LUBBOCK','AMARILLO','WICHITA FALLS','WACO','COLLEGE STATION','TYLER','LONGVIEW','KILLEEN','TEMPLE','LUFKIN','NACOGDOCHES','TEXARKANA','SHERMAN','MARSHALL','KERRVILLE','FREDERICKSBURG','MARBLE FALLS','BASTROP','WIMBERLEY','GRANBURY','STEPHENVILLE','BRYAN','SOUTH PADRE ISLAND'")
    n = content.count(old_top50)
    if n > 0:
        content = content.replace(old_top50, new_top50)
        changes += 1; print(f"  [OK] top50 arrays ({n} occurrences)")
    else:
        print("  [SKIP] top50 (already patched)")

    # HTML city entries
    for anchor, new_val, label in [(DFW_ANCHOR, DFW_NEW, "DFW HTML entries"),
                                    (HOU_ANCHOR, HOU_NEW, "Houston HTML entries"),
                                    (GULF_ANCHOR, GULF_NEW, "Gulf Coast HTML entries")]:
        if anchor in content and new_val not in content:
            content = content.replace(anchor, new_val, 1)
            changes += 1; print(f"  [OK] {label}")
        else:
            print(f"  [SKIP] {label}")

    # All other patches
    for i, patch in enumerate(PATCHES[1:], 2):
        if patch[0] == "__TOP50__": continue
        old, new = patch
        if old in content:
            content = content.replace(old, new, 1)
            changes += 1; print(f"  [OK] Patch {i}")
        else:
            print(f"  [SKIP] Patch {i} (already applied)")

    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Done. {changes} change(s) applied.")

if __name__ == "__main__":
    main()
