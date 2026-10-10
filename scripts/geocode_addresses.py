"""
geocode_addresses.py

Geocodes contractor street addresses using the free US Census Geocoder batch API.
Skips PO boxes and rows that already have lat/lng from the zip centroid lookup.
Writes results back to ca_licensed_contractors.csv in place.

Run: python scripts/geocode_addresses.py

- Batch size: 10,000 rows (Census API limit)
- Rate: no rate limit on batch endpoint
- Cost: free
- Expected match rate: ~85% of real addresses
"""

import csv, io, os, time, requests

BASE    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_IN  = os.path.join(BASE, 'data', 'ca', 'ca_licensed_contractors.csv')
CSV_OUT = os.path.join(BASE, 'data', 'ca', 'ca_licensed_contractors.csv')

CENSUS_URL  = 'https://geocoding.geo.census.gov/geocoder/locations/addressbatch'
BATCH_SIZE  = 9999  # Census hard limit is 10,000
BENCHMARK   = 'Public_AR_Current'

def is_po_box(addr):
    a = addr.upper().strip()
    return a.startswith('PO BOX') or a.startswith('P O BOX') or a.startswith('P.O.')

def geocode_batch(batch):
    """
    batch: list of (unique_id, address, city, state, zip) tuples
    Returns dict of unique_id -> (lat, lng)
    """
    lines = '\n'.join(f'{uid},"{addr}","{city}",{state},{zip_}' for uid, addr, city, state, zip_ in batch)
    resp = requests.post(CENSUS_URL, files={
        'addressFile': ('batch.csv', lines.encode(), 'text/plain'),
        'benchmark':   (None, BENCHMARK),
    }, timeout=300)
    resp.raise_for_status()

    results = {}
    for row in csv.reader(io.StringIO(resp.text)):
        if len(row) < 6:
            continue
        uid    = row[0].strip()
        status = row[2].strip()  # 'Match' or 'No_Match'
        if status != 'Match':
            continue
        # coords are in row[5]: "lng,lat" (x,y order)
        try:
            lng, lat = row[5].strip().split(',')
            results[uid] = (float(lat), float(lng))
        except Exception:
            continue
    return results

def main():
    with open(CSV_IN, encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
        fieldnames = list(rows[0].keys())

    if 'lat' not in fieldnames:
        fieldnames += ['lat', 'lng']

    # Build work list — skip PO boxes, skip rows that already have precise coords
    # (zip centroid coords are identical across rows in same zip, so we re-geocode those too)
    to_geocode = []
    for i, row in enumerate(rows):
        addr = row.get('Address', '').strip()
        if not addr or is_po_box(addr):
            continue
        to_geocode.append((str(i), addr, row.get('City',''), row.get('State','CA'), row.get('Zip','')))

    total   = len(to_geocode)
    batches = [to_geocode[i:i+BATCH_SIZE] for i in range(0, total, BATCH_SIZE)]
    print(f'{total:,} addresses to geocode across {len(batches)} batches')

    matched = 0
    for b_num, batch in enumerate(batches, 1):
        print(f'  Batch {b_num}/{len(batches)} ({len(batch):,} rows)...', end=' ', flush=True)
        try:
            results = geocode_batch(batch)
        except Exception as e:
            print(f'ERROR: {e} — skipping batch')
            time.sleep(5)
            continue

        for uid, (lat, lng) in results.items():
            rows[int(uid)]['lat'] = lat
            rows[int(uid)]['lng'] = lng
            matched += 1

        print(f'{len(results):,} matched (running total: {matched:,})')

        # Write progress after every batch so a crash doesn't lose work
        with open(CSV_OUT, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        time.sleep(1)  # be polite

    print(f'\nDone. {matched:,} of {total:,} addresses geocoded ({matched/total*100:.1f}%).')

if __name__ == '__main__':
    main()
