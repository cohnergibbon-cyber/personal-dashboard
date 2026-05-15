"""
geocode_tabc.py
Run quarterly to keep tx_venues_geo.json up to date.
Handles: new addresses, failed addresses (retried with alternate cities), updates.

Usage (from personal-dashboard folder):
    python static/geocode_tabc.py
"""

import requests, csv, io, json, time
from pathlib import Path

OUT_FILE   = Path(__file__).parent / "tx_venues_geo.json"
TABC_URL   = "https://data.texas.gov/resource/naix-2893.json"
CENSUS_URL = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"
BATCH_SIZE = 9000
PAGE_SIZE  = 50000
TIMEOUT    = 120
MAX_RETRY  = 5

# Cities that are often mislabeled in TABC — try alternates when primary fails
CITY_ALTERNATES = {
    "DALLAS":       ["ADDISON", "RICHARDSON", "GARLAND", "IRVING", "CARROLLTON",
                     "PLANO", "FARMERS BRANCH", "UNIVERSITY PARK", "HIGHLAND PARK"],
    "HOUSTON":      ["BELLAIRE", "WEST UNIVERSITY PLACE", "STAFFORD", "KATY"],
    "FORT WORTH":   ["ARLINGTON", "HURST", "EULESS", "BEDFORD", "KELLER"],
    "AUSTIN":       ["ROUND ROCK", "CEDAR PARK", "PFLUGERVILLE", "BEE CAVE"],
    "SAN ANTONIO":  ["SCHERTZ", "CONVERSE", "LIVE OAK"],
    "ADDISON":      ["DALLAS"],
    "RICHARDSON":   ["DALLAS", "PLANO"],
    "IRVING":       ["DALLAS", "GRAND PRAIRIE"],
}


def fetch_unique_addresses():
    print("Fetching TABC addresses...")
    seen, addrs = set(), []
    offset = 0
    while True:
        params = {"$select": "location_address,location_city,location_zip",
                  "$limit": PAGE_SIZE, "$offset": offset, "$order": "location_address"}
        rows = None
        for attempt in range(1, MAX_RETRY + 1):
            try:
                r = requests.get(TABC_URL, params=params, timeout=TIMEOUT)
                r.raise_for_status()
                rows = r.json()
                break
            except Exception as e:
                wait = attempt * 10
                print(f"  Page error (attempt {attempt}): {str(e)[:60]}")
                print(f"  Retrying in {wait}s...")
                time.sleep(wait)
        if rows is None:
            print("  Giving up on this page, stopping fetch.")
            break
        if not rows:
            break
        for row in rows:
            addr = (row.get("location_address") or "").strip().upper()
            city = (row.get("location_city") or "").strip().upper()
            zip5 = (row.get("location_zip") or "").strip()[:5]
            if addr and city:
                key = addr + "|" + city + "|" + zip5
                if key not in seen:
                    seen.add(key)
                    addrs.append((addr, city, zip5))
        print(f"  ...{offset + len(rows)} rows scanned, {len(addrs)} unique addresses")
        if len(rows) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
        time.sleep(1)
    print(f"Total unique addresses: {len(addrs)}")
    return addrs


def geocode_batch(batch):
    csv_lines = []
    for i, (street, city, zip5) in enumerate(batch):
        s = street.replace('"', '').replace(',', ' ')
        ct = city.replace('"', '').replace(',', ' ')
        csv_lines.append(f'{i},"{s}","{ct}",TX,{zip5}')
    blob = io.BytesIO("\n".join(csv_lines).encode("utf-8"))
    for attempt in range(1, MAX_RETRY + 1):
        try:
            resp = requests.post(CENSUS_URL,
                files={"addressFile": ("addresses.csv", blob, "text/plain")},
                data={"benchmark": "Public_AR_Current", "returntype": "locations"},
                timeout=300)
            resp.raise_for_status()
            break
        except Exception as e:
            print(f"  Census error (attempt {attempt}): {str(e)[:60]}")
            blob.seek(0)
            time.sleep(attempt * 15)
    else:
        return {}
    results = {}
    reader = csv.reader(io.StringIO(resp.text))
    for row in reader:
        if len(row) < 6:
            continue
        try:
            idx = int(row[0])
            match = row[2].strip()
            if match in ("Match", "Tie"):
                coords = row[5].strip().strip('"')
                lng_s, lat_s = coords.split(",")
                results[idx] = (float(lat_s), float(lng_s))
        except Exception:
            continue
    return results


def main():
    existing = {}
    if OUT_FILE.exists():
        with open(str(OUT_FILE), "r", encoding="utf-8") as f:
            existing = json.load(f)
        print(f"Loaded {len(existing)} existing entries")

    all_addrs = fetch_unique_addresses()
    lookup = dict(existing)

    # ── Pass 1: New addresses not yet in lookup
    new_addrs = [(s, c, z) for s, c, z in all_addrs
                 if (s + "|" + c + "|" + z) not in lookup]
    print(f"\n{len(new_addrs)} new addresses to geocode")

    if new_addrs:
        done = 0
        for start in range(0, len(new_addrs), BATCH_SIZE):
            batch = new_addrs[start: start + BATCH_SIZE]
            batch_num = start // BATCH_SIZE + 1
            print(f"Geocoding batch {batch_num} ({len(batch)} addresses, {done}/{len(new_addrs)} done)...")
            results = geocode_batch(batch)
            for idx, (lat, lng) in results.items():
                street, city, zip5 = batch[idx]
                lookup[street + "|" + city + "|" + zip5] = [round(lat, 6), round(lng, 6)]
            done += len(batch)
            print(f"  matched: {len(results)}  unmatched: {len(batch)-len(results)}")
            with open(str(OUT_FILE), "w", encoding="utf-8") as f:
                json.dump(lookup, f, separators=(",", ":"))
            print(f"  Saved {len(lookup)} entries")
            if start + BATCH_SIZE < len(new_addrs):
                time.sleep(2)

    # ── Pass 2: Retry failed addresses with alternate city names
    print("\nChecking for failed addresses to retry with alternate cities...")
    retry_pairs = []  # (original_key, retry_addr, retry_city, retry_zip)
    for addr, city, zip5 in all_addrs:
        key = addr + "|" + city + "|" + zip5
        if key not in lookup and city in CITY_ALTERNATES:
            for alt_city in CITY_ALTERNATES[city]:
                alt_key = addr + "|" + alt_city + "|" + zip5
                if alt_key not in lookup:
                    retry_pairs.append((key, addr, alt_city, zip5))
                    break  # only try first alternate per address

    print(f"{len(retry_pairs)} addresses to retry with alternate cities")

    if retry_pairs:
        retry_batch = [(addr, city, zip5) for _, addr, city, zip5 in retry_pairs]
        done = 0
        for start in range(0, len(retry_batch), BATCH_SIZE):
            batch = retry_batch[start: start + BATCH_SIZE]
            orig_keys = [retry_pairs[start + i][0] for i in range(len(batch))]
            batch_num = start // BATCH_SIZE + 1
            print(f"Retry batch {batch_num} ({len(batch)} addresses, {done}/{len(retry_batch)} done)...")
            results = geocode_batch(batch)
            for idx, (lat, lng) in results.items():
                orig_key = orig_keys[idx]
                # Store under BOTH the original key AND the alternate key
                lookup[orig_key] = [round(lat, 6), round(lng, 6)]
                alt_key = batch[idx][0] + "|" + batch[idx][1] + "|" + batch[idx][2]
                lookup[alt_key] = [round(lat, 6), round(lng, 6)]
            done += len(batch)
            print(f"  matched: {len(results)}  still missing: {len(batch)-len(results)}")
            with open(str(OUT_FILE), "w", encoding="utf-8") as f:
                json.dump(lookup, f, separators=(",", ":"))
            print(f"  Saved {len(lookup)} entries")
            if start + BATCH_SIZE < len(retry_batch):
                time.sleep(2)

    print(f"\nDone. {len(lookup)} total entries in {OUT_FILE}")
    print("Run quarterly to pick up new venues.")


if __name__ == "__main__":
    main()
