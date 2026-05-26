# 12 · Decisions Now vs Later

A living document. Update as decisions get locked or deferred.

## Lock NOW (before any code)

These ripple through the architecture.

| Decision | Default | Status |
|---|---|---|
| **Starting vertical** | Restaurants | DEFAULT |
| **Starting LLM provider** | Claude Sonnet 4.6 (Anthropic) | DEFAULT |
| **Canonical schema** | See `04-data-model.md` | DEFAULT |
| **Safety stack from Day 1** | All 10 layers | LOCKED |
| **Audit log + undo in the first tool** | Yes | LOCKED |
| **Hosted page vs widget for V1** | Both; hosted page default | DEFAULT |
| **Tech stack** | Next.js + Node + TypeScript + MySQL + Redis + Vercel + AWS RDS | DEFAULT |
| **Multi-tenant strategy** | Single DB, row-level `venue_id` filtering | DEFAULT |
| **Auth** | NextAuth.js with email + magic link | DEFAULT |
| **Pricing model** | Tiered SaaS (free / $79 / $149 / $249), not transactional | DEFAULT |
| **Customer success approach** | Founder-led hand-holding for first 10 | LOCKED |
| **First geographic market** | US (English) | DEFAULT |

Notes:

- Hotels and tours come in Phase 4–5. Restaurants give the cleanest
  learning loop.
- Build provider abstraction so an LLM swap is a week, not months.
- Multi-tenant via `venue_id`; multi-vertical via modules + JSON
  `attributes`. Lock before writing tool layer code.
- DB-per-tenant adds operational complexity not justified at <1000
  venues.

## Decide WITHIN 30 DAYS

| Decision | Options | Recommendation |
|---|---|---|
| Incorporation jurisdiction | Delaware C-corp, LLC, foreign | Delaware C-corp if fundraising; LLC if bootstrapping longer |
| Bank + payments | Mercury / Brex / SVB-alt + Stripe | Mercury + Stripe for early-stage SaaS |
| Cyber insurance carrier | At-Bay, Coalition, Embroker | Quote 3, pick lowest for $1M coverage |
| Database: MySQL or Postgres | Both work | Postgres for better JSON + row-level security |
| Email provider | SendGrid, Mailgun, Postmark | Postmark for transactional reliability; SendGrid for bulk |
| TOS + privacy policy | Counsel or Stripe Atlas templates | Templates if <$1M raised; counsel once revenue justifies |
| Logo + brand | DIY or designer | $1–3k for a designer, before customer #11 |
| Domain name | TBD | Lock before signup page goes live |

## Decide BEFORE PHASE 2

| Decision | Notes |
|---|---|
| DoorDash partner agreement signing party | The named entity holding the partnership |
| OAuth provider library | `openid-client` library vs Auth0 SaaS — lean library |
| Secrets manager | AWS Secrets Manager / Doppler / 1Password Connect — Doppler most DX-friendly |
| Webhook signing verification pattern | Lock early so adapters share helpers |

## DEFER

| Question | Defer to |
|---|---|
| Voice (Twilio call to bot) | Year 2 |
| Mobile app (native iOS/Android) | Year 2 |
| Fine-tuning own model | 1,000+ chat transcripts collected (Year 2 minimum) |
| Custom CMS integrations beyond WordPress | When a customer asks |
| Multi-location chains | First 50 customers nailed (Year 2) |
| International + multi-currency | First market dominated |
| Marketplace (venues finding venues) | Network effect doesn't exist yet |
| White-label / reseller | Year 2 |
| WhatsApp / Telegram interface | Phase 6+ |
| Sub-vertical specialisation (e.g. "for wine bars") | After 50+ generic restaurants on board |
| Built-in analytics dashboards beyond chat | Phase 6+ |
| Loyalty / rewards | Late Phase 6 |
| Native POS replacement | Never |
| Live customer support chat (you ↔ owner) | Email-first SLA at launch |
| AI image generation for menu photos | Late Year 2 |
| Public REST API for third-party developers | Phase 6 / Year 2 |
| Custom-trained vision model for menu OCR | Year 2 — Claude / GPT-4 multimodal handles V1 |

## Log of locked decisions

| Date | Decision | Rationale |
|---|---|---|
| | | |

## Log of overturned decisions

| Date | What changed | Why |
|---|---|---|
| | | |

## How to use this document

- Before any non-trivial feature work, check whether the question is in
  "Lock NOW" or "Defer."
- If it's in "Defer" and someone wants to build it, push back.
- If a "Lock NOW" decision needs revisiting, add to overturned log with
  rationale.
- Review monthly with the team.
