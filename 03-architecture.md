# 03 · Architecture

## The architectural insight

Most B2B SaaS is "an admin UI on top of a database." This is "a chat
orchestrator on top of a database, with multiple input and output
channels."

```
                  ┌──────────────────────────────────┐
                  │   PLATFORM (Brain)               │
                  │                                  │
                  │   ▸ Canonical venue data         │
                  │   ▸ Chat orchestrator + LLM      │
                  │   ▸ Module registry              │
                  │   ▸ Customer / order CRM         │
                  │   ▸ Marketing engine             │
                  │   ▸ Safety stack                 │
                  │   ▸ Adapter layer                │
                  └──────┬───────────────────────┬──┘
                         │                       │
        ┌────────────────┘                       └─────────────────┐
        ▼                                                           ▼
   INPUT CHANNELS                                            OUTPUT CHANNELS

  ▸ Web chat (dashboard)                              ▸ Our hosted page
  ▸ WhatsApp / Telegram (later)                       ▸ Widget on existing site
  ▸ Voice via Twilio (later)                          ▸ DoorDash / Uber Eats
  ▸ Mobile app (later)                                ▸ Booking.com (hotels)
  ▸ Email-to-bot (later)                              ▸ Eventbrite (tickets)
                                                      ▸ Google Business Profile
                                                      ▸ Customer SMS (Twilio)
                                                      ▸ Customer email (provider)
                                                      ▸ POS (Square, Toast)
```

## Five subsystems

### 1. Canonical data layer

Single MySQL or Postgres database holding source of truth per venue.
Multi-tenant via `venue_id` on every row. Multi-vertical via per-module
tables + JSON `attributes`. See `04-data-model.md`.

Table groups:

- **Venue core**: `venues`, `venue_users`, `venue_modules`
- **Catalog**: `catalog_items`, `catalog_categories`, `catalog_modifiers`
- **Vertical extensions**: `rooms`, `tours`, `events`, `inventory_units`
- **Customers + orders**: `customers`, `orders`, `order_items`, `payments`
- **Marketing**: `campaigns`, `campaign_recipients`, `campaign_tracking`,
  `email_templates`
- **Integrations**: `venue_integrations`, `integration_sync_log`
- **Safety**: `audit_log`, `tool_calls`, `chat_messages`, `confirmations`

### 2. Chat orchestrator

Takes a user message, decides what to do, executes tool calls, returns a
reply. Node.js service calling the LLM with structured tool definitions.
See `05-chat-orchestrator.md`.

```
user message
   ↓
load venue context (type, enabled modules, attribute schema, integrations,
                    recent messages, recent business state)
   ↓
build tools array — only those for venue's enabled modules
   ↓
call LLM with system prompt + tools + context + message
   ↓
loop:
  if LLM returns tool_calls:
    apply safety guardrails (confirm? rate limit? permission?)
    execute via tool layer
    feed results back to LLM
  else:
    LLM has produced final reply
    break
   ↓
persist conversation + every tool_call → audit_log
   ↓
return reply to user
```

### 3. Module + tool registry

Central declaration of every tool the LLM can call, scoped to its module.
The orchestrator consults this to assemble per-venue tool lists. See
`06-multi-vertical-modules.md`.

```
modules:
  menu:
    enabledFor: [restaurant, cafe, bar, hotel_restaurant]
    tools:
      - addMenuItem(name, basePrice?, category, attributes?)
      - updateMenuItem(itemId, fields)
      - setItemAvailability(itemId, available)
      - addCategory(name)
      - listMenu()
  rooms:
    enabledFor: [hotel, b&b]
    tools:
      - setRoomStatus(roomId, status)
      - setRoomRate(roomId, rate, dateRange?)
      - blockDates(roomId, dateRange)
  tickets:
    enabledFor: [tour_operator, theater, escape_room, concert_venue]
    tools:
      - createTour(...)
      - setTourSaleState(tourId, state)
      - addTicketTier(...)
  marketing:
    enabledFor: '*'
    tools:
      - searchCustomers(filter)
      - sendCampaign(segment, channel, template)
      - previewCampaign(...)
```

### 4. Adapter layer

One module per third-party platform translating between canonical schema
and the provider's API. Shared interface; provider-specific implementation.
See `07-integrations.md`.

```
adapters/
  pos/
    square.js
    toast.js
    clover.js
  delivery/
    doordash.js
    uber_eats.js
    grubhub.js
  reservations/
    opentable.js
  hotel_channel/
    booking_com.js
    airbnb.js
  ticketing/
    eventbrite.js
  cms/
    wordpress.js
    shopify.js
  comms/
    email_provider.js
    twilio.js
```

When a tool call modifies canonical state, the orchestrator looks up the
venue's active integrations and fans out via adapters in parallel.

### 5. Safety stack

Cross-cutting. Wraps every tool call. See `08-safety-and-guardrails.md`:

1. Tool-level limits
2. Confirmation prompts
3. Audit log
4. Undo / version history
5. Sandbox / preview mode
6. Tiered permissions
7. Rate limits per venue
8. Adapter sync with rollback
9. Idempotency keys
10. Human-in-the-loop for high-stakes

## Request flow — concrete example

Owner types: *"Mark the lobster roll as 86'd"*

```
1. Load venue context:
   type = restaurant
   modules = [menu, hours, marketing, orders]
   integrations = [pos=square, delivery=[doordash, ubereats]]
   recent menu items (so LLM can fuzzy-match "lobster roll")

2. Build tools for venue's enabled modules:
   [updateMenuItem, setItemAvailability, setHours,
    searchCustomers, sendCampaign, ...]

3. Call Claude with system prompt + tools + context + message

4. Claude returns:
   tool_call: setItemAvailability(itemId: 47, available: false)

5. Safety guardrails:
   - Single item, non-destructive → no confirmation
   - User has permission (owner role)
   - Within rate limit
   → proceed

6. Tool executor:
   a. UPDATE catalog_items SET available=0 WHERE id=47
   b. INSERT INTO audit_log
   c. Lookup venue_integrations of kind delivery/pos
   d. Parallel fan-out via adapters; await all

7. Tool result back to Claude:
   { ok: true, canonical: ok,
     doordash: ok, ubereats: failed (retrying) }

8. Claude generates final reply:
   "Done. Lobster Roll marked 86'd on your menu and DoorDash.
    Uber Eats push failed — I'll retry and let you know."

9. Persist conversation, tool_calls, audit_log rows
```

## Why this architecture survives growth

- **New vertical** (e.g. spa): add a `spa` module with new tools and
  tables. Existing modules untouched.
- **New integration** (e.g. Grubhub): write `adapters/delivery/grubhub.js`,
  add a row to `venue_integrations` per venue.
- **New LLM**: swap the provider call. Tools and prompts mostly unchanged.
- **New input channel**: channel adapter normalises into the same
  orchestrator input.
- **Scale**: shard by `venue_id`.

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | Next.js + Tailwind |
| API / orchestrator | Next.js API routes or standalone Node service |
| LLM | Claude Sonnet 4.6 via Anthropic API |
| DB | MySQL 8 or Postgres 16 |
| Queue | BullMQ + Redis |
| Email | SMTP provider (SendGrid / Mailgun / Postmark) |
| SMS | Twilio |
| Payments | Stripe |
| Hosting | Vercel + AWS RDS |
| Observability | Sentry + log dashboard |
| Auth | NextAuth.js |

Anything beyond — Kafka, Kubernetes, custom service mesh, GraphQL
federation — is over-engineering for year-1 scale.

## Anti-patterns

| Anti-pattern | Why we avoid it |
|---|---|
| Let the LLM write SQL directly | Injection risk; no audit story |
| Let the LLM call third-party APIs directly | No safety, no audit, breaks rate-limit accounting |
| "Generic" tool that takes JSON and modifies anything | LLM can't reason about it; safety gating impossible |
| Per-venue database (DB-per-tenant) | Operational nightmare at 100+ venues |
| Event sourcing / CQRS | Premature |
| Microservices | Monolith with clear modules first |
