# 07 · Integrations (Third-Party Adapters)

## Principle

For each third-party (Square, Toast, DoorDash, Booking.com, Eventbrite,
WordPress, Stripe, …), write **one adapter** that translates between our
canonical schema and the third-party's API. Every venue using that
third-party reuses the same adapter.

```
            ┌────────────────────────────────────┐
            │  Canonical data + orchestrator     │
            └─────────────────┬──────────────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │  Adapter interface    │
                  └─────┬────┬────┬───────┘
                        │    │    │
        ┌───────────────┘    │    └───────────────┐
        ▼                    ▼                    ▼
   ┌─────────┐         ┌──────────┐         ┌────────────┐
   │ Square  │         │ DoorDash │         │ Booking.com│
   │ adapter │         │ adapter  │         │  adapter   │
   └─────────┘         └──────────┘         └────────────┘
```

## Adapter categories

| Category | Examples | Common interface |
|---|---|---|
| `pos` | Square, Toast, Clover, Lightspeed | `pushMenu`, `pullOrders`, `setItemAvailability`, `getInventory` |
| `delivery` | DoorDash, Uber Eats, Grubhub, Caviar | `pushMenu`, `pullOrders`, `setHours`, `setItemAvailability` |
| `reservations` | OpenTable, Resy, Tock | `pullReservations`, `pushAvailability`, `cancelReservation` |
| `channel_manager` | Booking.com, Airbnb, Expedia | `pullBookings`, `pushAvailability`, `pushRates` |
| `ticketing` | Eventbrite, DICE, Ticketmaster | `createListing`, `pullSales`, `updateInventory` |
| `cms` | WordPress, Shopify | `pushPage`, `pushProduct`, `pullOrders` |
| `comms` | SendGrid, Mailgun, Postmark, Twilio | `sendEmail`, `sendSMS`, `getDeliveryStatus` |
| `payments` | Stripe, Square | `chargeCard`, `refund`, `linkAccount` |
| `discovery` | Google Business Profile, Yelp, Facebook | `pushHours`, `pushPhotos`, `pullReviews` |

## Shared contract

```typescript
interface Adapter {
  connect(credentials): Promise<{ ok: boolean; error?: string }>;
  disconnect(): Promise<void>;
  healthcheck(): Promise<{ ok: boolean; latencyMs?: number }>;

  pushMenu?(menu: CanonicalMenu): Promise<SyncResult>;
  pullOrders?(since: Date): Promise<CanonicalOrder[]>;
  setItemAvailability?(itemId: string, available: boolean): Promise<SyncResult>;
  setHours?(hours: CanonicalHours): Promise<SyncResult>;

  handleWebhook?(payload: any): Promise<CanonicalEvent[]>;
}

type SyncResult =
  | { ok: true; externalId?: string }
  | { ok: false; error: string; retryable: boolean };
```

## How a chat tool call fans out

When `setItemAvailability(itemId: 47, available: false)` runs:

```
1. Update canonical row:
   UPDATE catalog_items SET available = 0 WHERE id = 47;

2. Audit:
   INSERT INTO audit_log ...

3. Look up venue's active integrations:
   SELECT * FROM venue_integrations
    WHERE venue_id = X
      AND kind IN ('delivery', 'pos')
      AND status = 'active';

4. For each, call the adapter in parallel (Promise.allSettled):
   await Promise.allSettled([
     loadAdapter('doordash').setItemAvailability(external_id, false),
     loadAdapter('uber_eats').setItemAvailability(external_id, false),
     loadAdapter('square').setItemAvailability(external_id, false),
   ]);

5. Capture per-integration result:
   - ok → log success, update last_synced_at
   - failed retryable → enqueue retry
   - failed permanent → record error, surface to owner

6. Return aggregate result to LLM:
   {
     canonical: ok,
     adapters: {
       doordash: ok,
       uber_eats: ok,
       square:   { error: 'Item not mapped to Square id', retryable: false }
     }
   }
```

LLM reply: "Done. Lobster Roll 86'd on your menu, DoorDash, and Uber
Eats. Square doesn't have a link for this item yet — want me to help map
it?"

## ID mapping

Each adapter translates between **canonical IDs** and **external IDs**.
(Schema also listed in `04-data-model.md` — that file is the canonical
home for all DDL.)

```sql
CREATE TABLE integration_id_map (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  venue_id        BIGINT UNSIGNED NOT NULL,
  integration_id  BIGINT UNSIGNED NOT NULL,
  entity_type     VARCHAR(64) NOT NULL,
  canonical_id    BIGINT UNSIGNED NOT NULL,
  external_id     VARCHAR(255) NOT NULL,
  mapped_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_canonical (integration_id, entity_type, canonical_id),
  UNIQUE KEY uniq_external  (integration_id, entity_type, external_id),
  INDEX idx_venue (venue_id)
);
```

## Sync strategies

### Push-only (we're the source of truth)

For third-parties that don't have data of their own (DoorDash menus
mirror what we send).

- We mutate canonical → adapter pushes.
- Inbound: nothing (or only order events).

### Bidirectional with conflict resolution

For POS systems (Square, Toast) where the owner may edit on the terminal
during service.

- We mutate canonical → adapter pushes.
- Every 5–15 min the adapter pulls third-party state.
- Compare:
  - Our `updated_at` > theirs → push again.
  - Theirs > ours → update canonical, notify owner.
  - Both changed since last sync → conflict; surface in chat ("price for X is $10 on Square but $12 here — which is right?").

### Webhook-driven (event-time)

For order events (new DoorDash order → webhook → us in seconds).

- Adapter exposes a webhook endpoint per integration.
- Third-party signs payloads; we verify.
- Inbound events become canonical changes immediately.

## Priority order

US-focused, for restaurant V1:

1. **Hosted page only** — Month 1
2. **DoorDash** — Month 5–7. Certification adds months; start early.
3. **Square POS** — Month 8–9.
4. **Uber Eats** — Month 10–11.
5. **Toast POS** — Month 12.
6. **OpenTable** — Month 13.
7. **Grubhub** — Month 14+.
8. **WordPress plugin** — Month 14+.

Each integration is 2–4 months end to end:

- API discovery + auth flow (1–2 weeks)
- Core push/pull methods (3–4 weeks)
- Edge cases + error handling (2–3 weeks)
- Webhook handling (1–2 weeks)
- Certification if required (1–3 months parallel)
- Onboarding flow (1–2 weeks)
- Docs (1 week)

"Two integrations this quarter" is realistic. "Five this year" is
achievable. "Every major platform by month 6" is not.

## OAuth flow

Most platforms support OAuth:

1. Owner clicks "Connect Square" in admin.
2. Redirect to provider's consent screen.
3. Owner approves scopes.
4. Provider redirects back with auth code.
5. Exchange code for access + refresh token.
6. Store encrypted in `venue_integrations.credentials_encrypted`.
7. Schedule initial pull.

For platforms without OAuth, fall back to API key entry.

**Never store passwords.** Use a vault (AWS Secrets Manager / Doppler).

## Failure handling

### Per-call retry

- HTTP 5xx → exponential backoff, up to 5 attempts
- HTTP 429 → respect `Retry-After`, queue
- HTTP 401 → mark integration `error`, prompt owner to reconnect
- HTTP 4xx → don't retry; surface
- Timeout → retry once, then surface

### Per-venue degradation

If an adapter fails repeatedly for one venue, mark `status = 'error'` and
surface in chat: "DoorDash hasn't been syncing for 3 hours. Tap to
reconnect."

### Per-platform circuit breaker

If an entire provider has 20%+ error rate in 5 min, pause new calls and
queue them. Resume on recovery.

## "No integrations" mode (default)

A venue can run with zero integrations:

- Sign up → hosted page at `yourplatform.com/v/their-slug`
- Manage via chat
- Customers find them via Google / Instagram / QR codes
- Orders come through hosted page
- Marketing via comms provider
- CRM builds up

This is the **default**. ~30% of small venues will stay here permanently.

## What NOT to do

| Don't | Because |
|---|---|
| Build a "universal connector" that adapts via config | Each integration has quirks; explicit code per provider is cheaper long-term |
| Sync everything in real time | Some can be batched; some can't. Pick per-operation |
| Let one integration block other syncs | `Promise.allSettled`, never `Promise.all` |
| Block chat reply on integration sync | Sync is async (job queue); chat returns on canonical commit |
| Store unencrypted credentials | Secrets manager, encryption at rest |
| Skip audit for adapter calls | Every push and pull is an audit row |
| Hand-roll OAuth | Use a library (`openid-client`, Passport adapters) |
