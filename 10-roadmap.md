# 10 · Roadmap

Phased build plan. Greenfield — nothing reused from any prior codebase.
Don't move to the next phase until the current one's exit metric is hit.

## Summary

| Phase | Months | Goal | Customers at end |
|---|---|---|---|
| 0 | 1–3 | Chat + safety + hosted page for restaurants. No integrations. | 5 |
| 1 | 4–6 | Marketing module (campaigns, customer CRM). | 5–10 |
| 2 | 7–10 | DoorDash sync. | 10–15 |
| 3 | 8–10 (parallel) | JS widget for existing sites. | 15–25 |
| 4 | 11–13 | Square POS + hotels vertical. | 25–40 |
| 5 | 14–15 | Tickets vertical. | 40–50 |
| 6 | 16–18 | Self-serve onboarding + Uber Eats + Toast + SOC 2 start. | 50–100 |

End state at ~18 months: working multi-vertical platform with
restaurants + hotels + tour operators, $40k+/month revenue, ready for
Series A.

---

## Phase 0 — Foundation (Months 1–3)

**Goal:** working chat + canonical DB + safety stack. Restaurants only.
No integrations.

### Build

| Item |
|---|
| Canonical DB schema |
| Chat orchestrator (agent loop, Claude Sonnet 4.6, tool registry, context loader, response streaming) |
| Safety stack (layers 1, 2, 3, 4, 6, 9 minimum) |
| Mock `LLMProvider` for unit tests / CI (no live LLM in the test loop) |
| Regression corpus: real owner messages → expected tool calls, re-run on every prompt change |
| `menu` module tools |
| `hours` module tools |
| Auto-generated hosted page `yourplatform.com/v/{slug}` |
| Owner dashboard (login + chat UI + audit log viewer + basic settings) |
| Manual onboarding (founder hand-walks each customer) |

### Exit criteria

- 5 paying restaurant customers
- Each using chat at least once per day
- Zero data-loss incidents in audit log
- 95%+ of chat turns correctly execute the request (measured by manual
  review of first 100 sessions per customer)

### Out of scope

- DoorDash / Uber Eats (Phase 2)
- POS sync (Phase 4)
- Other verticals (Phase 4+)
- Self-serve onboarding (Phase 6)
- Mobile, voice, WhatsApp (Year 2+)

---

## Phase 1 — Marketing + CRM (Months 4–6)

**Goal:** restaurants now sending marketing campaigns from chat. CRM
builds up from hosted-page orders.

### Build

| Item |
|---|
| `customers` table + capture from hosted-page orders |
| `marketing` module tools |
| Transactional + marketing email pipeline (SendGrid / Mailgun / Postmark) |
| SMS pipeline (Twilio) |
| Tracking pixel + click-tracking redirector |
| Per-campaign analytics in chat ("Show me opens for last week's promo") |
| Cost-aware confirmation ("About to send to 487 customers, est. $0.49 — confirm?") |

### Exit criteria

- At least 3 customers sent ≥ 1 marketing campaign
- Open rate > 25%
- < 1 sent-by-mistake incident across all customers

---

## Phase 2 — First Integration: DoorDash (Months 7–10)

**Goal:** two-way sync. Menu edits push out; orders flow in.

### Build

| Item |
|---|
| DoorDash partner agreement (start in Month 4 — certification takes months) |
| OAuth flow |
| Outbound adapter (`pushMenu`, `setItemAvailability`, `setHours`) |
| ID mapping table |
| Inbound webhook receiver |
| Sync state badges (`synced` / `syncing` / `partial_sync` / `sync_failed`) |
| Owner-facing connect flow |
| Retry queue + alert on persistent failure |

### Exit criteria

- 3+ restaurants fully two-way synced
- < 1 sync failure per week per venue
- Mark item 86'd in chat → both menu and DoorDash update in <30s

### Trap

Don't block phase progression on DoorDash certification — start in
Month 4 in parallel. If certification is delayed, ship with sandbox
credentials and onboard production customers as it clears.

---

## Phase 3 — JS Widget (Months 8–10, parallel to Phase 2)

**Goal:** venues with an existing site can embed the widget instead of
using the hosted page.

### Build

| Item |
|---|
| Widget bundle (menu, order form, reservation widget) |
| Per-venue theme config |
| Widget appearance editor in admin |
| Cross-origin embed (CORS + iframe-safe layout) |
| Performance budget: < 50kb gzipped, < 200ms load |

### Exit criteria

- 10+ venues using widget on existing sites
- Onboard in < 15 minutes from sign-up to live widget

---

## Phase 4 — Square POS + Hotels Vertical (Months 11–13)

**Goal:** cover the other half of US restaurant POS share AND open the
hotels vertical.

### Build

#### Square POS

| Item |
|---|
| `adapters/pos/square.js` (OAuth, menu push, order pull, inventory sync) |
| Conflict resolution when owner edits in chat AND on Square terminal |
| Square Catalog API mapping (items, categories, modifiers, taxes) |

#### Hotels vertical

| Item |
|---|
| `rooms` module (schema + tools) |
| Hosted hotel page (booking widget, room display, photos) |
| Booking.com adapter (inbound only — channel-manager pull) |

### Exit criteria

- 15+ restaurants on Square + DoorDash
- 5+ hotel customers using the rooms module
- $20k+ MRR

### Why now

Restaurant economics validated. Hotels = higher ACV ($200–500/mo vs
$50–100 for restaurants), justifying the engineering investment.

---

## Phase 5 — Tickets / Events (Months 14–15)

**Goal:** tour operators, theaters, escape rooms, small concert venues.

### Build

| Item |
|---|
| `tickets` module (tours, schedules, ticket_tiers) |
| `events` module (lighter, with attendee lists) |
| Stripe Connect integration |
| QR ticket generation (email + QR) |
| Door-side check-in flow (mobile-optimised) |
| Eventbrite adapter (push events for discovery) |

### Exit criteria

- 5+ tour operators actively booking via chat
- Door check-in works on a phone at a 50+ ticket live event
- $30k+ MRR

---

## Phase 6 — Polish + Scale (Months 16–18)

**Goal:** prepare for marketing spend + scale. Onboarding self-serve.

### Build

| Item |
|---|
| LLM-powered onboarding (paste URL / upload menu PDF / photo → AI bootstraps profile) |
| Uber Eats adapter |
| Toast POS adapter |
| OpenTable adapter |
| SOC 2 Type I audit (start Month 14, complete Month 22) |
| WordPress plugin |
| Self-serve billing (Stripe subscriptions) |
| Help docs + onboarding videos |
| Public REST API + docs |

### Exit criteria

- 50+ paying venues across 3 verticals
- Self-serve sign-up conversion > 30%
- $40k+ MRR
- < 5% monthly churn

### Optional (demand-driven)

- Mobile app
- Voice / WhatsApp interface
- White-label / reseller program

---

## Explicitly deferred

| Ask | Defer to | Reason |
|---|---|---|
| Voice (Twilio call to bot) | Year 2 | Chat web first; STT/TTS adds latency + complexity |
| Mobile app (native) | Year 2 | PWA suffices for most owners |
| Edit-any-arbitrary-website | Never | Unsolved AI problem; reframe as widget + hosted page |
| Multi-location chains | Year 2 | Architecture supports it; UX needs redesign |
| International + multi-currency | Year 2 | First market dominated first |
| Custom CMS plugins beyond WordPress | When asked | Niche |
| Marketplace (venues find venues) | Never as Phase 1 | No network effect yet |
| AI image generation for menu photos | Late Year 2 | Nice-to-have |
| AI-generated marketing copy | Phase 6 stretch | Owners write better promos initially |
| Loyalty / rewards | Late Phase 6 | Customers request when ready |
| Native POS replacement | Never | Sell as chat layer ABOVE existing POS |

## Pitfalls that break this timeline

| Pitfall | Cost | How to avoid |
|---|---|---|
| Adding a second vertical before nailing restaurants | 3 months | Move Phase 4 hotels AFTER restaurants are loved by 25+ paying venues |
| Building 3 integrations in parallel | 6 months | Sequence strictly. DoorDash, then Square, then Uber Eats |
| Skipping safety stack to ship faster | Catastrophic | All 10 layers by end of Phase 1. No exceptions |
| Self-serve before 10 hand-held customers | 2–3 months | Manual onboarding for first 10 |
| Building a "universal" integration framework | Endless | Adapters per provider; copy-paste over abstractions |
| One big customer demanding their own roadmap | Months of distraction | Don't sell to them. Pick narrow, repeatable profile |
| Mid-roadmap LLM provider change | 2–3 weeks | Pick at start; commit for a year |

## How to use this roadmap

- Review monthly. Reality diverges; adjust quarterly.
- Don't lock customer commitments to features that aren't yet shipped.
- Each phase has an exit criterion. Don't move on until met, calendar
  notwithstanding.
- 50 happy customers > 200 mediocre ones.
