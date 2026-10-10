# The GC's Office — Project Vision & Architecture
### Built by Loyal9 LLC & Amazon Q | Open Source | MIT + DOI Licensed

---

## What We're Building

A free, web-first PWA that is the digital version of everything a contractor carries in their truck.
Estimates, contracts, bookkeeping, receipts, subs, change orders, lien waivers, permits, job photos —
all in one place, all connected, all free.

Every licensed trade gets their own version. GCs, electricians, plumbers, framers, painters, HVAC —
same engine, scoped to their work. The moment a sub sends their signed contract to a GC, it auto-fills
the GC's job ledger. Zero double-entry across the entire job, not just the GC's own receipts.

Home Depot is our source of truth for materials. State DOI data is our source of truth for labor,
waste, and permits. Every contract submitted makes the AI smarter. The data is the business.

---

## The Business Model

**Free. All of it. Forever.**

No per-project fees. No lifetime tiers. No subscriptions. No paywalls.

The Facebook route: frictionless entry, maximum adoption, compounding data. Every bid, every actual,
every sub invoice, every change order, every "pays on time" vet, every finish tier a GC actually buys
— that is the most valuable dataset in the trades industry that has never existed. We collect it,
we make the AI smarter, and the opportunities find us.

What that dataset is worth to insurers, material suppliers, proptech investors, and the trades
industry at large dwarfs anything we'd collect in subscription fees. We don't charge contractors.
We build something so useful they can't imagine working without it.

---

## The Core Problem We're Solving

Contractors run their business out of their truck, their head, or a messy spreadsheet. They type
the same number three times — once for the bid, once for the contract, once for the expense tracker.
Subs send invoices by text. GCs log them manually. Nobody knows if the job is making money until
it's over.

This eliminates all of it:

**Parametric estimate → Kitchen-table client view → Signed contract → One-tap job ledger → Sub invoices auto-post → Snap receipts → Change orders → Lien waivers → .xlsx to accountant**

Zero double-entry. Instant math. Friction-free bookkeeping. Across the entire crew.

---

## Who This Is For

**General Contractor**
- Prefilled estimates from real material costs and regional labor averages
- Three price tiers per item: economy, standard, premium — slider-driven
- Bid converts to a signable contract on demand
- Signed contract becomes an active job-cost ledger automatically
- Sub invoices sent through the app auto-post to the GC's ledger — one tap to approve
- Change orders amend the live contract with a new signature
- Lien waivers generated and signed at payment
- Draw schedule tracked against contract total
- Job site photos logged per project in S3

**Subcontractor (any trade)**
- Claims their profile from the public directory — free, instant
- Gets a trade-scoped PWA: bid tool configured for their specific work
- Electrician sees fixture counts, rough-in footage, panel work
- Plumber sees fixture units, supply/drain runs, water heater, permit fees
- Framer sees stud counts, plate LF, sheathing, labor per sq ft
- Painter sees sq footage, coats, primer, labor rate
- HVAC sees equipment cost, duct LF, labor
- Sends their signed contract directly to the GC — it posts to the GC's ledger automatically
- Gets vetted by GCs they've worked with — reputation travels with them

**Homeowner**
- No contractor needed to get a real number
- No sticker shock — sees everything broken out before work starts
- Kitchen-table view makes the estimate a conversation, not a confrontation

---

## Core Features

### 1. Room Builder
- Input: zip code, room type, L × W × H
- Smart prefilled defaults per room type
- Accordions for detail — progressive disclosure only, no data overload
- Three price tiers per material line: `price_min` / `price_best_seller` / `price_max`

### 2. Trade-Scoped PWA
- Every licensed trade gets a bid tool configured for their scope of work
- Same calculation engine underneath — different inputs, different line items, different UI skin
- Trade skin is set automatically when a sub claims their profile based on license classification
- Editable: sub can add secondary specialties via dropdown
- Trade scopes at launch: General Contractor, Electrician, Plumber, Framer, Painter, Drywall, HVAC

### 3. Live Blueprint
- Mock blueprint renders as selections are made
- Drag and drop: doors, windows, toilets, fixtures
- Wall assignment for placement
- Updates in real time as dimensions or selections change

### 4. Itemized Estimate
- Top line: total project cost
- Broken out: materials, labor, waste disposal, permits, contingency, GC markup (10–20%, editable)
- Every line item sourced and labeled
- GC or sub can override any prefilled value with their actual

### 5. Kitchen-Table View (Client-Facing)
- Clean, bold total with a color-coded progress bar: Materials / Subs / Permits / GC Fee
- Interactive sliders: Standard ↔ Luxury finish toggle, live GC fee adjustment
- Turns the GC into a problem-solver, not a number-defender
- Toggle instantly between Kitchen-Table View and Pro Mode

### 6. Pro Mode (Contractor View)
- Full granular breakdown: exact stud/drywall counts, Home Depot SKU pricing
- Local tax, compliance rules, and margin analysis visible
- Overhead & compliance line items: GL insurance allocation, worker's comp %, markup

### 7. Bid → Contract
- One click converts estimate to formal bid
- One more click converts bid to contract
- In-browser digital signature — no DocuSign, no redirect
- Print-ready PDF output via React PDF
- Stored with zip code for AI training

### 8. Sub → GC Contract Handshake
The network effect that makes the whole system compound.

- Sub completes their scope, generates a contract from their trade PWA
- Sub taps "Send to GC" — selects the GC by profile or active project code
- GC receives a push notification: *"Plumber submitted invoice $3,400 — tap to review"*
- GC reviews line items, taps Approve
- DynamoDB expenses table updates automatically
- Budgets table recalculates variance
- SNS fires if a threshold is crossed
- Zero manual entry on the GC's side — the sub did the paperwork, the app did the bookkeeping

```
Sub signs contract → tags GC project
  → SNS push to GC → GC approves
    → expenses table updated
      → budgets table variance recalculated
        → threshold check → Web Push if triggered
```

### 9. Change Order Management
- GC or sub taps "Request Change Order" on any active contract
- Describes the scope change and revised amount
- New line item added to the contract — original locked values preserved
- Client or counterparty receives push notification to review
- New in-browser signature required to execute
- Ledger updates automatically on approval
- Full change order history preserved on the contract record

### 10. Post-Contract Job Ledger (The Handshake)
When the client signs, one tap converts the locked estimate into an `Active_Job_Budget` ledger.

**Actual vs. Budget Dashboard:**
- Category / Line Item (Framing, Electrician Sub, Permits, etc.)
- Original Contract Budget — locked at signing
- Actual Spent To-Date — aggregated from sub invoices + logged expenses
- Variance / Remaining Balance — color-coded green/red
- Profit Health Meter — total revenue vs. actual costs vs. current net margin

### 11. Draw Schedule Tracker
- GC sets draw milestones at contract signing (e.g., 30% upfront / 30% rough-in / 40% completion)
- Each draw milestone tracked against contract total
- GC marks draw as requested / received
- Draw history visible on the contract record
- Integrates with the ledger — received draws update the revenue side of the Profit Health Meter

### 12. Smart Receipt Reader
- GC taps "Add Expense," snaps a photo of any receipt
- AWS Textract extracts: vendor name, date, line items, total amount
- Auto-categorization matches vendor/items to a project budget line
- GC taps "Approve" — logged, ledger updated, receipt image stored
- Receipt images saved to S3: `receipts/<project_id>/YYYY-MM-DD_<vendor>_<amount>.jpg`
- Audit-ready: tap any expense line to view the original receipt image

### 13. Lien Waiver Generator
- GC taps "Pay Sub" on any sub line item in the ledger
- App generates a conditional lien waiver pre-filled with: sub name, project address, amount, date
- Sub receives push notification, reviews, signs in-browser
- Signed waiver PDF stored in S3 under the project record
- Ledger marks that line item as paid + waived
- Unconditional waiver generated automatically when payment clears (manual confirmation for now)

### 14. Permit Tracker
- Simple status field per project: Applied / Approved / Inspected / Finaled
- GC updates status with one tap
- Permit cost logged against the budget line automatically at "Applied" status
- Push notification reminder if a permit has been in "Applied" status for more than 10 business days
- Permit record stores: permit number, issuing authority, applied date, approved date, final date

### 15. Job Site Photo Log
- GC or sub taps "Add Photo" from any active project
- Photo tagged by: date, category (Framing / Rough-in / Finish / Inspection / Issue)
- Stored in S3: `photos/<project_id>/<category>/YYYY-MM-DD_<timestamp>.jpg`
- Viewable as a chronological timeline per project
- Audit and liability protection — visual record of every stage of work

### 16. Push Notifications (AWS SNS + Web Push)
- Sub invoice submitted: *"Plumber submitted $3,400 — tap to approve"*
- 80% budget threshold alert: *"You've spent 80% of your Framing budget"*
- Over-budget alert: *"Electrician Sub is $340 over budget"*
- Profit margin warning if actuals push net margin below GC's set floor
- Change order submitted for review
- Lien waiver ready to sign
- Permit reminder if stalled at Applied status
- Weekly job summary: budget health snapshot for every active project
- Delivered via AWS SNS → Web Push (PWA) — no third-party push service

### 17. The Rolodex — Public Directory
- Seeded automatically from state contractor licensing board registries, sorted by ZIP and trade
- Search and filter by trade (Electrician, Plumber, Framer, HVAC, Painter, Drywall, etc.) and location
- Unclaimed profiles display public license registry data only — greyscale card, no photo, no contact triggers
- Claimed profiles display in full color with trade icon, photo, work portfolio, click-to-call, click-to-text
- Trade category auto-assigned from state license classification; editable dropdown for secondary specialties
- Trade icons per job title — custom icon set for each trade displayed on card and in directory filter bar
- Accordion expand on each card — basics visible at a glance, more detail expands inline, never leaves the page
- Click-to-call and click-to-text on every claimed profile card
- GC Vouched icons on claimed profiles (Vetted By wall — see below)
- Work photos and self photo uploadable on claimed profiles

**Location & Directory Defaults:**
- No user ever sees a blank page — directory always shows contractors regardless of location state
- Location ON: show contractors within 25mi radius, sorted by proximity then by claimed status
- Location OFF: show top X contractors in the platform's default region, nudge bar at top — "Enter your zip or use your location for local results"
- Zip input or "Use My Location" button always visible — updates results without page reload
- Top X is determined by: claimed first, then vetted count, then proximity to platform default zip

**Claim Your Space workflow:**
- Sub taps "Claim Your Space" on their unclaimed profile (or "Add Me" if not yet in directory)
- Popup appears: input license number + paste the gov URL containing that license (any state board URL)
- Sub clicks Submit — Lambda scrapes that URL, searches for the license number in the response
- Match found: form appears pre-filled with scraped data — sub completes their Rolodex profile
- No match: message displayed — "We couldn't find that license at the URL provided. Please paste a URL from your state's contractor licensing board that shows your license number."
- IP ban detected on scrape: "The licensing board is temporarily blocking requests. Please wait 60 seconds and resubmit." — frontend countdown timer, auto-resubmit enabled after 60s
- Scraped data is used only for verification — nothing from the scrape is stored
- On successful verification: profile unlocks trade PWA, portfolio uploads, direct contact, Vetted By wall
- Claimed profiles stored in `subs` table; unclaimed profiles remain read-only seed data

**Tool Access Gate:**
- Any unclaimed contractor profile attempting to use estimating tools sees: "Claim your space first — it's free and takes 2 minutes"
- Gate is non-destructive: their in-progress work is preserved, claim flow opens as overlay
- Once claimed, gate never appears again for that user

**Vetted By — Sub Profiles:**
- GCs who have worked with a sub can place their face (profile photo + name) on that sub's profile
- Each vet is a clickable card linking to the GC's public profile
- Only the GC can initiate a vet — no requests, no prompts from the sub side
- GC can silently remove their vet at any time — no notification sent to the sub
- Display cap: 3 most recent vets shown, overflow as "+N more"
- Gate: GC must have that sub assigned to a completed project inside the app

**Vetted By — GC Profiles:**
- Subs who have completed a project under a GC can place their face on that GC's public profile
- Vet signals are specific checkmarks — no star ratings, no free text:
  - ✓ Pays on time
  - ✓ Clear scope / no surprise changes
  - ✓ Respectful on site
  - ✓ Would work with again
- Each vet displays the sub's photo, name, trade, and selected checkmarks — clickable to their profile
- Same rules: only the sub can initiate, silent removal available, 3 shown + overflow
- Gate: sub must have a completed project linked to that GC inside the app
- "Pays on time" signal visible in directory search results — the most important hiring signal in the trades

### 18. My Guy — Private Roster
- Private to the user's profile — never visible to others
- Quick-action hub: one-tap call, one-tap text, project-history linking
- Any profile from the Public Directory can be added to My Guy with one tap
- Manually added contacts (off-platform) supported — name, trade, phone minimum

**Business Card Reader:**
- Tap "Add to My Guy" → "Scan a Card"
- Camera opens, snaps the business card
- AWS Textract extracts: name, phone, email, company, trade
- Lambda fuzzy-matches extracted fields against the `subs` table by name + zip + trade
- Match found: *"Is this John Rivera, Licensed Electrician, 92504?"* — one tap confirms, full verified profile linked
- No match: contact added from extracted fields, `linked_sub_id` stays null
- Retroactive link: when an unmatched contact later claims their profile, GC receives a push notification — *"John Rivera just claimed his profile. Link to your existing contact?"* — one tap connects the records automatically
- Same Textract infrastructure as the receipt reader — no new AWS services

**Share / Referral:**
- Every My Guy entry has a Share button
- Triggers `navigator.share()` — native device share sheet
- Pre-formats a clean professional message: name, trade, phone, and app referral link
- Referral metadata tracked for future incentive programs

### 19. Share My Profile — Digital Business Card
- Every claimed profile has a "Share My Profile" button
- Triggers `navigator.share()` with a pre-formatted message and a deep link: `thegcsoffice.com/pro/<name-trade-zip>`
- Recipient taps the link and lands on the full public profile — Vetted By wall, portfolio, license verification
- If recipient is already on the platform: one tap adds to My Guy
- If recipient is not on the platform: they see a real profile with real social proof before any sign-up ask — "Claim Your Space" or sign-up CTA lives at the bottom
- Every profile share is a potential new user landing on a page that already has value — stronger acquisition than any marketing homepage

**QR Code Swap:**
- "Show My QR" button on every profile generates a QR code on screen
- QR encodes the profile deep link
- Two contractors on a job site — one scans the other's screen, profile opens instantly
- No typing, no texting, no card — the modern business card swap
- Built with a lightweight QR library (e.g., `qrcode`) rendering the profile URL — no new infrastructure

### 20. One-Click .xlsx Export
- "Send to Accountant" button generates a clean Excel workbook
- Tab 1 — Summary: P&L, total budget vs. actuals, variance breakdown, draw history
- Tab 2 — Expense Ledger: every transaction with date, vendor, category, amount
- Tab 3 — Sub Invoices: all sub contracts received, approved dates, lien waiver status
- Built server-side with `exceljs` — lightweight, multi-tab
- Ready to email to CPA or hand to client on demand

---

## UI / UX Architecture

### Design Philosophy
Built for a GC in a parking lot with dirty gloves and one free hand. Every critical action is
reachable in one tap. Useful data is always visible. Nothing important is ever buried.
Less is more. The app should feel like the truck dashboard — glanceable, immediate, actionable.

---

### Bottom Nav Bar (Persistent)
No hamburger menu. Four tabs, always visible, thumb-reachable at the bottom of the screen.
Every major section is one tap away from anywhere in the app.

```
[ 🏠 Home ]  [ 📁 Jobs ]  [ 📷 ]  [ 👥 Rolodex ]  [ 👤 Profile ]
                           ^^^^
                    Floating Action Button
```

| Tab | What Lives Here |
|---|---|
| Home | Dashboard — quick actions + active job cards + platform pulse |
| Jobs | Full project list, archived jobs, start new project |
| Rolodex | Public Directory + My Guy roster — toggled in one place |
| Profile | Public profile, QR code, Share My Profile, settings |

---

### Floating Action Button (FAB)
The single most-used action on a job site floats above the nav bar, center screen.
One tap from anywhere opens a three-option action sheet:

```
[ 📄 Scan Receipt ]  [ 📸 Job Photo ]  [ 💼 Scan Business Card ]
```

Three taps maximum from anywhere in the app to any primary field action.
Camera opens, Textract runs, result posts. No navigation required.

---

### Dashboard — Home Tab

**Quick Action Bar**
Big, thumb-friendly icon buttons in a single persistent row at the top.
Muscle memory after the first week. Labels stay for new users.

```
[ Bid ]  [ Contract ]  [ Camera ]  [ Books ]  [ My Guys ]
```

**Active Job Cards**
Each active project renders as a card — not a list row. Real data, at a glance.
Color coded: green is healthy, yellow is watch it, red is act now.

```
┌─────────────────────────────────────┐
│ Johnson Kitchen Remodel             │
│ 📍 Riverside, CA  •  Day 14 of ~30  │
│                                     │
│ Budget  ████████░░  78%  $18,400    │
│ Spent   ██████░░░░  61%  $14,200    │
│ Margin  ████████░░  22%  ✓ Healthy  │
│                                     │
│ ⚠ Framing at 84% — review budget   │
│ 📋 Plumber invoice pending approval │
└─────────────────────────────────────┘
```

Three gauges per card — the right number. More is noise:
1. **Budget Burn** — % of total budget spent
2. **Margin Health** — current net margin vs. GC's set floor
3. **Timeline** — soft estimate: "Day 14 of ~30" derived from project start date
   and regional average completion time from AI data — no schedule entry required

Surface alerts and pending actions directly on the card:
- ⚠ Category over 80% budget threshold
- 📋 Sub invoice pending approval — one tap to review
- ✍ Change order awaiting signature
- 🔑 Permit stalled at Applied status

The GC never has to go hunting. If something needs attention it is on the card.

**Platform Pulse**
Small, ambient. Below the job cards. Makes the app feel alive without being noisy:
- Vets received this month
- Profile views (someone looked you up in the directory)
- Referral conversions (someone you shared joined the platform)

**Empty State**
A new user with no jobs never sees an empty grid.
One clear prompt, one clear action:

*"Start your first project — tap Bid to build your first estimate."*

The dashboard always points somewhere useful.

---

### Rolodex Tab
Two views, one tab, toggled at the top:

```
[ Public Directory ]  [ My Guys ]
```

- Public Directory defaults to the user's zip, filterable by trade and location
- My Guy roster below — quick-action cards with call, text, share, project history
- Search bar persistent across both views

---

### Profile Tab
The user's public-facing profile and personal settings in one place:

- Profile photo, name, trade, license verified badge
- Vetted By wall — GC or sub faces who've vouched for you
- Portfolio images
- **Share My Profile** button — `navigator.share()` deep link
- **Show My QR** button — full-screen QR code for job site swaps
- Settings: notification preferences, margin floor, default markup, trade/specialty

---

### Responsive Behavior
- Mobile first — designed for one hand, job site conditions
- Tablet / desktop: bottom nav shifts to a left sidebar, job cards expand to a two-column grid
- Blueprint canvas (Konva.js) benefits most from tablet/desktop — full drag and drop experience
- All critical actions remain accessible on mobile — no feature is desktop-only

Every material item in every room template carries three price points, sourced from one
representative zip per state (most populated economic hub; CA baseline: 92504).

| Field | Purpose |
|---|---|
| `price_min` | Budget/economy alternative — powers the low end of the finish slider |
| `price_best_seller` | Standard baseline — default for all calculations |
| `price_max` | Premium alternative — powers the luxury end of the finish slider |

### Seeded Categories at Launch
- **Lumber & Shell:** Sill plates, framing studs, roof rafters/trusses, subflooring, roof decking, drywall
- **Exterior Finishes:** House wrap, siding, roofing (shingles/metal), windows, exterior doors
- **Interior Finishes:** Insulation, joint tape/mud, interior doors, baseboards, trim, paint/primer
- **Waste Removal:** Dumpster rental tiers (10-yd, 20-yd), landfill tipping fees
- **Permits & Municipal Fees:** Building permit base, plan check, regional compliance (e.g., CALGreen)
- **Subcontractor Labor:** Electrician, plumber, HVAC/mechanical, general labor/framing crew
- **Overhead & Compliance:** GL insurance allocation, worker's comp %, GC markup (default 15%)

---

## Tech Stack

### Frontend
- **Next.js 14** (App Router) — PWA capable, SEO friendly, fast
- **Tailwind CSS** — utility first, no bloat
- **Konva.js** — canvas-based blueprint with drag and drop
- **React PDF** — contract, estimate, and lien waiver PDF generation
- **Signature Pad** — in-browser digital signature, no DocuSign dependency
- **exceljs** — server-side .xlsx generation
- **qrcode** — profile QR code generation, no infrastructure required

### Backend
- **Next.js API Routes** — one repo, keeps it simple
- **AWS Lambda** — scraper workers, estimate engine, Textract processor, export generator, handshake processor
- **AWS Step Functions** — orchestrates the scrape pipeline
- **SQS** — job queue for scraper workers
- **EventBridge** — scheduled re-scrapes, permit reminders, monthly Bedrock fine-tune trigger

### Data
- **DynamoDB** — primary data store, access-pattern driven schema
- **S3** — contracts, estimates, lien waivers, receipts, job photos, scrape archives
- **ElastiCache (Redis)** — zip-level labor/disposal rate caching, session state

### Notifications
- **AWS SNS** — all push triggers: sub invoices, budget alerts, change orders, lien waivers, permit reminders, weekly summaries
- **Web Push API** — PWA push delivery, no third-party push service

### Auth
- **Clerk** — auth, user management, role assignment (Homeowner / GC / Sub by trade)

### AI & OCR
- **AWS Bedrock** — inference layer, estimate prefill, outlier detection, AI training loop
- **AWS Textract** — receipt OCR, field extraction, auto-categorization
- **AWS Location Service** — zip-to-region resolution for directory proximity search (post-MVP)

---

## DynamoDB Schema (Access Pattern Driven)

### Table: `products`
```
PK: CATEGORY#<category>
SK: SKU#<sku>
Attributes: name, price_min, price_best_seller, price_max, unit_type, dimensions,
            weight, coverage_area, scraped_at
```

### Table: `labor_rates`
```
PK: STATE#<state_code>
SK: TRADE#<trade>
Attributes: avg_hourly, avg_project, source, updated_at
```

### Table: `projects`
```
PK: USER#<user_id>
SK: PROJECT#<project_id>
Attributes: zip, room_type, dimensions, selections, estimate, status, created_at
GSI: ZIP#<zip> → for AI training aggregation
```

### Table: `contracts`
```
PK: PROJECT#<project_id>
SK: CONTRACT#<contract_id>
Attributes: bid_total, line_items, signature, signed_at, pdf_s3_key, zip,
            change_orders[], draw_schedule[], sender_role (GC | SUB), recipient_user_id
```

### Table: `expenses`
```
PK: PROJECT#<project_id>
SK: EXPENSE#<expense_id>
Attributes: vendor, date, amount, category, receipt_s3_key, textract_raw,
            approved_at, source (receipt | sub_contract | manual)
GSI: USER#<user_id> → for cross-project expense views
```

### Table: `budgets`
```
PK: PROJECT#<project_id>
SK: CATEGORY#<category>
Attributes: budgeted_amount, actual_spent, variance, alert_threshold_pct, last_alert_sent_at
```

### Table: `permits`
```
PK: PROJECT#<project_id>
SK: PERMIT#<permit_id>
Attributes: permit_number, issuing_authority, type, status (Applied|Approved|Inspected|Finaled),
            applied_at, approved_at, finaled_at, cost
```

### Table: `lien_waivers`
```
PK: PROJECT#<project_id>
SK: WAIVER#<waiver_id>
Attributes: sub_user_id, amount, waiver_type (conditional | unconditional),
            signed_at, pdf_s3_key, expense_id
```

### Table: `photos`
```
PK: PROJECT#<project_id>
SK: PHOTO#<timestamp>
Attributes: s3_key, category (Framing|Rough-in|Finish|Inspection|Issue), uploaded_by, notes
```

### Table: `subs`
```
PK: STATE#<state_code>
SK: SUB#<license_number>
Attributes: name, trade_primary, trade_secondary, zip, phone, email, license_status,
            claimed, verified_at, portfolio_s3_keys[], profile_image_s3_key
GSI: ZIP#<zip>#TRADE#<trade> → for directory search + filter
```

### Table: `gc_profiles`
```
PK: USER#<user_id>
Attributes: name, photo_s3_key, city, state, zip, bio, active_since,
            pays_on_time_count, clear_scope_count, respectful_count, would_rehire_count
```

### Table: `vets`
```
PK: PROFILE#<vetted_user_id>
SK: VET#<vetter_user_id>
Attributes: vetter_role (GC | SUB), vetted_role (SUB | GC), project_id,
            checkmarks[] (pays_on_time | clear_scope | respectful | would_rehire),
            created_at, removed (bool)
GSI: VETTER#<vetter_user_id> → all vets a user has given (for removal management)
```

### Table: `my_guys`
```
PK: USER#<user_id>
SK: SUB#<sub_id_or_custom>
Attributes: name, trade, phone, email, notes, linked_sub_id (nullable), added_at
```

### Table: `referrals`
```
PK: REFERRER#<user_id>
SK: REFERRAL#<referral_id>
Attributes: sub_id, share_timestamp, referral_link, converted (bool), converted_at
```

---

## Scraper Architecture

### What We Scrape from Home Depot
- Product name, SKU, category, unit cost (min/best_seller/max), unit type, dimensions, weight, coverage area
- One zip code — consistent pricing, no store-level variance
- Weekly re-scrape to keep costs current

### What We Scrape from DOI / State Sources
- Average labor rates by trade (electrician, plumber, tile, drywall, paint, demo)
- Waste disposal rates by state
- Permit cost averages by state

### What We Scrape from State Contractor Licensing Boards
- Contractor name, license number, license classification/trade, license status, zip code
- One scrape per state at launch, seeding the `subs` table with unclaimed profiles
- Quarterly re-scrape to catch new licenses, expirations, and status changes
- Pipeline: Playwright → S3 archive → transform Lambda → DynamoDB subs table

### Pipeline
```
EventBridge (weekly trigger)
  → SQS queue (category-level jobs)
    → Lambda workers (Playwright, rotating headers)
      → raw JSON → S3 archive
        → transform Lambda
          → DynamoDB products table
```

### Anti-Detection Strategy
- Playwright with stealth plugin
- Randomized request delays
- Rotating user agents
- Single zip, single session context — minimal footprint

---

## Sub → GC Handshake Pipeline
```
Sub signs contract → tags GC by project code or profile
  → Lambda writes pending_invoice to contracts table
    → SNS push to GC: "Sub submitted invoice — tap to review"
      → GC approves
        → expenses table updated (source: sub_contract)
          → budgets table variance recalculated
            → SNS threshold check → Web Push if triggered
```

---

## Receipt Processing Pipeline
```
Mobile camera → S3 upload (presigned URL)
  → S3 event → Lambda
    → AWS Textract (AnalyzeExpense API)
      → extracted fields → Lambda categorizer
        → suggested category → GC confirmation
          → expenses table + budgets table updated
            → SNS threshold check → Web Push if triggered
```

---

## Push Notification Logic
```
On business card scan — no match found, contact later claims profile:
  → Lambda detects new claim, fuzzy-matches against unlinked my_guys records
    → SNS → Web Push to GC: "[Name] just claimed their profile. Link to your existing contact?"

On sub invoice approval:
  → expenses + budgets updated → threshold check → alert if triggered

On every receipt write:
  → if actual_spent / budgeted_amount >= 0.80 → SNS → Web Push
  → if actual_spent > budgeted_amount → SNS → over-budget alert
  → if net_margin < gc_margin_floor → SNS → margin warning

On change order submitted:
  → SNS → Web Push to counterparty for review + signature

On lien waiver generated:
  → SNS → Web Push to sub for signature

On permit status stalled (Applied > 10 business days):
  → EventBridge rule → SNS → Web Push reminder

EventBridge (weekly, Monday 7am local time):
  → Lambda aggregates all active project budget health
    → SNS → weekly summary push
```

---

## AI Training Loop

Every completed contract writes to the training dataset:
- zip code, room type, dimensions
- material selections + quantities (with tier: min/standard/max)
- labor actuals (GC and sub overrides)
- final contract total
- sub invoice actuals vs. original estimate
- expense actuals vs. original estimate (post-job variance)
- change order frequency and average delta per trade/zip

Bedrock fine-tuning job runs monthly on accumulated contract data.
Over time: regional accuracy improves, prefill defaults sharpen, outlier detection flags bad bids,
finish-tier defaults calibrate to what contractors actually buy per zip, change order patterns
surface which scopes are chronically underestimated.

---

## The Dataset We're Building

Every free user generates data that has never existed at scale in the trades:

- Real material costs vs. estimated, by zip, by trade, by finish tier
- Real labor actuals vs. DOI averages, by trade, by region
- Change order frequency and delta, by scope type
- Sub invoice amounts vs. GC budget line, by trade
- "Pays on time" signal density by GC, by market
- Finish tier selection rates by zip code and room type

This dataset is valuable to: insurers pricing contractor liability policies, material suppliers
forecasting regional demand, proptech platforms, trade associations, and investors. We don't
sell individual data. We don't sell PII. We build aggregate intelligence and the opportunities find us.

---

## Room Types at Launch (MVP)

- Bathroom
- Kitchen
- Bedroom
- Living Room

Basement, garage, exterior — post-MVP.

---

## PWA vs Native App

PWA first:
- One codebase, works on job site (mobile) and office (desktop)
- No app store approval friction
- Installable, offline capable for blueprint viewing
- Web Push works natively in PWA — no app store needed for notifications
- Trade-specific PWA skins served from the same codebase via role-based routing
- If native is needed later, React Native shares component logic

---

## Open Source & Licensing

- **DOI licensed** — data is free, always
- **MIT licensed** — code is free, always
- Contributors welcome, attribution required
- Every contract's aggregate data feeds the public model, never individual PII

---

## What Makes This Defensible

1. **Free, forever** — zero friction entry, maximum adoption, the data compounds
2. **Home Depot as source of truth** — pricing is real, not estimated
3. **DOI labor data** — not made up averages, sourced and cited
4. **Trade network OS** — every trade on the platform makes every other trade's experience better
5. **Sub → GC handshake** — the more subs on the platform, the more the GC's books fill themselves
6. **Two-way Vetted By** — reputation travels with you, in both directions
7. **The dataset** — the most complete picture of real construction costs ever assembled
8. **All AWS** — one ecosystem, one bill, no third-party service sprawl

---

## Build Order

### Phase 1 — Foundation
1. DynamoDB schema + table setup (all tables)
2. Scraper pipeline (Home Depot + DOI labor data, three price points)
3. Estimate calculation engine (materials + labor + waste + contingency + markup)

### Phase 2 — Frontend Core
4. Clerk auth + role assignment (Homeowner / GC / Sub by trade)
5. Trade-scoped PWA routing — role-based UI skin per trade
6. Room builder + accordion selections + finish slider
7. Blueprint canvas (Konva.js)
8. Kitchen-Table View + Pro Mode toggle
9. Itemized estimate page

### Phase 3 — Bid, Contract & Change Orders
10. Bid → contract flow + PDF generation (React PDF)
11. In-browser digital signature
12. Change order flow — amend contract, new signature, ledger update

### Phase 4 — The Network (Sub → GC Handshake)
13. Sub contract generation (trade-scoped)
14. Sub → GC send flow + GC approval + auto-ledger post
15. Draw schedule tracker
16. Lien waiver generator + sub signature flow

### Phase 5 — Bookkeeping Suite
17. Job ledger — Actual vs. Budget dashboard
18. Receipt upload → S3 → Textract → auto-categorize → expense log
19. Permit tracker
20. Job site photo log
21. SNS + Web Push notification system (all triggers)
22. .xlsx export (exceljs — 3 tabs)

### Phase 6 — The Rolodex
23. State licensing board scraper → seed `subs` table
24. GC + sub public profiles — photo, city, vet wall
25. Public Directory — search, filter, unclaimed profile view
26. Claim Your Space — verification flow + trade PWA unlock
27. Vetted By — two-way system, project-link gate, silent removal
28. My Guy — private roster, business card reader (Textract), quick-action hub, Share via `navigator.share()`
29. Share My Profile — deep link share, QR code swap

### Phase 7 — Intelligence & Launch
29. Bedrock AI integration (estimate prefill + outlier detection)
30. PWA configuration + Web Push service worker
31. Public launch

---

*"Everything in the truck. Nothing on paper. Free forever."*
