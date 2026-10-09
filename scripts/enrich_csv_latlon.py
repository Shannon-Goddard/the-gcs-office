"""
enrich_csv_latlon.py
Adds lat/lng columns to ca_licensed_contractors.csv from ca_zip_latlon.json.
Run: python scripts/enrich_csv_latlon.py
"""
import csv, json, os

BASE    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_IN  = os.path.join(BASE, 'data', 'ca', 'ca_licensed_contractors.csv')
CSV_OUT = os.path.join(BASE, 'data', 'ca', 'ca_licensed_contractors.csv')
LOOKUP  = os.path.join(BASE, 'data', 'ca_zip_latlon.json')

with open(LOOKUP) as f:
    zip_map = json.load(f)

with open(CSV_IN, encoding='utf-8', errors='ignore') as f:
    rows = list(csv.DictReader(f))
    fieldnames = list(rows[0].keys())

if 'lat' not in fieldnames:
    fieldnames += ['lat', 'lng']

matched = 0
for row in rows:
    z = row.get('Zip', '').strip()[:5]
    ll = zip_map.get(z)
    if ll:
        row['lat'] = ll[0]
        row['lng'] = ll[1]
        matched += 1
    else:
        row['lat'] = ''
        row['lng'] = ''

with open(CSV_OUT, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f'Done. {matched:,} of {len(rows):,} rows matched ({len(rows)-matched} unmatched).')
