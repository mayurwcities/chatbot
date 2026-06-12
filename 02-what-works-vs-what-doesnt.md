# 02 · What Works vs What Doesn't

The most important doc in the folder. Read before any other.

## What WORKS

| Approach | Why |
|---|---|
| **The platform IS the database of record** | One source of truth. Chat edits it. Outputs go everywhere. No dependency on third-party site internals. |
| **JS widgets for existing websites** | One `<script>` tag works on WordPress, Squarespace, Wix, custom HTML. Owner-managed via chat. Covers ~80% of existing-site venues. |
| **Hosted page for venues without a site** | Auto-generated: `yourplatform.com/v/joes-burgers`. Default, not afterthought. |
| **Native plugins for 1–2 dominant CMSes only** | WordPress first, Shopify second. Each is months of work. |
| **Adapter pattern for third-party APIs** | One adapter per provider. Write once; every customer on that platform benefits. |
| **Chat-first interface as differentiator** | Most B2B SaaS still has 8-tab admin panels. A working chat UI is genuinely new. |
| **Rent intelligence from Claude or GPT-4o** | Frontier LLMs via API. Pay per call. Swap providers in a week. |
| **Vertical-by-vertical expansion** | Restaurants → hotels → tours → retail. Backbone stays constant. |
| **Hand-onboard the first 10 customers** | Manual. Learn what to automate from real usage. |
| **OAuth tokens, never stored passwords** | Square / Toast / Stripe / DoorDash all support this. |
| **Safety stack from Day 1** | Confirmation prompts, undo, audit log, rate limits, tiered permissions, idempotency. Non-negotiable. |
| **Confirmation before destructive actions** | "About to email 500 customers. Continue?" — explicit before bulk / costly / irreversible tool calls. |
| **Per-venue tool registry** | LLM literally cannot call tools that don't apply to this venue. |

## What does NOT work

| Trap | Why |
|---|---|
| **Connect to any external website and edit it** | Unsolved. 12+ months burned for nothing shippable. Trust story is also a non-starter. |
| **Direct writes to a customer's own database** | ~95% of venues have no DB to reach (closed platforms, API-only POS). The rest are all different — per-customer reverse-engineering that breaks on their next plugin update. Writes behind the app's back skip its caches/validation and corrupt the site. |
| **Stateless API pass-through (store nothing on our side)** | LLM needs the catalog in context every turn (latency + provider rate limits force a cache = data anyway). Undo needs prior state. Audit IS stored data. Three platforms disagreeing need a reconciled master. ~30% of venues have no API. CRM has nowhere else to live. |
| **Training a custom LLM** | $10M+ compute, 10–20 researchers, 12+ months. Beaten by frontier the moment you ship. |
| **Multiple third-party integrations in parallel** | Each is 2–4 months solo, longer in parallel. Ship one, sell it, then the next. |
| **All verticals at launch** | Nothing works well anywhere. Data model alone is months if you try to handle all of them. |
| **Self-serve onboarding for V1** | Real venues need handholding. They'll quit at the first error. |
| **"The AI handles everything" pitch** | LLMs hallucinate. Without confirmation + undo + audit, the first bad incident kills the product. |
| **Trying to be everything** | Chat + CRM + POS + payments + ticketing + marketing + analytics. Pick the anchor. The chat is it. |
| **Edge-case features early** | Solve the simple case first. Edge cases come when paying customers ask. |
| **Custom-site integrations as first-class** | Tech-savvy custom sites are 5% of the market and take 10x the engineering. |
| **Voice / WhatsApp / mobile on Day 1** | Web chat first. |
| **Promising same-day support** | 3–4 engineers. Email SLA only at first. |
| **"Replace your POS"** | Too aggressive. Position as the conductor that ties existing tools together. |
| **Web scraping a venue's site for live data** | Brittle. Breaks the moment they change their theme. Only acceptable once at onboarding. |
| **LLM picks destructive tools without confirmation** | "Delete pizza category" → wipes menu before dinner rush. Gate behind explicit confirm. |
| **No audit log** | Without per-action provenance there's no undo, no debugging, no compliance story. |
| **One prompt controlling multiple destructive actions** | Hard limit: max 1 destructive op per call. |

## Reframing the manager's pitch

| What stakeholders ask for | What we build |
|---|---|
| "Plug in your site" | One JS widget on existing sites, OR a hosted page for venues without one. |
| "AI does everything" | Chat translates intent into structured tool calls. Tool layer executes against canonical DB + syncs outward via adapters. |
| "Modify the site" | Update the DB; widget on next page-load shows the change. Third-party platforms sync via adapter. |
| "Without me lifting a finger" | Owner confirms destructive / costly actions in chat (one tap). |

The outcome is identical from the owner's perspective. The implementation
is buildable.

## The "blast radius" rule

For every proposed feature: **if this misfires once, how bad is it?**

| Action | Blast radius | Guardrail floor |
|---|---|---|
| Mark one menu item out of stock | 1 item unavailable | None |
| Update price of one item | One item shows wrong price | Auto-undo offered for 1 hour |
| Update prices of 20 items | Customer confusion | Confirm before applying; show diff first |
| Delete a category | All items orphaned | Confirm + show what'll be deleted + offer dry-run |
| Send promotional email to 500 customers | Customer trust + cost + spam reputation | Confirm with recipient count + cost; rate-limit |
| Refund $200 to a customer | Real money | Owner confirms + second-factor (email click) |
| Disable all hotel rooms for a date range | Lost revenue | Confirm with date range + bookings affected |

A feature without an answer to "what's the blast radius" does not ship.

## Cost-of-error vs cost-of-friction

- Too many confirmations → chat feels slow. Owner stops using it.
- Too few confirmations → first bad incident kills trust.

Confirm only when the action is **bulk** (>5 entities), **destructive**
(delete / disable / refund), or **costly** (mass send, external push).
Single-item edits are one-shot.

When in doubt, add the confirmation.

## Decision rule for new features

1. Does it serve the chat-first vision? If it becomes another admin
   panel, skip it.
2. What's the blast radius if mishandled? If extreme and not gateable,
   defer.
3. Will the first 50 paying restaurants actually ask for this? If no,
   defer.
4. Does it require a new third-party integration? Each is 2–4 months.

If 2+ are red, don't build it now.
