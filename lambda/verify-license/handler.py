"""
verify-license/handler.py

POST /api/verify-license
Body: { "license": "926325", "url": "https://www.cslb.ca.gov/..." }

1. Scrapes the gov URL via Bright Data Scraping Browser
2. Searches the page text for the license number
3. If found, looks up the contractor in DynamoDB and returns their data
4. Returns: { match, banned, name, classification, city, state, license, status }
"""

import json
import os
import re
import boto3
from playwright.sync_api import sync_playwright

REGION     = os.environ.get('AWS_REGION', 'us-east-1')
TABLE_NAME = os.environ.get('DYNAMODB_TABLE', 'gcoffice-subs')
SB_URL     = os.environ.get('BRIGHTDATA_SB_URL')

BANNED_PHRASES = [
    'something went wrong',
    'access denied',
    'too many requests',
    'rate limit',
    'blocked',
    'captcha',
]

def scrape_page_text(url):
    """Scrape page via Bright Data CDP, return (text, banned)."""
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(SB_URL, timeout=120000)
        page = browser.new_page()
        try:
            page.goto(url, timeout=60000, wait_until='domcontentloaded')
            page.wait_for_timeout(3000)
            text = page.inner_text('body').lower()
            banned = any(phrase in text for phrase in BANNED_PHRASES)
            return text, banned
        finally:
            browser.close()

def lookup_dynamo(license_number):
    """Look up contractor in DynamoDB by license number."""
    dynamodb = boto3.resource('dynamodb', region_name=REGION)
    table    = dynamodb.Table(TABLE_NAME)
    resp = table.get_item(Key={
        'pk': 'STATE#CA',
        'sk': f'LICENSE#{license_number}'
    })
    return resp.get('Item')

def handler(event, context):
    try:
        body    = json.loads(event.get('body', '{}'))
        license = body.get('license', '').strip()
        url     = body.get('url', '').strip()

        if not license or not url:
            return respond(400, {'error': 'license and url are required'})

        # Scrape the gov URL
        try:
            page_text, banned = scrape_page_text(url)
        except Exception as e:
            print(f'Scrape error: {e}')
            return respond(200, {'match': False, 'banned': False,
                                 'error': 'Could not load that URL. Check the link and try again.'})

        if banned:
            return respond(200, {'match': False, 'banned': True})

        # Check if license number appears on the page
        if license.lower() not in page_text:
            return respond(200, {'match': False, 'banned': False})

        # Look up in DynamoDB
        item = lookup_dynamo(license)
        if not item:
            # License found on page but not in our DB — still a valid verify
            return respond(200, {
                'match':          True,
                'name':           'Unknown',
                'classification': 'Unknown',
                'city':           'Unknown',
                'state':          'CA',
                'license':        license,
                'status':         'CLEAR',
                'is_bonded':      False,
                'is_wc_covered':  False,
            })

        return respond(200, {
            'match':          True,
            'name':           item.get('business_name', ''),
            'classification': item.get('classification', ''),
            'field':          item.get('field', ''),
            'city':           item.get('city', ''),
            'state':          'CA',
            'license':        license,
            'status':         item.get('status', ''),
            'business_type':  item.get('business_type', ''),
            'issue_date':     item.get('issue_date', ''),
            'expiration_date':item.get('expiration_date', ''),
            'is_bonded':      item.get('is_bonded', False),
            'is_wc_covered':  item.get('is_wc_covered', False),
            'source_url':     item.get('source_url', ''),
        })

    except Exception as e:
        print(f'Unhandled error: {e}')
        return respond(500, {'error': 'Internal server error'})

def respond(status, body):
    return {
        'statusCode': status,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(body),
    }
