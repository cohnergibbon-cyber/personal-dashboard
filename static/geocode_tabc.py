import requests
import csv
import io
import json
import time
from pathlib import Path

OUT_FILE   = Path(__file__).parent / "tx_venues_geo.json"
TABC_URL   = "https://data.texas.gov/resource/naix-2893.json"
CENSUS_URL = "https://geocoding.geo.census.gov/geocoder/locations/addressbatch"
BATCH_SIZE = 9000
PAGE_SIZE  = 50000
TIMEOUT    = 120   # seconds per TABC request
MAX_RETRY  = 5     # retries per page


def fetch_unique_addresses():
    print("Fetching TABC addresses...")
    seen   = set()
    addrs  = []
    offset = 0

    while True:
        params = {
            "$select": "location_address,location_city,location_zip",
            "$limit":  PAGE_SIZE,
            "$offset": offset,
            "$order":  "location_address",
        }

        rows = None
        for attempt in range(1, MAX_RETRY + 1):
            try:
                r = requests.get(TABC_URL, params=params, timeout=TIMEOUT)
                r.raise_for_status()
                rows = r.json()
                break
            except Exception as e:
                wait = attempt * 10
                print("  Page error (attempt " + str(attempt) + "): " + str(e)[:80])
                print("  Retrying in " + str(wait) + "s...")
                time.sleep(wait)

        if rows is None:
            print("  Failed after " + str(MAX_RETRY) + " attempts, stopping here.")
            break

        if not rows:
            break

        for row in rows:
            addr = (row.get("location_address") or "").strip().upper()
            city = (row.get("location_city")    or "").strip().upper()
            zip5 = (row.get("location_zip")     or "").strip()[:5]
            if addr and city:
                key = addr + "|" + city + "|" + zip5
                if key not in seen:
                    seen.add(key)
                    addrs.append((addr, city, zip5))

        print("  ..." + str(offset + len(rows)) + " rows scanned, " + str(len(addrs)) + " unique addresses")

        if len(rows) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
        time.sleep(1)

    print("Total unique addresses: " + str(len(addrs)))
    return addrs


def geocode_batch(batch):
    csv_lines = []
    for i, (street, city, zip5) in enumerate(batch):
        s = street.replace('"', '').replace(',', ' ')
        c = city.replace('"', '').replace(',', ' ')
        csv_lines.append(str(i) + ',"' + s + '","' + c + '",TX,' + zip5)

    blob = io.BytesIO("\n".join(csv_lines).encode("utf-8"))

    for attempt in range(1, MAX_RETRY + 1):
        try:
            resp = requests.post(
                CENSUS_URL,
                files={"addressFile": ("addresses.csv", blob, "text/plain")},
                data={"benchmark": "Public_AR_Current", "returntype": "locations"},
                timeout=300,
            )
            resp.raise_for_status()
            break
        except Exception as e:
            wait = attempt * 15
            print("  Census error (attempt " + str(attempt) + "): " + str(e)[:80])
            blob.seek(0)
            time.sleep(wait)
    else:
        return {}

    results = {}
    reader = csv.reader(io.StringIO(resp.text))
    for row in reader:
        if len(row) < 6:
            continue
        try:
            idx   = int(row[0])
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
        print("Loaded " + str(len(existing)) + " existing entries")

    addrs = fetch_unique_addresses()

    new_addrs = [(s, c, z) for s, c, z in addrs if (s + "|" + c + "|" + z) not in existing]
    print(str(len(new_addrs)) + " new addresses to geocode (" + str(len(addrs) - len(new_addrs)) + " already cached)")

    if not new_addrs:
        print("Nothing to do - lookup is up to date.")
        return

    lookup = dict(existing)
    total  = len(new_addrs)
    done   = 0

    for start in range(0, total, BATCH_SIZE):
        batch     = new_addrs[start: start + BATCH_SIZE]
        batch_num = start // BATCH_SIZE + 1
        print("Geocoding batch " + str(batch_num) + " (" + str(len(batch)) + " addresses)...")

        results = geocode_batch(batch)
        for idx, (lat, lng) in results.items():
            street, city, zip5 = batch[idx]
            key = street + "|" + city + "|" + zip5
            lookup[key] = [round(lat, 6), round(lng, 6)]

        done += len(batch)
        print("  matched: " + str(len(results)) + "  unmatched: " + str(len(batch) - len(results)) + "  total done: " + str(done) + "/" + str(total))

        OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(str(OUT_FILE), "w", encoding="utf-8") as f:
            json.dump(lookup, f, separators=(",", ":"))
        print("  Saved " + str(len(lookup)) + " entries to " + str(OUT_FILE))

        if start + BATCH_SIZE < total:
            time.sleep(2)

    print("Done. " + str(len(lookup)) + " total entries saved.")


if __name__ == "__main__":
    main()
