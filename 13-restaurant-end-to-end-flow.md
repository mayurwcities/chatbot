# 13 · Restaurant — End-to-End Flow

The complete journey for the restaurant vertical, from first contact to
daily chat-driven operations. This is the walkthrough doc: it stitches
together the architecture (`03`), data model (`04`), orchestrator (`05`),
modules (`06`), integrations (`07`), and safety (`08`) into one
chronological story for a single restaurant.

Restaurants are the launch vertical (Phase 0–3 of `10-roadmap.md`).
Everything below describes what V1 looks like for them.

## The journey at a glance

```
 ┌─────────┐   ┌────────────┐   ┌───────────┐   ┌────────────┐   ┌─────────────┐
 │ 1. SIGN │ → │ 2. BOOTSTRAP│ → │ 3. GO LIVE│ → │ 4. OPERATE │ → │ 5. GROW     │
 │   UP    │   │   DATA      │   │ (page /   │   │  VIA CHAT  │   │ (marketing, │
 │         │   │ (menu,hours)│   │  widget)  │   │  daily     │   │ integrations)│
 └─────────┘   └────────────┘   └───────────┘   └────────────┘   └─────────────┘
   Day 0          Day 0–1          Day 1           Every day        Week 2+
```

Target: a restaurant goes from sign-up to a live, orderable page in
**under one day** (Phase 0: founder-assisted; Phase 6: self-serve in
under 15 minutes).

---

## Step 1 — Sign-up & account creation

### Phase 0–5: manual onboarding (first ~10–50 customers)

No public sign-up form. The founder books a call, walks the owner
through it. This is deliberate (`02` → "Self-serve onboarding for V1"
doesn't work): real owners quit at the first error, and manual
onboarding teaches us what to automate.

What happens on the call:

1. Founder creates the venue from an internal admin:
   - `venues` row: `name`, `slug` (e.g. `joes-burgers`), `type =
     'restaurant'`, timezone, address, phone, brand color, logo.
   - `venue_users` row: owner's email, `role = 'owner'`, invite email
     with a set-password link (NextAuth.js).
   - `venue_modules` rows auto-created from the restaurant default set:
     **menu, hours, marketing, orders** (see `06` → default modules).
2. Owner logs in at the dashboard, lands on the chat UI.
3. Founder stays on the call through Step 2 (data bootstrap).

### Phase 6: self-serve sign-up

The same flow, automated:

1. Owner enters email + restaurant name + address on the sign-up page.
2. Verification email → set password → logged in.
3. `venues` + `venue_users` + default `venue_modules` rows created
   exactly as above; slug auto-generated from the name with a
   uniqueness check.
4. Stripe subscription created (trial first; card required to publish
   the hosted page, not to explore).
5. Owner is dropped straight into the onboarding chat (Step 2).

What sign-up does NOT do at any phase: ask about integrations, POS,
delivery apps, or website. Those come later, one at a time. The only
goal of sign-up is a venue row, an owner login, and an open chat.

---

## Step 2 — Data bootstrap (getting the menu in)

The empty-database problem: chat is useless until the venue has data.
Three ways in, in order of preference:

### 2a. Conversational entry (always available, Phase 0 default)

The owner (or founder, on the call) just types the menu into chat:

```
Owner:  "Add a Margherita pizza, $14, in a Pizzas category.
         Thin or thick crust, large size is $18."

LLM →   addCategory(name: "Pizzas")                    ← didn't exist; LLM
                                                          asked first
LLM →   addMenuItem(
          name: "Margherita",
          category: "Pizzas",
          basePrice: 14.00,
          attributes: {
            crust_type_options: ["thin", "thick"],
            sizes_with_prices: [
              { size: "regular", price: 14 },
              { size: "large",   price: 18 }
            ]
          })

Reply:  "Added Margherita to Pizzas — $14 regular / $18 large,
         thin or thick crust. What's next?"
```

Each item is one `catalog_items` row; sizes and options go in the JSON
`attributes` column per the venue's `attribute_schema` (`04` → catalog).
A 40-item menu takes 20–30 minutes of conversational entry. Tedious but
zero new engineering — it's the same tools used for daily edits.

### 2b. Document import (Phase 0 founder-assisted, Phase 6 self-serve)

Owner uploads a menu PDF, photo of the printed menu, or pastes their
current website URL. An LLM extraction pass turns it into a **draft**
menu:

```
upload menu.pdf
   ↓
LLM extraction (Claude, document/vision input) →
   proposed categories + items + prices + descriptions as JSON
   ↓
draft shown in chat AND as a reviewable list in the dashboard
   ↓
owner corrects in chat: "The Caesar is $12 not $11, and we
   dropped the calzones last year"
   ↓
owner says "looks good" → tool layer commits the batch
   (bulk insert = confirmation required, per safety layer 2)
```

Rules that keep this safe (`02` → blast radius):

- Extraction output is **never** committed directly. It's a draft the
  owner approves. LLM price hallucination on a live menu is exactly the
  incident that kills trust.
- Website scraping happens **once, at onboarding only** — never as an
  ongoing sync (`02` → "Web scraping a venue's site for live data").

### 2c. Import from an integration (Phase 4+)

If the restaurant is on Square: connect Square first (OAuth), pull the
Square catalog as the initial menu, and write `integration_id_map` rows
in the same pass. The POS-connected restaurant skips manual entry
almost entirely. Not available before Phase 4 — don't promise it.

### Hours, profile, and the rest

Same conversational pattern, same call:

```
"We're open 11 to 10 every day, midnight on Fridays and Saturdays."
   → setHours(...) × 7        → business_hours rows

"We're closed Thanksgiving."
   → addSpecialHours(...)     → special_hours row

"Our Instagram is @joesburgers and here's our logo."
   → updateVenueProfile(...)  → venues row
```

### Bootstrap exit checklist

Before go-live, the dashboard shows a simple completeness card (not a
wizard — chat remains the interface, this is just a status display):

- [ ] Menu: ≥ 1 category, ≥ 1 item with a price
- [ ] Hours: all 7 days set (closed counts as set)
- [ ] Profile: address, phone, logo
- [ ] Owner has sent ≥ 1 successful chat command themselves
      (not the founder driving — the owner must experience it)

---

## Step 3 — Going live: hosted page and widget

Two output channels, both rendering from the same canonical DB. The
owner never edits a "website" — they edit data via chat, and every
surface re-renders. This is the reframe from `02`: "modify the site" =
update the DB; the page shows the change on next load.

### 3a. Hosted page (default — Phase 0)

Every venue gets `yourplatform.com/v/{slug}` automatically the moment
the bootstrap checklist passes. Nothing to build, install, or publish.

What's on it (restaurant template):

```
┌────────────────────────────────────────────┐
│  [logo]  Joe's Burgers          [Order]    │
│  Open now · closes 10pm · (212) 555-0148   │
├────────────────────────────────────────────┤
│  MENU (from catalog_categories/items,      │
│        86'd items hidden automatically)    │
│    Pizzas                                  │
│      Margherita ... $14/$18    [Add]       │
│      ...                                   │
├────────────────────────────────────────────┤
│  ORDER  → cart → checkout (Stripe)         │
│         → pickup time selection            │
├────────────────────────────────────────────┤
│  Hours · Address + map · Phone · Socials   │
└────────────────────────────────────────────┘
```

- Server-rendered (Next.js), themed from `venues.brand_colors` +
  `logo_url`. The owner adjusts the look via chat: "make the page use
  our red and show the patio photo at the top."
- "Open now" computed from `business_hours` + `special_hours` in the
  venue's timezone.
- Online ordering is built into the page from Phase 0: cart → Stripe
  checkout → `orders` + `order_items` rows with
  `source = 'hosted_page'`, customer email/phone captured into
  `customers` (this is what seeds the CRM — Step 5).
- Owner sees new orders in the dashboard and via chat: "what's
  pending?" → `listOrders(status: 'pending')`.

This page is not an afterthought; ~30% of venues stay on it permanently
with zero integrations (`07` → "no integrations" mode). Google
indexing, a QR code generator (table tents, window sticker), and an
Instagram-bio-ready link are part of the template.

### 3b. JS widget for existing websites (Phase 3)

For the restaurant that already has a site (WordPress, Wix,
Squarespace, custom HTML) and wants to keep it:

```html
<script src="https://yourplatform.com/widget.js"
        data-venue="joes-burgers"
        data-widgets="menu,order"></script>
```

- One script tag; works on any host that allows custom HTML. Renders
  menu + ordering (and later reservations) inside their page,
  iframe-safe, CORS-clean, < 50 kb gzipped, < 200 ms load (`10` →
  Phase 3 budget).
- Same data source as the hosted page. The owner 86's an item in chat;
  the widget reflects it on the next page load. No "publish" step, no
  site editing, no access to their site needed.
- Appearance (colors, font, layout density) configured in a small
  admin editor — and adjustable via chat: "make the widget match my
  site's dark theme."
- The hosted page keeps existing in parallel as the canonical
  fallback/order link.

### What we deliberately do NOT offer

Per the hard "no"s in `CLAUDE.md` and `02`:

- We don't log into or edit their existing website. Ever.
- We don't read or write their site's database.
- A full "website builder" with drag-and-drop is out of scope: the
  hosted page is a **templated render of canonical data** with theme
  options, not a page builder. If an owner wants arbitrary layout
  control, the answer is the widget on a site they control.
- Native CMS plugins (WordPress) arrive Phase 6, and only because one
  plugin covers a huge share of the market — not as a general pattern.

---

## Step 4 — Daily operation via chat

This is the product. Everything the owner does day-to-day is a chat
message → orchestrator → tool call(s) → canonical DB → fan-out to
surfaces. Full loop mechanics in `05`; restaurant-flavored examples:

### Menu management

| Owner says | Tool call(s) | Confirmation? |
|---|---|---|
| "86 the lobster roll" | `setItemAvailability(47, false)` | No — single item, reversible |
| "Lobster roll is back" | `setItemAvailability(47, true)` | No |
| "Raise the burger to $13.50" | `updateMenuItem(12, {base_price: 13.50})` | No — but undo offered for 1h |
| "Raise everything in Pizzas by $1" | bulk `updateMenuItem` × N | **Yes** — shows diff of all N items first |
| "Add a weekend brunch menu" | `addCategory` + `addMenuItem` × N | Batch insert → yes |
| "Delete the Appetizers category" | `deleteCategory(...)` | **Yes** — tool returns what would be orphaned, owner approves token (`05` → Rule 5) |

### Hours

| Owner says | Result |
|---|---|
| "Close early tonight at 8" | `special_hours` row for today |
| "We're closed July 4th" | `special_hours` row, `is_closed = 1` |
| "Starting next month, open Mondays" | `business_hours` with `effective_from` |

Hosted page / widget "Open now" badge and (later) DoorDash + Google
Business Profile hours update from the same row.

### Orders

| Owner says | Tool call |
|---|---|
| "What's pending?" | `listOrders(status: 'pending')` |
| "Mark order 218 ready" | `updateOrderStatus(218, 'ready')` |
| "Refund the cold-pizza order, $18" | `refundOrder(...)` — confirmation + owner role + email second factor (`02` → blast radius) |
| "Take a phone order: large Margherita for Dana, pickup 6:30" | `manualOrder(...)` |

### Questions (read-only — half of all usage)

"What were my top sellers last week?", "How many orders did we do
Saturday?", "Do we have anything vegan on the menu?" — `analytics` and
read tools, no confirmation, no audit beyond access log.

### Who can do what

`venue_users.role` gates tools (`08` → tiered permissions):

| Role | Can | Cannot |
|---|---|---|
| owner | everything | — |
| manager | menu, hours, orders, campaigns | refunds above limit, billing, user management |
| staff | 86 items, order status, read menu | price changes, campaigns, deletes |
| viewer | read-only | any write |

The shift cook gets a login that can 86 the special but cannot fat-finger
a price change. Same chat UI; smaller tool list assembled per user.

### Safety, in flow terms

Every write above passes the same gauntlet (`08`): tool-level argument
limits → confirmation check (bulk / destructive / costly) → rate limit →
execute with idempotency key → `audit_log` row with before/after JSON →
undo window. The owner-visible parts: occasional one-tap confirms, an
"undo" reply that works for an hour after single edits, and an activity
feed in the dashboard rendered from `audit_log` ("Yesterday 4:12pm —
staff Maria 86'd Lobster Roll").

---

## Step 5 — Growth: CRM and marketing (Phase 1)

The CRM builds itself. Every hosted-page/widget order upserts a
`customers` row (email/phone, opt-in flags, running `total_orders` /
`total_spend`, `last_order_at`). No import, no setup.

Campaign flow, entirely in chat:

```
Owner:  "Send 15% off to anyone who ordered in the last 30 days
         but not the last 7."

LLM →   searchCustomers({last_order_between: [-30d, -7d]})
Reply:  "That's 142 customers with email opt-in. Drafted:
         [subject + body preview]. Estimated cost $0.15.
         Send now, schedule, or edit?"

Owner:  "Send at 4pm."

LLM →   sendCampaign({segment, channel: 'email', scheduled_for: ...,
                      confirmation_token: 'xyz'})
```

- Recipient count + cost shown **before** the confirm, always (`06` →
  marketing module). >100 recipients always confirms.
- Sends go through the comms adapter (SendGrid/Mailgun/Postmark for
  email, Twilio for SMS) with per-recipient status rows, open/click
  tracking (`campaign_tracking`, `campaign_clicks`), and unsubscribe
  handling baked in.
- Later: "How did Friday's promo do?" → `getCampaignStats(...)` →
  "38% opens, 9% clicks, 21 orders attributed, $480 revenue."

---

## Step 6 — Integrations, one at a time (Phase 2 & 4)

Only after the restaurant is live and using chat daily. Strictly
sequenced (`07` → priority order): DoorDash first, then Square POS,
then Uber Eats, then Toast.

### Connecting DoorDash (Phase 2)

1. Owner (in chat or settings): "Connect my DoorDash."
2. OAuth redirect → owner approves → encrypted tokens in
   `venue_integrations` (`status: 'pending'`).
3. Initial sync job: push the canonical menu via the DoorDash adapter,
   write `integration_id_map` rows for every category/item/modifier.
4. Owner reviews the result; `status → 'active'`. Dashboard shows a
   sync badge per integration: `synced / syncing / partial / failed`.

From then on, every menu/hours/availability tool call fans out
automatically (`07` → fan-out): "86 the lobster roll" now updates the
canonical DB, the hosted page, the widget, **and** DoorDash in <30s —
one chat message. Inbound DoorDash orders arrive by webhook as `orders`
rows (`source: 'doordash'`) and feed the same CRM and "what's pending?"
view.

Failures degrade gracefully, never silently: per-call retry queue,
chat-visible surfacing ("Uber Eats push failed — retrying"), and a
"DoorDash hasn't synced in 3 hours, tap to reconnect" nudge.

### Connecting Square POS (Phase 4)

Same connect flow, plus bidirectional sync: pull every 5–15 min; if the
owner edited a price on the Square terminal during service, Square wins
the conflict, our canonical row updates, and outward surfaces re-publish
(`03` → source-of-truth policy). True conflicts (both sides changed)
surface in chat as a question, not a silent overwrite.

---

## Failure modes & the unhappy paths

| Situation | Behavior |
|---|---|
| LLM misunderstands ("86 the roll" — two roll items) | Tool returns `ambiguous_item` + candidates; LLM asks which (`05` → Rule 3) |
| Owner regrets an edit | "Undo that" → revert from `audit_log.before_json` (1h window for single edits) |
| Bulk request over limits | Tool refuses >N items per call; LLM splits with confirmation, or declines |
| Integration down | Canonical commit succeeds, chat replies immediately, sync retries async — chat reply is never blocked on a third party (`07` → What NOT to do) |
| Owner asks for another venue's data | Hard refusal; `venue_id` is bound to the session, never LLM-supplied |
| Chat itself is down | Dashboard retains minimal manual fallbacks (86 toggle, order status) — the DB is the product, chat is the interface |

## Timeline summary (maps to `10-roadmap.md`)

| When | What the restaurant experiences |
|---|---|
| Phase 0 (M1–3) | Sign-up (hand-held) → menu + hours via chat → hosted page live with ordering → daily chat ops |
| Phase 1 (M4–6) | CRM accumulating; first email/SMS campaigns from chat |
| Phase 2 (M7–10) | DoorDash connected; one message updates everywhere; delivery orders flow in |
| Phase 3 (M8–10) | Widget embedded on their existing site |
| Phase 4 (M11–13) | Square POS two-way sync |
| Phase 6 (M16–18) | Self-serve sign-up; PDF/URL menu import fully automated; sub-15-minute onboarding |

## Open questions (not yet locked — see `12-decisions-now-vs-later.md`)

- Pickup only vs delivery on the hosted page at Phase 0 (lean: pickup
  only; delivery logistics is not our business).
- Whether hosted-page ordering charges per-order fees or is flat-rate
  within the subscription.
- Reservation support timing for restaurants (module exists in the
  catalog; OpenTable adapter is Month 13+).
