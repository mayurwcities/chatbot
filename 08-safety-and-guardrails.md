# 08 · Safety and Guardrails

This stack is the product. Without it the first incident kills
reputation. With it, owners trust the chat enough to use it daily.

Ten layers. Build in order. Skip none.

## Layer 1 — Tool-level limits

Enforced by the executor, not the LLM.

| Limit | Default |
|---|---|
| Max entities affected per call | 5 (single-mutation tools); 1 (destructive) |
| Max bulk-send recipients without explicit confirm | 100 |
| Max price change delta per item without confirm | 25% |
| Max items deleted per session before forced break | 10 |
| Max LLM tokens per chat turn | 8,000 in / 2,000 out |
| Max consecutive tool iterations per turn | 8 |

Limits are **per-venue config with these safe defaults** (stored in
`venue_modules.config`), not hardcoded — a 200-seat venue legitimately
needs different bulk thresholds than a food truck. Changing a limit is
itself an audited, owner-only action.

Tool returns:

```json
{
  "ok": false,
  "error": "limit_exceeded",
  "limit": "bulk_recipients",
  "actual": 487,
  "max_without_confirm": 100,
  "next_action": "Request explicit user confirmation for large blast."
}
```

## Layer 2 — Confirmation prompts

Triggered by tool category, not LLM judgement.

| Action | Confirmation? |
|---|---|
| Read | Never |
| Single-item edit (non-destructive) | Never |
| Single-item destructive (delete, refund, cancel) | Always |
| Bulk edit (>5 items) | Always |
| Mass send (>100 recipients) | Always, with cost estimate |
| External API push (DoorDash, Square menu) | First time per venue, then opt-in |
| Multi-step plan (>3 tool calls) | Summary + confirm before executing |

Mechanism: tool's first call returns `{ status: 'confirmation_required',
token, summary, expires_in: 600 }`. LLM presents summary. User says yes
→ LLM re-calls with the token → executes. Tokens stored in
`confirmations` table with 10-minute TTL.

## Layer 3 — Audit log

Every mutation gets a row. No exceptions.

```sql
INSERT INTO audit_log (
  venue_id, actor_user_id, actor_kind,
  entity_type, entity_id, action,
  before_json, after_json,
  reason, reversible,
  ip, user_agent, created_at
) VALUES (...);
```

`reason` is the user's chat message that triggered it.

Use cases:
- "Who 86'd the lobster roll at 6 PM yesterday?"
- "What changed on the menu in the last 2 hours?"
- Customer dispute: price audit trail
- SOC 2: 30-day retention of all data mutations

## Layer 4 — Undo / version history

Each `audit_log` row stores `before_json` and `after_json`. A reverse
function for each tool reapplies `before_json`.

Owner can:

- Type "undo" → revert last action ("Undid: 86'd lobster roll → back on menu")
- Type "what changed today?" → audit feed
- View last 100 changes in dashboard, one-click revert
- See auto "Want to undo?" toast for 60 seconds after destructive actions

Daily snapshots of full venue state for catastrophic restore.

## Layer 5 — Sandbox / preview mode

Owner says "what would happen if I…" → orchestrator runs the tool with
`dry_run: true`, returns a diff, makes nothing.

Useful for:
- "What would happen if I deleted the lunch menu?"
- "Show me who'd receive the 15%-off email"
- "If I raised pizza prices 20%, what's the impact?"

Apply runs through normal confirmation flow.

## Layer 6 — Tiered permissions

| Role | Can do | Cannot do |
|---|---|---|
| **owner** | Everything including delete category, refund, mass send, integrations | n/a |
| **manager** | Daily ops, edit menu / hours, send to <200 recipients | Add/remove integrations, change pricing >50%, refunds >$200 |
| **staff** | Mark items 86'd, mark orders complete, view today's data | Edit menu, send marketing, view full customer PII |
| **viewer** | Read-only across enabled modules | Any mutation |

Per-permission overrides via JSON column for edge cases.

Executor checks permissions before running. LLM gets `{ error:
'permission_denied' }` and tells the user.

## Layer 7 — Rate limits per venue

| Limit | Default |
|---|---|
| Chat messages / minute | 30 |
| LLM tokens / hour | 100,000 |
| External API calls / day | 1,000 |
| Mass-send recipients / day | 5,000 |
| Adapter sync attempts / minute | 60 |

Hit → `{ error: 'rate_limited', retry_after_s: N }`. Owner sees clear
message.

Critical for cost control. Without these, a single misconfigured chat
could rack up $1k of LLM spend in an hour.

## Layer 8 — Adapter sync with rollback

When a tool modifies canonical AND pushes to N adapters:

- Canonical write commits first (always).
- Adapter pushes in parallel (`Promise.allSettled`).
- All succeed → success.
- Some succeed / some fail → log per-adapter status; queue retries.
- All fail → keep canonical change, mark `sync_state: 'all_failed'`,
  surface to owner.

Never rollback canonical because an adapter failed. Adapter failures are
recoverable.

Sync state badges:

| Badge | Meaning |
|---|---|
| `synced` | All active integrations have current value |
| `syncing` | At least one push in-flight |
| `partial_sync` | Some succeeded; retrying others |
| `sync_failed` | All failed; check `last_error` |

UI surfaces these.

## Layer 9 — Idempotency keys

Every tool call carries a UUID. Re-executing with the same key is a
no-op returning the original result.

Protects against:
- Network blips causing LLM retries
- Browser double-click on "Confirm"
- Re-running cron jobs

```sql
CREATE TABLE tool_calls (
  ...
  idempotency_key VARCHAR(64),
  UNIQUE KEY uniq_idempotency (idempotency_key)
);
```

## Layer 10 — Human-in-the-loop for high-stakes

Some actions require a second authentication factor.

| Action | Requires |
|---|---|
| Refund >$500 | Email confirmation link |
| Mass send >500 recipients | Email or SMS code |
| Connect new payment integration | Email confirmation |
| Delete entire venue | Email + 24-hour delay + cancellable |
| Bulk delete >20 catalog items | Email confirmation |
| Change owner email or password | SMS code + email notification |

Flow:

```
User: "Refund $1200 to customer Sarah"
Assistant: "That's above the in-chat limit. I've sent a confirmation link
            to owner@joesburgers.com — click it within 10 minutes."
[owner clicks link]
Assistant: "Refund authorized. Processing... done. Sarah notified."
```

Friction is the point.

## Layer composition

```
                      ┌────────────────────────────┐
                      │  Tool call requested       │
                      └──────────────┬─────────────┘
                                     ▼
                      ┌────────────────────────────┐
                      │  Idempotency check (L9)    │
                      └──────────────┬─────────────┘
                                     ▼
                      ┌────────────────────────────┐
                      │  Rate limit check (L7)     │
                      └──────────────┬─────────────┘
                                     ▼
                      ┌────────────────────────────┐
                      │  Permission check (L6)     │
                      └──────────────┬─────────────┘
                                     ▼
                      ┌────────────────────────────┐
                      │  Tool-level limit (L1)     │
                      └──────────────┬─────────────┘
                                     ▼
                      ┌────────────────────────────┐
                      │  Confirmation check (L2)   │
                      └──────────────┬─────────────┘
                                     ▼
                      ┌────────────────────────────┐
                      │  Step-up auth (L10)        │
                      └──────────────┬─────────────┘
                                     ▼
                      ┌────────────────────────────┐
                      │  Execute + audit (L3) +    │
                      │  before_json (L4)          │
                      └──────────────┬─────────────┘
                                     ▼
                      ┌────────────────────────────┐
                      │  Adapter fan-out (L8)      │
                      └──────────────┬─────────────┘
                                     ▼
                      ┌────────────────────────────┐
                      │  Return aggregate result   │
                      └────────────────────────────┘
```

## Failure mode catalog

| Without | Risk |
|---|---|
| L1 (limits) | "Update all prices" → set all to $0 |
| L2 (confirmation) | "Delete pizza category" wipes 12 items mid-service |
| L3 (audit) | Customer disputes a charge; no record |
| L4 (undo) | Mistakes are permanent |
| L5 (sandbox) | Owner is scared to try things |
| L6 (permissions) | Bartender wipes the menu |
| L7 (rate limit) | One venue runs up $500 LLM bill in an hour |
| L8 (sync rollback) | UI lies about external state |
| L9 (idempotency) | Double-charges, double-sends |
| L10 (step-up) | $5000 refund triggered by chatbot misunderstanding |

## What NOT to do

| Don't | Because |
|---|---|
| Rely on LLM prompt instructions for safety | Prompt injection bypasses them |
| Add confirmation to every tool call | Kills adoption |
| Skip safety for "trusted" power users | Power users make the worst mistakes |
| Make undo opt-in or paid | Trust signal too important to gatekeep |
| Let staff role do anything an owner can do | Permissions matrix is mandatory |
| Store credentials unencrypted | Breach liability |
| Use the same idempotency key across 24+ hours | Stale state. Per-day / per-session keys only |
| Allow chat access to system tables (users, billing, settings) | Out of scope. Admin UI only |
