import re

path = r'C:\Users\CohnerGibbons\personal-dashboard\static\texas_alcohol_explorer.html'

with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

print('File size before:', len(c))
changes = 0

# Fix runComparison to also resolve typed-but-not-selected venue names
old_run = """function runComparison() {
  var selected = cmpVenues.filter(function(v){return v!==null;});
  if (!selected.length) { alert('Enter at least one venue name and select from the dropdown.'); return; }

  var status = document.getElementById('cmp-status');
  status.style.display = 'block';
  status.textContent = 'Fetching history for ' + selected.length + ' venue(s)…';
  document.getElementById('cmp-result').style.display = 'none';

  var promises = selected.map(function(v) {"""

new_run = """function runComparison() {
  var status = document.getElementById('cmp-status');
  status.style.display = 'block';
  status.textContent = 'Resolving venues…';
  document.getElementById('cmp-result').style.display = 'none';

  // Collect typed names from inputs and resolve any unselected ones
  var inputs = document.querySelectorAll('.cmp-venue-input');
  var resolvePromises = [];
  inputs.forEach(function(inp, slot) {
    var val = inp.value.trim();
    if (!val) return;
    if (cmpVenues[slot] && cmpVenues[slot].location_name.toLowerCase() === val.toLowerCase()) return; // already selected
    // Typed but not selected from dropdown — look up exact match
    resolvePromises.push(
      fetch('https://data.texas.gov/resource/naix-2893.json?$select=location_name,location_city,location_address,location_zip,taxpayer_name&$where=' +
        encodeURIComponent("upper(location_name) like '%" + val.toUpperCase().replace(/'/g,"''") + "%' AND total_receipts>=25000") +
        '&$limit=1&$order=total_receipts DESC')
      .then(function(r){return r.json();})
      .then(function(data){
        if (data && data.length) cmpVenues[slot] = data[0];
      })
    );
  });

  Promise.all(resolvePromises).then(function() {
    var selected = cmpVenues.filter(function(v){return v!==null;});
    if (!selected.length) {
      status.textContent = 'No venues found. Try a more specific name.';
      return;
    }
    status.textContent = 'Fetching history for ' + selected.length + ' venue(s)…';
    var promises = selected.map(function(v) {"""

old_run_end = """  Promise.all(promises).then(function() {
    status.style.display = 'none';
    renderComparison(selected);
  }).catch(function(e){
    status.textContent = 'Error: ' + e.message;
  });
}"""

new_run_end = """    Promise.all(promises).then(function() {
      status.style.display = 'none';
      renderComparison(selected);
    }).catch(function(e){
      status.textContent = 'Error: ' + e.message;
    });
  });
}"""

if old_run in c:
    c = c.replace(old_run, new_run)
    print('1. runComparison top: fixed'); changes += 1
else:
    print('1. runComparison top: not found')

if old_run_end in c:
    c = c.replace(old_run_end, new_run_end)
    print('2. runComparison end: fixed'); changes += 1
else:
    print('2. runComparison end: not found')

with open(path, 'w', encoding='utf-8') as f:
    f.write(c)

print('File size after:', len(c))
print('Changes made:', changes)
print('Done.')
