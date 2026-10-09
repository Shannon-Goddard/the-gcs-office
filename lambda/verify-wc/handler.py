"""
verify-wc/handler.py

POST /api/verify-wc
Body: { "url": "https://www.cslb.ca.gov/..." }

1. Scrapes the gov URL via Bright Data
2. Looks for active WC coverage indicators on the page
3. Returns: { match, banned }
No policy details are stored — only the URL is saved as the badge href.
"""

import json
import os
from playwright.sync_api import sync_playwright

SB_URL = os.environ.get('BRIGHTDATA_SB_URL')

BANNED_PHRASES = [
    'something went wrong',
    'access denied',
    'too many requests',
    'rate limit',
    'blocked',
    'captcha',
]

# Phrases that indicate active WC coverage on a CSLB page
WC_ACTIVE_PHRASES = [
    "workers' compensation insurance",
    "workers compensation insurance",
    "wc insurance",
    "coverage type",
    "policy effective",
    "insurance company",
]

# Phrases that indicate exempt or no coverage
WC_EXEMPT_PHRASES = [
    'exempt',
    'no workers',
    'not required',
]

def scrape_page_text(url):
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(SB_URL, timeout=120000)
        page = browser.new_page()
        try:
            page.goto(url, timeout=60000, wait_until='domcontentloaded')
            page.wait_for_timeout(3000)
            text   = page.inner_text('body').lower()
            banned = any(phrase in text for phrase in BANNED_PHRASES)
            return text, banned
        finally:
            browser.close()

def handler(event, context):
    try:
        body = json.loads(event.get('body', '{}'))
        url  = body.get('url', '').strip()

        if not url:
            return respond(400, {'error': 'url is required'})

        try:
            page_text, banned = scrape_page_text(url)
        except Exception as e:
            print(f'Scrape error: {e}')
            return respond(200, {'match': False, 'banned': False,
                                 'error': 'Could not load that URL.'})

        if banned:
            return respond(200, {'match': False, 'banned': True})

        has_active = any(phrase in page_text for phrase in WC_ACTIVE_PHRASES)
        is_exempt  = any(phrase in page_text for phrase in WC_EXEMPT_PHRASES)

        match = has_active and not is_exempt
        return respond(200, {'match': match, 'banned': False})

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
