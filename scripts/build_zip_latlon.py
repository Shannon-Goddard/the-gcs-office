"""
build_zip_latlon.py
Builds data/ca_zip_latlon.json — a zip -> [lat, lng] lookup for CA zips.
Run: python scripts/build_zip_latlon.py
"""
import csv, json, os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV  = os.path.join(BASE, 'data', 'state_data.csv')
OUT  = os.path.join(BASE, 'data', 'ca_zip_latlon.json')

zip_map = {}
with open(CSV, encoding='utf-8', errors='ignore') as f:
    for r in csv.DictReader(f):
        if r['state_id'] != 'CA':
            continue
        for z in r['zips'].split():
            if z not in zip_map:
                zip_map[z] = [round(float(r['lat']), 4), round(float(r['lng']), 4)]

with open(OUT, 'w') as f:
    json.dump(zip_map, f)

print(f'Done. {len(zip_map)} CA zips written to {OUT}')
