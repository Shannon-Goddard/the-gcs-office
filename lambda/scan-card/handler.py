"""
scan-card/handler.py

POST /api/scan-card
Body: { "key": "uploads/abc123.jpg" }

1. Runs Textract AnalyzeDocument (FORMS) on the S3 object
2. Parses key-value pairs + raw lines for phone, email, name, company
3. Returns: { name, phone, email, company }
Nothing is stored — S3 object expires in 24h via lifecycle rule.
"""

import json
import os
import re
import boto3

BUCKET = os.environ.get('CARD_SCAN_BUCKET', 'gcoffice-card-scans')
REGION = os.environ.get('AWS_REGION_NAME', 'us-east-1')

textract = boto3.client('textract', region_name=REGION)

PHONE_RE = re.compile(r'(\+?1?\s*[\.\-]?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4})')
EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')

def handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        key  = body.get('key', '').strip()
        if not key:
            return respond(400, {'error': 'key is required'})

        resp = textract.analyze_document(
            Document={'S3Object': {'Bucket': BUCKET, 'Name': key}},
            FeatureTypes=['FORMS'],
        )

        # Collect all LINE text blocks
        lines = [b['Text'] for b in resp['Blocks'] if b['BlockType'] == 'LINE']

        # Build key-value map from FORM pairs
        kv = extract_kv(resp['Blocks'])

        phone   = find_phone(lines, kv)
        email   = find_email(lines, kv)
        name    = find_name(lines, kv, phone, email)
        company = find_company(lines, kv, name)

        return respond(200, {
            'name':    name,
            'phone':   phone,
            'email':   email,
            'company': company,
        })

    except Exception as e:
        print(f'Error: {e}')
        return respond(500, {'error': 'Card scan failed'})


def extract_kv(blocks):
    """Build a flat dict of Textract FORM key → value text."""
    block_map = {b['Id']: b for b in blocks}
    kv = {}
    for b in blocks:
        if b['BlockType'] != 'KEY_VALUE_SET' or 'KEY' not in b.get('EntityTypes', []):
            continue
        key_text = get_text(b, block_map)
        for rel in b.get('Relationships', []):
            if rel['Type'] == 'VALUE':
                for vid in rel['Ids']:
                    val_text = get_text(block_map.get(vid, {}), block_map)
                    if key_text and val_text:
                        kv[key_text.lower().strip()] = val_text.strip()
    return kv


def get_text(block, block_map):
    text = ''
    for rel in block.get('Relationships', []):
        if rel['Type'] == 'CHILD':
            for cid in rel['Ids']:
                child = block_map.get(cid, {})
                if child.get('BlockType') == 'WORD':
                    text += child.get('Text', '') + ' '
    return text.strip()


def find_phone(lines, kv):
    # Check KV pairs first
    for k, v in kv.items():
        if any(w in k for w in ('phone', 'cell', 'mobile', 'tel', 'call', 'text')):
            m = PHONE_RE.search(v)
            if m:
                return digits_only(m.group())
    # Fall back to scanning all lines
    for line in lines:
        m = PHONE_RE.search(line)
        if m:
            return digits_only(m.group())
    return ''


def find_email(lines, kv):
    for k, v in kv.items():
        if 'email' in k or 'mail' in k:
            m = EMAIL_RE.search(v)
            if m:
                return m.group()
    for line in lines:
        m = EMAIL_RE.search(line)
        if m:
            return m.group()
    return ''


def find_name(lines, kv, phone, email):
    # KV hint
    for k, v in kv.items():
        if any(w in k for w in ('name', 'contact', 'owner', 'president', 'ceo')):
            return v
    # Heuristic: first line that isn't phone/email/url and looks like a name
    # (2-4 words, title case, no digits)
    skip = {phone, email}
    for line in lines:
        if line in skip:
            continue
        if re.search(r'\d', line):
            continue
        if re.search(r'(http|www|\.com|llc|inc|corp|co\.|contractor|license)', line, re.I):
            continue
        words = line.split()
        if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
            return line
    return ''


def find_company(lines, kv, name):
    for k, v in kv.items():
        if any(w in k for w in ('company', 'business', 'firm', 'contractor', 'llc', 'inc')):
            return v
    for line in lines:
        if line == name:
            continue
        if re.search(r'(llc|inc|corp|co\.|construction|electric|plumbing|hvac|roofing|painting|contracting)', line, re.I):
            return line
    return ''


def digits_only(phone_str):
    digits = re.sub(r'\D', '', phone_str)
    return digits[-10:] if len(digits) >= 10 else digits


def respond(status, body):
    return {
        'statusCode': status,
        'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
        'body': json.dumps(body),
    }
