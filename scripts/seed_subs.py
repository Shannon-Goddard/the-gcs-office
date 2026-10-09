"""
seed_subs.py — Load ca_licensed_contractors.csv into gcoffice-subs DynamoDB table.
275,390 rows. Uses batch_writer for efficiency (25 items per request).
Run: python scripts/seed_subs.py
"""

import csv
import boto3
from datetime import datetime, date

TABLE_NAME = 'gcoffice-subs'
CSV_PATH   = 'data/ca/ca_licensed_contractors.csv'
REGION     = 'us-east-1'

CLASSIFICATION_FIELD_MAP = {
    'A': 'general', 'B': 'general',
    'C-2': 'insulation', 'C-4': 'plumbing', 'C-5': 'framing',
    'C-6': 'carpentry', 'C-7': 'electrical', 'C-8': 'concrete',
    'C-9': 'drywall', 'C10': 'electrical', 'C11': 'elevator',
    'C12': 'earthwork', 'C13': 'fencing', 'C15': 'flooring',
    'C16': 'fire', 'C17': 'glazing', 'C20': 'hvac',
    'C21': 'demolition', 'C22': 'hazmat', 'C23': 'metal',
    'C27': 'landscape', 'C28': 'security', 'C29': 'masonry',
    'C31': 'traffic', 'C32': 'paving', 'C33': 'painting',
    'C34': 'pipeline', 'C35': 'plastering', 'C36': 'plumbing',
    'C38': 'hvac', 'C39': 'roofing', 'C42': 'plumbing',
    'C43': 'metal', 'C45': 'signage', 'C46': 'solar',
    'C47': 'general', 'C49': 'landscape', 'C50': 'concrete',
    'C51': 'metal', 'C53': 'pool', 'C54': 'flooring',
    'C55': 'plumbing', 'C57': 'earthwork', 'C60': 'metal',
    'C61': 'general', 'D-3': 'carpentry', 'D-4': 'general',
    'D-6': 'concrete', 'D-9': 'earthwork', 'D10': 'flooring',
    'D12': 'landscape', 'D16': 'security', 'D21': 'general',
    'D24': 'metal', 'D28': 'carpentry', 'D29': 'painting',
    'D30': 'earthwork', 'D31': 'general', 'D34': 'general',
    'D35': 'pool', 'D38': 'general', 'D39': 'general',
    'D40': 'general', 'D41': 'framing', 'D42': 'signage',
    'D43': 'landscape', 'D50': 'drywall', 'D52': 'carpentry',
    'D53': 'carpentry', 'D54': 'earthwork', 'D59': 'landscape',
    'D62': 'hvac', 'D63': 'general', 'D64': 'general',
    'D65': 'insulation', 'HAZ': 'hazmat',
}

def resolve_field(classification_raw):
    c = classification_raw.strip().upper()
    if c in CLASSIFICATION_FIELD_MAP:
        return CLASSIFICATION_FIELD_MAP[c]
    for part in c.split():
        if part in CLASSIFICATION_FIELD_MAP:
            return CLASSIFICATION_FIELD_MAP[part]
    return 'general'

def is_bonded(row):
    bond = row.get('ContractorBondNumber', '').strip()
    cancelled = row.get('BondCancellationDate', '').strip()
    if not bond:
        return False
    if cancelled:
        try:
            if datetime.strptime(cancelled, '%m/%d/%Y').date() <= date.today():
                return False
        except ValueError:
            pass
    return True

def is_wc_covered(row):
    coverage = row.get('WorkersCompCoverageType', '').strip().lower()
    cancelled = row.get('PolicyCancellationDate', '').strip()
    expired = row.get('PolicyExpirationDate', '').strip()
    if not coverage or 'exempt' in coverage:
        return False
    if cancelled:
        try:
            if datetime.strptime(cancelled, '%m/%d/%Y').date() <= date.today():
                return False
        except ValueError:
            pass
    if expired:
        try:
            if datetime.strptime(expired, '%m/%d/%Y').date() < date.today():
                return False
        except ValueError:
            pass
    return True

def build_item(row):
    license_num  = row.get('LicenseNumber', '').strip()
    classification = row.get('Classification', '').strip()
    field        = resolve_field(classification)
    zip_code     = row.get('Zip', '').strip()[:5]

    return {
        'pk':             'STATE#CA',
        'sk':             f'LICENSE#{license_num}',
        'gsi_zip_trade':  f'ZIP#{zip_code}#TRADE#{field}',
        'license_number': license_num,
        'business_name':  row.get('BusinessName', '').strip().title(),
        'business_type':  row.get('BusinessType', '').strip(),
        'classification': classification,
        'field':          field,
        'city':           row.get('City', '').strip().title(),
        'state':          'CA',
        'zip':            zip_code,
        'county':         row.get('County', '').strip(),
        'status':         row.get('Status', '').strip(),
        'issue_date':     row.get('IssueDate', '').strip(),
        'expiration_date':row.get('ExpirationDate', '').strip(),
        'is_bonded':      is_bonded(row),
        'is_wc_covered':  is_wc_covered(row),
        'claimed':        False,
        'source_url':     row.get('\ufeffsource_url', row.get('source_url', '')).strip(),
        'seeded_at':      datetime.utcnow().isoformat(),
    }

def main():
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    table    = dynamodb.Table(TABLE_NAME)

    print(f'Loading {CSV_PATH}...')
    with open(CSV_PATH, encoding='utf-8', errors='ignore') as f:
        rows = list(csv.DictReader(f))

    total = len(rows)
    print(f'{total:,} rows found. Starting batch write...')

    written = 0
    skipped = 0
    start   = datetime.now()

    with table.batch_writer() as batch:
        for row in rows:
            license_num = row.get('LicenseNumber', '').strip()
            if not license_num:
                skipped += 1
                continue
            try:
                batch.put_item(Item=build_item(row))
                written += 1
                if written % 10000 == 0:
                    elapsed = (datetime.now() - start).seconds
                    print(f'  {written:,} written ({elapsed}s)...')
            except Exception as e:
                print(f'  ERROR on license {license_num}: {e}')
                skipped += 1

    elapsed = (datetime.now() - start).seconds
    print(f'\nDone. {written:,} written, {skipped} skipped in {elapsed}s.')

if __name__ == '__main__':
    main()
