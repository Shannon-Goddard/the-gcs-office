import csv, os, asyncio
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

INPUT  = os.path.join(os.path.dirname(__file__), '..', 'data', 'ca', 'riverside', 'material_cost', 'material_cost.csv')
OUTPUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'ca', 'riverside', 'material_cost', 'material_cost_candidates.csv')
BROWSER_WS = os.getenv('BRIGHTDATA_SB_URL')
RESULTS_PER_ITEM = 3
FIELDNAMES = ['item_name', 'rank', 'title', 'url', 'price']
DEBUG = False  # set False for full run


def load_done():
    if not os.path.exists(OUTPUT):
        return set()
    with open(OUTPUT, encoding='utf-8-sig') as f:
        return {r['item_name'] for r in csv.DictReader(f)}


def load_items():
    with open(INPUT, encoding='utf-8-sig') as f:
        return [r['item_name'].strip() for r in csv.DictReader(f) if r['item_name'].strip()]


def append_rows(rows):
    write_header = not os.path.exists(OUTPUT)
    with open(OUTPUT, 'a', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if write_header:
            w.writeheader()
        w.writerows(rows)


async def scrape_item(page, item_name):
    search = page.locator('#headerSearch, input[type="search"], [data-testid="typeahead-search-field"]').first
    await search.wait_for(state='visible', timeout=20000)
    await search.click()
    await search.fill('')
    await search.fill(item_name)
    await search.press('Enter')

    await page.wait_for_url('**/s/**', timeout=30000)

    pod_locator = page.locator('[data-testid="product-pod"]')
    try:
        await pod_locator.first.wait_for(timeout=20000)
    except Exception:
        html = await page.content()
        with open('debug_challenge.html', 'w', encoding='utf-8') as f:
            f.write(html)
        if 'Something went wrong' in html or 'error page' in html.lower():
            raise RuntimeError('HD error page — will retry')
        raise RuntimeError('no product pods found')

    n = min(await pod_locator.count(), RESULTS_PER_ITEM)
    rows = []
    for i in range(n):
        pod = pod_locator.nth(i)
        href = await pod.locator('a[aria-label="Link"]').first.get_attribute('href')
        title = (await pod.locator('[data-testid="attribute-product-label"]').first.inner_text()).strip()
        try:
            price = (await pod.locator('[data-testid="price-simple"]').first.inner_text()).strip().split('\n')[0].strip()
        except Exception:
            price = ''
        rows.append({
            'item_name': item_name,
            'rank': i + 1,
            'title': title,
            'url': 'https://www.homedepot.com' + href if href and href.startswith('/') else (href or ''),
            'price': price,
        })
    return rows


async def connect(p):
    for attempt in range(5):
        try:
            browser = await p.chromium.connect_over_cdp(BROWSER_WS, timeout=120000)
            context = browser.contexts[0] if browser.contexts else await browser.new_context()
            return browser, context
        except Exception as e:
            print(f'Connect attempt {attempt+1} failed: {str(e)[:60]}', flush=True)
            if attempt < 4:
                await asyncio.sleep(15)
    raise RuntimeError('Could not connect after 5 attempts')


async def main():
    done = load_done()
    items = [i for i in load_items() if i not in done]
    print(f'{len(items)} items to scrape, {len(done)} already done.', flush=True)

    async with async_playwright() as p:
        browser, context = await connect(p)
        skipped = 0

        for item in items:
            page = None
            success = False
            for attempt in range(2):
                try:
                    page = await context.new_page()
                    await page.goto('https://www.homedepot.com', wait_until='domcontentloaded', timeout=60000)
                    rows = await scrape_item(page, item)
                    append_rows(rows)
                    print(f'OK  {item}: {len(rows)} results', flush=True)
                    success = True
                    await asyncio.sleep(5)
                    break
                except Exception as e:
                    err = str(e)
                    print(f'ERR {item} (attempt {attempt+1}): {err[:100]}', flush=True)
                    if 'session killed' in err or 'Target page' in err or 'closed' in err or 'error page' in err:
                        print('Reconnecting for fresh session...', flush=True)
                        try:
                            await browser.close()
                        except Exception:
                            pass
                        await asyncio.sleep(5)
                        browser, context = await connect(p)
                    elif attempt == 0:
                        await asyncio.sleep(10)
                finally:
                    if page:
                        try:
                            await page.close()
                        except Exception:
                            pass

            if not success:
                print(f'SKIP {item}', flush=True)
                skipped += 1
                if DEBUG:
                    print('DEBUG mode: stopping after first skip.', flush=True)
                    break

        await browser.close()


asyncio.run(main())
