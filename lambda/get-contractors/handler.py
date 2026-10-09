"""
get-contractors/handler.py

GET /api/contractors?zip=92504&trade=plumbing&lastKey=<token>

Queries the zip-trade-index GSI on gcoffice-subs.
Returns 24 contractors per page + a lastKey token for pagination.
trade=all queries each trade separately and merges — capped at 24 for 'all'.
"""

import json
import os
import boto3
from boto3.dynamodb.conditions import Key
import base64

REGION     = os.environ.get('AWS_REGION_NAME', 'us-east-1')
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'gcoffice-subs')
PAGE_SIZE  = 24

TRADES = [
    'general','electrical','plumbing','hvac','painting','roofing','flooring',
    'landscape','framing','carpentry','concrete','masonry','drywall','insulation',
    'plastering','metal','glazing','fencing','earthwork','paving','pipeline',
    'fire','security','elevator','solar','pool','signage','demolition','hazmat','traffic',
]

dynamodb = boto3.resource('dynamodb', region_name=REGION)
table    = dynamodb.Table(TABLE_NAME)

def handler(event, context):
    try:
        params   = event.get('queryStringParameters') or {}
        zip_code = params.get('zip', '92504').strip().zfill(5)
        trade    = params.get('trade', 'all').strip().lower()
        last_key = params.get('lastKey', None)

        if trade == 'all':
            items = query_all_trades(zip_code)
        else:
            items, next_key = query_trade(zip_code, trade, last_key)
            return respond(200, {
                'contractors': [serialize(i) for i in items],
                'count': len(items),
                'lastKey': next_key,
            })

        return respond(200, {
            'contractors': [serialize(i) for i in items],
            'count': len(items),
            'lastKey': None,
        })

    except Exception as e:
        print(f'Error: {e}')
        return respond(500, {'error': 'Could not load contractors'})


def query_trade(zip_code, trade, last_key_token=None):
    gsi_key = f'ZIP#{zip_code}#TRADE#{trade}'
    kwargs  = {
        'IndexName': 'zip-trade-index',
        'KeyConditionExpression': Key('gsi_zip_trade').eq(gsi_key),
        'Limit': PAGE_SIZE,
    }
    if last_key_token:
        try:
            kwargs['ExclusiveStartKey'] = json.loads(
                base64.b64decode(last_key_token).decode()
            )
        except Exception:
            pass

    resp     = table.query(**kwargs)
    items    = resp.get('Items', [])
    last_key = resp.get('LastEvaluatedKey')
    next_token = base64.b64encode(json.dumps(last_key).encode()).decode() if last_key else None
    return items, next_token


def query_all_trades(zip_code):
    """Sample up to 2 contractors per trade for the 'all' view — gives variety."""
    items = []
    for trade in TRADES:
        gsi_key = f'ZIP#{zip_code}#TRADE#{trade}'
        resp = table.query(
            IndexName='zip-trade-index',
            KeyConditionExpression=Key('gsi_zip_trade').eq(gsi_key),
            Limit=2,
        )
        items.extend(resp.get('Items', []))
        if len(items) >= PAGE_SIZE:
            break
    return items[:PAGE_SIZE]


def serialize(item):
    return {
        'license':        item.get('license_number', ''),
        'name':           item.get('business_name', ''),
        'trade':          item.get('field', ''),
        'classification': item.get('classification', ''),
        'city':           item.get('city', ''),
        'state':          item.get('state', 'CA'),
        'zip':            item.get('zip', ''),
        'status':         item.get('status', ''),
        'business_type':  item.get('business_type', ''),
        'issue_date':     item.get('issue_date', ''),
        'expiration_date':item.get('expiration_date', ''),
        'is_bonded':      bool(item.get('is_bonded', False)),
        'is_wc_covered':  bool(item.get('is_wc_covered', False)),
        'claimed':        bool(item.get('claimed', False)),
        'phone':          item.get('phone', ''),
        'lat':            item.get('lat', ''),
        'lng':            item.get('lng', ''),
        'source_url':     item.get('source_url', ''),
    }


def respond(status, body):
    return {
        'statusCode': status,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(body),
    }
