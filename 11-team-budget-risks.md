# 11 · Team, Budget, Risks

## Team

To execute the 18-month roadmap:

| Role | Count | Notes |
|---|---|---|
| Backend engineer | 2 | Core platform, chat orchestrator, tool layer, adapters |
| Frontend engineer | 1 | Admin dashboard, hosted page, widget, embed bundle |
| Designer | 0.5 | Brand, page templates, widget themes — contract OK |
| Founder / PM | 1 | Sales, onboarding, support, product decisions |
| Ops / DevOps | 0.5 (later) | Infra hardening, SOC 2 prep, on-call |

Total: ~4 FTE-equivalents.

### Ownership

**Backend Engineer #1 — Core platform**
- Canonical DB schema + migrations
- Chat orchestrator
- Safety stack
- Multi-tenant security
- Tool layer (per-module tools)
- Audit + undo + version history

**Backend Engineer #2 — Integrations + sync**
- Adapter pattern + interface
- DoorDash, Square, Uber Eats, Toast (one at a time)
- Webhook handlers
- Sync queue + retries
- ID mapping infrastructure

**Frontend Engineer — Owner UX + public pages**
- Onboarding flow
- Owner dashboard (chat + side panels)
- Hosted venue page
- Widget bundle
- Per-venue customisation tooling

**Designer (part-time)** — Brand, themes, marketing site, templates

**Founder / PM** — Sales (first 50 customers personally), onboarding,
support, roadmap, fundraising, partnerships

**Ops (later)** — Month 10 onwards: monitoring, alerting, SOC 2,
security questionnaires, scaling

### Hiring timeline

| Hire | When |
|---|---|
| 4 founding engineers + PM | Day 0 |
| Designer (contract) | Month 1 |
| Second frontend engineer | Month 10 |
| Customer success / support | Month 12 |
| Ops / DevOps | Month 14 |
| Sales hire #1 | Month 16 |
| ML engineer | Year 2 |

## Budget

### Run-rate (US/Canada team)

| Line | Monthly | Annual |
|---|---|---|
| 4 founding engineers @ $12k–$18k loaded | $48k–$72k | $580k–$870k |
| Founder/PM @ $12k loaded | $12k | $144k |
| Designer contract (0.5 FTE) | $4k | $48k |
| Office + tools + perks | $3k | $36k |
| LLM API | $300 → $5k as venues grow | $20k–$50k |
| Email / SMS / Stripe fees | $200–500 | $5k–10k |
| Hosting (Vercel + AWS) | $500–2k | $10k–25k |
| Domain, SSL, misc SaaS | $300 | $4k |
| Sentry + observability | $200 | $3k |
| **Subtotal** | **~$70k–$95k/month** | **~$850k–$1.2M/year** |
| SOC 2 audit (Year 1) | one-time | $40k–$80k |
| Cyber insurance ($1–5M policy) | $500–1.5k | $6k–18k |
| Legal (TOS, privacy, contracts) | $1–3k | $15k–35k |
| Pen test (annual) | $5k–15k | $5k–15k |
| **Year 1 total** | | **~$1M–1.5M** |

Year 2 typically 1.5–2x with one or two added hires and growing infra.

### Revenue model

| Tier | Price/month | Includes | Target |
|---|---|---|---|
| Starter | Free | Hosted page only, 100-customer limit | Tiny venues testing |
| Standard | $79 | + Marketing + 5k customer cap | Solo / small restaurants |
| Pro | $149 | + 1 integration (DoorDash OR Square OR Uber Eats) + 25k customers | Growing restaurants |
| Pro+ | $249 | + Unlimited integrations | Multi-channel restaurants |
| Hotel | $299 | Rooms + 1 channel manager (Booking.com / Airbnb) | Independent hotels / B&Bs |
| Tour Operator | $199 | Tickets + Eventbrite + Stripe payments | Tour / experience providers |
| Enterprise | custom ($1k+) | Multi-location, SSO, custom integrations, CSM | Chains, larger venues |

### Revenue trajectory (conservative)

| Month | Paying customers | ARPU | MRR |
|---|---|---|---|
| 3 | 5 | $79 | $395 |
| 6 | 10 | $85 | $850 |
| 10 | 25 | $100 | $2,500 |
| 13 | 40 | $135 | $5,400 |
| 15 | 50 | $160 | $8,000 |
| 18 | 75–100 | $175 | $13k–17k |
| 24 | 200 | $190 | $38k |
| 30 | 350 | $200 | $70k |

Cash-flow positive: month 30–36, depending on burn discipline.

### Funding

- **Bootstrap**: months 1–3, $50–100k founder capital
- **Pre-seed / friends-family**: $300–600k by Month 3
- **Seed**: $1.5–3M by Month 12 (with 25+ paying customers)
- **Series A**: $5–10M by Month 20–24 (with $20k+ MRR + multi-vertical
  proof)

## Risk register

Ordered by combined (likelihood × impact).

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Chatbot wipes a menu / sends wrong promo / refunds wrong amount | HIGH | CATASTROPHIC | All 10 safety layers by end of Phase 1. Founder-led incident response. Public post-mortem on first incident |
| DoorDash certification rejected or takes 9+ months | MEDIUM | High | Don't put DoorDash on the gating critical path. Sell manual mode first |
| LLM costs spike (one venue runs up $500 in a day) | MEDIUM | Medium | Per-venue rate limits + cost dashboards + alerts at $50/day/venue |
| Competing with Toast, Square, Shopify | HIGH | Existential | Position as chat layer ABOVE their POS, not a replacement |
| Bad sync to DoorDash → wrong price | MEDIUM | High | Sync confirmation for first 30 days per venue; opt-in to "auto-push after" |
| Owner can't figure out the chat | HIGH (without onboarding) | High | Hand-onboard first 10. Every "I don't know how to do X" becomes a tool, prompt, or help doc |
| Building 6 modules but each mediocre | MEDIUM | High | Cut scope. One excellent module > six okay ones |
| Engineer burnout / single point of failure | MEDIUM | High | No on-call rotation Year 1 (small team) → founder takes pages. Document everything |
| Manager pushes for "edit any website" / "direct DB access" / "store nothing, just use APIs" version | HIGH | High | Reference `02-what-works-vs-what-doesnt.md` and `MANAGER_BRIEF.md` (has the where-it-breaks examples). Push back politely |
| LLM provider outage | LOW | High | Fallback provider configured. Cached system prompt + tool defs |
| GDPR / privacy lawsuit | LOW | High | Don't collect more PII than needed. Consent at every collection point |
| Data breach | LOW (Year 1) | Catastrophic | Encrypt at rest. OAuth not passwords. SOC 2 within 12 months. Cyber insurance from Month 1 |
| One large customer demands custom dev | MEDIUM | Medium | Decline or price prohibitively |
| Adapter API changes break sync silently | MEDIUM | Medium | Healthchecks per adapter hourly; alert on >5% error rate |
| Cyberattack on tenant data | LOW | Catastrophic | Per-venue isolation at data layer; annual pen-test; secrets rotation |
| Acquisition offer too early | LOW | Medium | Have a "minimum viable acquisition price" set up front |
| Founder disagreement on direction | MEDIUM | High | Document key decisions; review monthly |

## Operational practices

### Engineering

- PR review by 1+ peer for every merge. No solo commits to main.
- Migrations versioned. Add column → backfill → release. Drop column →
  wait one release → release.
- Destructive tool calls require confirmation by integration test, not
  by trust.
- Audit log queries reviewed weekly for anomalies.
- Cost dashboard reviewed daily for the first 6 months.

### Customers

- Founder handles first 10 customers personally.
- 30-minute weekly sync per customer for first 30 days post-launch.
- Public changelog of what shipped each week.
- Incident report within 48 hours of any data-touching bug, however
  small.

### Decision-making

- Defaults in `12-decisions-now-vs-later.md` override discussions until
  a new compelling argument arises.
- One stakeholder owns each major decision.
- Monthly retros, quarterly OKR reviews.

## Hiring traps

| Trap | Avoid by |
|---|---|
| Senior IC engineers who want to architect grand systems | Hire for execution. Stack is conventional |
| "Head of AI" Day 1 | LLM use is standard tool-use API. No research lead needed until Year 2 |
| "Head of sales" Day 1 | Founder sells the first 50. Then hire for SMB inbound |
| Hiring for hypothetical future scale | At 50 venues you don't need someone who can scale to 100k |
| Hiring without role clarity | Each role above has clear ownership. Don't add ambiguous "engineer" hires |

## What success looks like at Month 18

- 50+ paying venues across restaurants, hotels, tour operators
- $40k MRR, ~$500k ARR run-rate
- < 1 destructive-action incident per month
- 80%+ DAU
- 30%+ self-serve sign-up conversion
- 3+ working integrations (DoorDash, Square, Uber Eats minimum)
- SOC 2 Type I audit in progress
- 4–6 person team
- Series A pitch ready

What success does NOT look like at Month 18:

- 1000 paying customers (premature scale)
- 10 integrations (most mediocre)
- Voice + mobile + WhatsApp on top of everything
- 4 verticals all halfway done

Tighter beats bigger.
