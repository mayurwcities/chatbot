# Email to Manager — Venue Chatbot Platform

---

**Subject:** Venue chatbot platform — what's buildable and what isn't

Hi [Manager],

I've spent time mapping out the venue chatbot idea end to end. Below is a
direct read on what we can build, what we can't, and what it will
realistically take. I want us aligned on this before any engineering
starts.

## What we CAN build

1. **Chat-controlled venue management as a SaaS.** Owners of restaurants,
   hotels, tour operators, and retail shops manage their operations
   (menus, hours, rooms, tickets, customer marketing) by talking to an
   AI assistant. The platform is the canonical source of truth.

2. **Multi-vertical via modules.** One codebase serves restaurants
   first, then hotels, tours, retail. Each vertical adds modules. The
   backbone (chat orchestrator, safety stack, customers, orders,
   marketing, hours) is universal.

3. **Outputs to wherever the venue's data needs to appear.**
   - A hosted page for venues without a website (`yourplatform.com/v/{slug}`).
   - A JS widget for venues with an existing site (WordPress,
     Squarespace, Wix, custom HTML — one script tag).
   - Adapter integrations to third-party platforms (DoorDash, Uber
     Eats, Square, Toast, Booking.com, Eventbrite, etc.). One adapter
     per provider, reused across every customer on that provider.
   - Email + SMS to the venue's own customers.

4. **A safety stack that prevents the chatbot from breaking a customer's
   business.** Ten layers: tool-level limits, confirmation prompts for
   destructive actions, audit log of every change, undo / version
   history, sandbox preview mode, tiered permissions, rate limits,
   adapter sync with rollback, idempotency keys, step-up auth for
   high-stakes actions (refunds over $500, mass sends over 500
   recipients, etc.).

5. **Reliable LLM tool use.** We rent intelligence from Anthropic
   (Claude Sonnet 4.6) or OpenAI (GPT-4o) via API. Their structured
   function-calling now executes the right action ~95% of the time. Cost
   per active venue lands at $9–35/month depending on caching, against
   $79–249/month subscription pricing.

## What we CANNOT build (and shouldn't pretend to)

1. **"Plug in any venue's existing website and edit it via AI."** This
   is an unsolved research problem. Websites are not databases — to
   change a venue's site, you need to change the system that generates
   it (CMS plugin, custom code, or static rebuild). Browser-using AI
   agents that click around a site are demos, not products. Trying to
   build this would burn 12+ months for nothing shippable and the trust
   story is a non-starter (no venue will let an AI log into their CMS
   and click around unattended).

   **What we do instead:** the chatbot edits OUR database. Data
   publishes outward via the widget, the hosted page, and per-platform
   adapter integrations. The owner's experience is the same; the
   implementation is buildable.

2. **A custom-trained LLM.** $10M–$100M+ in compute, 10–20 ML
   researchers, 12+ months minimum, and we'd be behind whatever
   Anthropic / OpenAI / Google released that week. Our moat is
   integrations + UX + workflow, not model weights.

3. **All verticals at launch (restaurants + hotels + tours + retail
   simultaneously).** The data model alone is months of design work
   if we try to handle all of them up front. Restaurants first, then
   one vertical at a time.

4. **Five third-party integrations in parallel.** Each integration is
   2–4 months end to end (API discovery, OAuth flow, push/pull methods,
   webhook handling, certification if required, onboarding flow, docs).
   "Ship two this quarter" is realistic. "Ship every major platform by
   month 6" is not.

5. **Self-serve onboarding from Day 1.** Real small-venue owners need
   handholding. They'll quit at the first error. We hand-onboard the
   first 10 customers personally, learn what to automate, then build
   self-serve in Phase 6.

6. **"The AI handles everything" with no friction.** LLMs hallucinate.
   Every destructive / bulk / costly action goes behind a confirmation
   prompt. The safety stack IS the product — without it, the first
   incident (chatbot wipes a menu mid-service, refunds the wrong
   customer, sends a promo to the wrong list) kills our reputation
   immediately.

7. **Voice, WhatsApp, mobile app, all on Day 1.** Web chat first.
   Other channels in Year 2.

8. **DoorDash / Uber Eats / Square / Toast simultaneously.** DoorDash
   certification alone takes several months. We sequence: DoorDash,
   then Square, then Uber Eats, then Toast.

## Realistic timeline

This is a greenfield build — no shared infrastructure with any existing
project. Roughly 18 months to a credible V1 with a 4-person team
(2 backend, 1 frontend, founder/PM, half-time designer).

| Phase | Months | Goal |
|---|---|---|
| 0 | 1–3 | Chat + safety + hosted page for restaurants. No integrations. 5 paying customers. |
| 1 | 4–6 | Marketing module + customer CRM. 5–10 customers. |
| 2 | 7–10 | First integration: DoorDash. 10–15 customers. |
| 3 | 8–10 (parallel) | JS widget for existing sites. |
| 4 | 11–13 | Square POS + hotels vertical. 25–40 customers. |
| 5 | 14–15 | Tickets vertical (tour operators, theaters). 40–50 customers. |
| 6 | 16–18 | Self-serve onboarding + Uber Eats + Toast + SOC 2. 50–100 customers. |

End state at ~18 months: working multi-vertical platform, $40k+ MRR,
ready for Series A.

## Realistic budget

Year 1: **~$1M–$1.5M** all-in (4 FTE engineering, founder/PM, designer
contract, LLM API, hosting, observability, legal, insurance, optional
SOC 2). Year 2 typically 1.5–2x with added hires and growing infra.

Revenue trajectory (conservative): 5 paying customers by Month 3, 25 by
Month 10, 50–100 by Month 18, ~200 by Month 24. Cash-flow positive
around Month 30–36 depending on burn discipline.

Funding plan: bootstrap → friends-and-family ($300–600k by Month 3) →
seed ($1.5–3M by Month 12) → Series A ($5–10M by Month 20–24).

## What I need from you

To move forward I need agreement on three things:

1. **We don't promise customers we'll "edit their existing website."**
   We position as: "the chat is your control panel; your data shows up
   on your existing site via our widget, or on a hosted page we
   generate, or on DoorDash / Uber Eats / etc. via integrations."

2. **We sequence verticals and integrations.** Restaurants first.
   DoorDash before Square. No parallel integration builds. No multi-
   vertical at launch.

3. **The safety stack ships with V1.** Not later. The 10 layers go in
   from the first tool call. This is non-negotiable — skipping it to
   "ship faster" ends the product on the first incident.

If we're aligned on those, the plan is buildable on the timeline and
budget above. If we want to change any of them, I want to talk through
the tradeoffs before committing engineering time.

The full design is documented in 12 design docs in this folder
(`/Users/wcities/ReactStudy/chatbot`). Happy to walk through any
specific section in person.

Thanks,
[Your name]
