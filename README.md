# The GC's Office

**Free. Web-first. Built for working contractors.**

A public contractor directory and operational platform seeded from state licensing board data. Find licensed, bonded, and insured contractors by trade and zip code. Claim your profile in 2 minutes. Free forever.

> *"Everything in the truck. Nothing on paper. Free forever."*

---

## Live Features

### The Rolodex — Find a Pro
- 275,390+ CA licensed contractors seeded from the CSLB public registry
- Filter by 31 trades, search by zip or location
- My Location button — Nominatim reverse geocode → real zip → live results
- License, bond, and WC badges green/gray from real `is_bonded` / `is_wc_covered` DynamoDB fields
- Claimed profiles: full color, click-to-call, click-to-text, work photos, Vetted By wall
- Unclaimed profiles: grayscale, public data only
- Cards paginate 24 at a time via base64 `lastKey` token — Load More appends

### Claim Your Space
- Enter license number + paste the gov URL showing your license
- Lambda scrapes the URL via Bright Data CDP, matches your license number
- Bond and WC verification follow the same pattern — number matched, URL stored, number discarded
- Profile unlocks on verification — no manual review, no waiting

### My Guy — Private Roster
- Private contact list, never visible to others
- Quick-action cards: one-tap call, text, share
- Add manually or scan a business card
- Business card scanner: camera → S3 → AWS Textract → fields prefill the form automatically
- Share via `navigator.share()` — native device share sheet, clipboard fallback

---

## Tech Stack

| Layer | What |
|---|---|
| Frontend | Vanilla HTML + Tailwind CSS (CDN) |
| Backend | AWS Lambda (Docker/Python 3.12) |
| API | Amazon API Gateway (REST) |
| Database | Amazon DynamoDB |
| Storage | Amazon S3 |
| OCR | AWS Textract |
| Scraping | Playwright + Bright Data Scraping Browser CDP |
| IaC | AWS SAM (`template.yaml`) |
| Secrets | AWS SSM Parameter Store |

---

## Repo Structure

```
├── index.html              # Rolodex — public contractor directory
├── my-guy.html             # My Guy — private roster
├── about.html
├── contact.html
├── privacy.html
├── terms.html
├── licenses.html
├── LICENSE                 # MIT
├── VISION.md               # Full product vision and architecture
├── AWS_SETUP.md            # How to rebuild the AWS backend from scratch
├── template.yaml           # SAM template — all Lambda functions + API Gateway
│
├── lambda/
│   ├── Dockerfile          # Single image, all 6 handlers
│   ├── requirements.txt    # playwright, boto3
│   ├── verify-license/     # POST /api/verify-license
│   ├── verify-bond/        # POST /api/verify-bond
│   ├── verify-wc/          # POST /api/verify-wc
│   ├── get-upload-url/     # GET  /api/card-upload-url
│   ├── scan-card/          # POST /api/scan-card
│   └── get-contractors/    # GET  /api/contractors
│
├── scripts/
│   └── seed_subs.py        # Seeds DynamoDB from CSLB CSV (275,390 rows)
│
├── scraper/
│   ├── hd_search.py        # Home Depot material cost scraper
│   └── requirements.txt
│
├── data/
│   ├── license_guide.csv   # 76 CA license classifications → field names
│   ├── labor_data.csv
│   ├── material_cost.csv
│   └── ca/riverside/       # Scraped material costs + permit fees
│
└── icons/
    ├── trades/             # 31 trade SVGs
    └── docs/               # license.svg, bonded.svg, wc-insurance.svg
```

---

## API

Base URL: `https://8bvjb1qz6g.execute-api.us-east-1.amazonaws.com/prod`

| Method | Route | Body | Returns |
|---|---|---|---|
| POST | `/api/verify-license` | `{ license, url }` | `{ match, banned, name, classification, city, status, is_bonded, is_wc_covered }` |
| POST | `/api/verify-bond` | `{ bond, url }` | `{ match, banned }` |
| POST | `/api/verify-wc` | `{ url }` | `{ match, banned }` |
| GET | `/api/card-upload-url` | — | `{ url, key }` — presigned S3 PUT URL |
| POST | `/api/scan-card` | `{ key }` | `{ name, phone, email, company }` |
| GET | `/api/contractors` | `?zip=92504&trade=plumbing&lastKey=...` | `{ contractors[], lastKey }` |

Bond numbers are matched on the page and discarded — never stored.

---

## DynamoDB

**Table**: `gcoffice-subs`

| Key | Example |
|---|---|
| `pk` | `STATE#CA` |
| `sk` | `LICENSE#926325` |
| `gsi_zip_trade` | `ZIP#92504#TRADE#plumbing` |

GSI `zip-trade-index` powers the directory filter by zip + trade.

---

## Setup

See [`AWS_SETUP.md`](AWS_SETUP.md) for the full rebuild guide including:
- DynamoDB table creation
- S3 bucket + lifecycle config
- ECR repo + Docker build command (linux/amd64, provenance=false)
- SSM parameter for Bright Data credentials
- SAM deploy command

---

## Seed the Database

```bash
python scripts/seed_subs.py
```

Reads `data/ca/ca_licensed_contractors.csv` (not in repo — source from CSLB).
Writes 275,390 rows to DynamoDB in ~17 minutes. Computes `is_bonded` and `is_wc_covered` at seed time.

---

## Run the Scraper

```bash
cd scraper
pip install -r requirements.txt
playwright install chromium
python hd_search.py
```

Requires `BRIGHTDATA_SB_URL` in `.env`. Scrapes Home Depot search results for material cost candidates.

---

## Brand

| | |
|---|---|
| Header | `#54585A` Carbonized Gray |
| CTAs | `#A0272D` Rapid Red |
| Font | System UI stack |

Working class truck color palette. No frameworks, no build step, no nonsense.

---

## Roadmap

See [`VISION.md`](VISION.md) for the full 20-feature build plan including:
- Parametric estimating engine
- Bid → Contract → Job Ledger flow
- Sub → GC contract handshake (auto-posts to GC's books)
- Receipt OCR → expense log
- Lien waiver generator
- Vetted By — two-way reputation system
- Share My Profile + QR code swap
- Bedrock AI training loop on real job cost data

---

## License

MIT — see [`LICENSE`](LICENSE).

Data sourced from the California Contractors State License Board (CSLB) public registry.
Not affiliated with or endorsed by the CSLB.

---

## Built By

**Shannon Goddard** — Founder, Loyal9 LLC · Riverside, CA  
[shannon@loyal9.app](mailto:shannon@loyal9.app) · [GitHub](https://github.com/Shannon-Goddard) · [Portfolio](https://shannon-goddard.loyal9.app)

**Amazon Q** — AI pair programmer, AWS  
Every Lambda, every schema, every deploy command, every fix. Built alongside Shannon from first line to first push.

If this saves you time, [buy the dev a beer](https://www.buymeacoffee.com/goddardshannon9).
