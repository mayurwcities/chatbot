# 01 · Vision

## Pitch

A chat-controlled venue management system. Owners run their restaurant,
hotel, tour company, or retail shop by talking to an AI assistant that
handles menu edits, hours, rooms, tickets, customer marketing, and
third-party platform sync.

## What it replaces

A typical small-venue owner currently juggles:

- A POS (Square, Toast, Clover)
- A website (Squarespace, Wix, custom)
- DoorDash / Uber Eats / Grubhub merchant dashboards
- A reservation tool (OpenTable, Resy, or paper)
- An email tool (Mailchimp / Klaviyo)
- Instagram for marketing
- Google Business Profile
- A ticketing tool if they host events

Eight admin panels. Each change has to be propagated by hand. Most venues
skip half of them.

Our pitch: **one chat window. Everything else syncs from there.**

## What it is NOT

| Not this | Reason |
|---|---|
| An AI that edits arbitrary external websites | Unsolved research problem. Browser-using agents are demos. |
| A POS replacement | Square, Toast, Clover are entrenched. We are the chat layer above them. |
| A custom-trained LLM | $10M+ compute, beaten by frontier providers immediately. We rent intelligence. |
| A single schema for every vertical | Modules + JSON attributes handle this. |
| A do-everything platform from day one | Restaurants first. Expand vertical by vertical. |

## Who it's for

**Primary customer (V1):** independent small restaurants, 1–3 locations,
US-based, $200k–$5M annual revenue, owner-operated, 1–20 staff.

These owners are time-poor, tech-frustrated, mobile-first, and will pay
$50–200/mo for software that saves them hours.

**Later verticals:**

- Independent hotels / B&Bs (Phase 4)
- Tour operators / experience providers / escape rooms (Phase 5)
- Small retail (Phase 6+)

## Why now

Three things are true in 2026 that weren't true three years ago:

1. **LLM tool use is reliable.** Structured function calling executes the
   correct action ~95% of the time.
2. **Multimodal models read photos.** Onboarding is now 5 minutes of
   chat, not 8 hours of form-filling.
3. **Third-party APIs have matured.** DoorDash, Uber Eats, Square, Toast,
   Booking.com, Airbnb, Eventbrite all have stable merchant APIs.

## Success criteria (12 months)

- 50+ paying venue customers
- 80%+ daily active rate
- $40k+ MRR
- < 1 destructive-action incident per month
- 3 verticals live (restaurants, hotels, tour operators)
- 2 third-party integrations live

If these are hit, the Series A story is credible. The safety stack and
chat orchestrator quality are the most likely gaps.
