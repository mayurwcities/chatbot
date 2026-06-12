# 05 · Chat Orchestrator

Takes a user message, decides what to do, executes tool calls, returns a
reply. Most of the engineering value lives here.

## Agent loop pattern

Industry-standard "LLM with tool use." Anthropic (`tool_use`), OpenAI
(function calling), Google (Gemini tool use) all support it.

```
                  ┌──────────────────────────────┐
                  │ User message comes in        │
                  └──────────────┬───────────────┘
                                 ▼
              ┌──────────────────────────────────────┐
              │ Load session context                 │
              │   - Venue: id, type, modules         │
              │   - User: id, role, permissions      │
              │   - Conversation: recent messages    │
              │   - Business state: live snapshots   │
              │   - Tool definitions: per-module     │
              │   - Confirmation queue               │
              └──────────────┬───────────────────────┘
                             ▼
              ┌──────────────────────────────────────┐
              │ Build prompt:                        │
              │   system + context + tools +         │
              │   conversation + message             │
              └──────────────┬───────────────────────┘
                             ▼
              ┌──────────────────────────────────────┐
              │ Call LLM                             │
              └──────────────┬───────────────────────┘
                             ▼
              ┌──────────────────────────────────────┐
              │ Did LLM call tools?                  │
              └────────┬─────────────────┬───────────┘
                       │ Yes             │ No
                       ▼                 ▼
              ┌────────────────┐  ┌──────────────────┐
              │ For each call: │  │ Final reply →    │
              │   guardrails   │  │ return to user   │
              │   execute      │  └──────────────────┘
              │   capture      │
              │   result       │
              └────────┬───────┘
                       ▼
              ┌──────────────────────────────────────┐
              │ Feed tool results back to LLM        │
              └──────────────┬───────────────────────┘
                             ▼
                      (loop back to "Call LLM")
                      max N iterations
```

Iteration cap: 5–10 per turn. More usually means broken prompt or tools.

## Five pieces of every prompt

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. SYSTEM PROMPT (static per venue type, customised per venue)  │
│                                                                  │
│ "You're an assistant for Joe's Burgers, a restaurant in NYC.    │
│  Help the owner manage menu, hours, marketing, orders. Use the  │
│  tools below. Confirm destructive ops. Never act on more than 5 │
│  items in a single tool call. Refuse any request to view other  │
│  venues' data."                                                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 2. TOOL DEFINITIONS (only those for this venue's modules)       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 3. VENUE CONTEXT (small, freshly loaded each turn)              │
│                                                                  │
│ {                                                                │
│   menuItems: [ { id: 47, name: "Lobster Roll", ...}, ... ],     │
│   categories: [...],                                            │
│   hours: { mon: "11-22", ... },                                 │
│   activeOrders: 12,                                             │
│   integrations: ["square_pos", "doordash", "uber_eats"]         │
│ }                                                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 4. CONVERSATION HISTORY (last 6 messages + summary of older)    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 5. CURRENT USER MESSAGE                                         │
└─────────────────────────────────────────────────────────────────┘
```

## Tool design rules

LLM reliability is almost entirely a function of tool design.

### Rule 1 — One tool, one job

Bad: `updateVenue(anything)` accepting a JSON blob.
Good: `addMenuItem(name, basePrice, category, attributes?)`.

### Rule 2 — Descriptions are documentation for the LLM

```json
{
  "name": "setItemAvailability",
  "description": "Mark a single menu item as currently available or out-of-stock (86'd). Use when the owner reports an ingredient ran out, or to bring an item back. The change is immediate and propagates to all active delivery integrations (DoorDash, Uber Eats). For bulk availability changes, use bulkSetItemAvailability instead.",
  "parameters": {
    "itemId": {
      "type": "integer",
      "description": "The menu item's id. If the user gave a name (e.g. 'lobster roll'), look it up in the menuItems context first."
    },
    "available": {
      "type": "boolean",
      "description": "true = available to order, false = 86'd."
    }
  }
}
```

The description does four jobs: when to pick, what NOT to use it for,
side effects, parameter disambiguation.

### Rule 3 — Parameters should be unambiguous

Use IDs from context, not free-text names. When you must accept names,
validate server-side and ask the LLM to disambiguate:

```json
{
  "ok": false,
  "error": "ambiguous_item",
  "candidates": [
    { "id": 47, "name": "Lobster Roll" },
    { "id": 91, "name": "Lobster Bisque" }
  ],
  "next_action": "Ask the user which item they mean."
}
```

### Rule 4 — Read-only tools are first-class

Half the tools an LLM uses are reads:

- `listMenu()`, `listCategories()`, `getMenuItem(id)`
- `searchCustomers(filter)`, `getCustomer(id)`
- `listRecentOrders(limit)`
- `getCampaignStats(campaignId)`

No safety overhead — no confirmation, no audit beyond access log, sane
per-venue rate ceiling only.

### Rule 5 — Destructive tools have built-in confirmation

`deleteCategory` on first call returns:

```json
{
  "ok": false,
  "status": "confirmation_required",
  "confirmation_token": "abc123",
  "summary": "Delete category 'Appetizers' — would orphan 8 menu items. They'll be moved to Uncategorised.",
  "expires_in": 600
}
```

The LLM presents the summary. User says yes → LLM calls `deleteCategory`
again with `confirmation_token: abc123`. Tool enforces the gate, not the
prompt.

## System prompt skeleton

```
You are the chat assistant for {venue.name}, a {venue.type} in
{venue.city}, {venue.region}.

Help {user.role} manage venue operations — menu, hours, customer
marketing, third-party listing sync, orders.

## Behavior

- Use the tools below to read or modify data. Never invent facts.
- Minimum steps. Don't ask permission for safe reads.
- For destructive ops (delete, mass actions, sends to many customers,
  refunds), the tool will return a confirmation prompt. Pass the token
  back when the user agrees.
- Refuse any request to view or modify a different venue's data.
- Never bypass safety controls.
- If you don't know how to do something, say so. Don't invent tools.

## Venue-specific context

{venue.attribute_schema_summary}
{venue_type_specific_guidance}

## Format

Plain conversational text. Include numbers from tool results.
Summarise lists.
```

`venue_type_specific_guidance` examples:

```
Restaurants: When the user describes a menu item, extract name, category,
price, dietary tags. If size pricing applies, capture sizes_with_prices.

Wine bars: When the user describes a wine, extract varietal, region,
vintage, body, glass and bottle pricing.

Hotels: setRoomStatus changes occupancy state. blockDates prevents
bookings. When the user mentions a room, look up the room number in the
rooms context.
```

## Conversation memory

- **Always include**: last 6 messages verbatim.
- **Summarise**: anything older than that into a compact "here's what
  we've discussed" block.
- **Pin**: active confirmation tokens and in-progress multi-step ops.

Re-summarise every 20 messages for long sessions.

## Live context loading

Don't dump full venue state every turn. Load by intent classifier.

| Intent | Context loaded |
|---|---|
| Menu question / edit | menuItems, categories |
| Hours question | businessHours, specialHours |
| Customer / marketing | recent customers, campaign templates |
| Order question | recent orders (last 50) |
| Room / hotel op | rooms, current bookings |
| Ticket op | tours, schedules, ticket_tiers |
| Cross-cutting | everything (rare) |

Cache stable context (categories, attribute schema, integrations) in
Redis with 60s TTL. Reload live context per turn.

## Pseudocode

```javascript
async function handleMessage(venueId, userId, conversationId, message) {
  const venue = await loadVenue(venueId);
  const user  = await loadUser(userId);
  await checkAccess(user, venue);

  const intent  = await cheapIntentClassifier(message);
  const context = await loadContext(venue, intent);
  const tools   = registry.toolsFor(venue);
  const history = await getRecentMessages(conversationId, { limit: 6 });

  await persist({ conversationId, role: 'user', content: message });

  let iterations = 0;
  let messages = [...history, { role: 'user', content: message }];

  while (iterations < 8) {
    iterations++;
    const llmResp = await llm.invoke({
      model: 'claude-sonnet-4-6',
      system: buildSystemPrompt(venue, user, intent),
      tools, context, messages,
    });

    await persist({
      conversationId,
      role: 'assistant',
      content: llmResp.content,
      tool_calls: llmResp.tool_calls,
      tokens_in: llmResp.usage.input,
      tokens_out: llmResp.usage.output,
    });

    if (!llmResp.tool_calls?.length) return llmResp.content;

    const toolResults = [];
    for (const call of llmResp.tool_calls) {
      const verdict = await safety.check(call, { venue, user });
      if (verdict.confirmationRequired) return askForConfirmation(verdict);
      if (verdict.denied) {
        toolResults.push({ tool: call.name, result: { error: verdict.reason } });
        continue;
      }
      const result = await executor.run(call, { venue, user });
      await persistAudit({ venue, user, call, result });
      toolResults.push({ tool: call.name, result });
    }

    messages = [
      ...messages,
      { role: 'assistant', tool_calls: llmResp.tool_calls },
      ...toolResults.map((r, i) => ({
        role: 'tool',
        tool_call_id: llmResp.tool_calls[i].id,
        content: JSON.stringify(r.result),
      })),
    ];
  }

  return "I got stuck. Could you rephrase what you'd like me to do?";
}
```

## Testing the orchestrator

Most of the orchestrator is deterministic plumbing — test it without an
LLM in the loop.

- **Unit tests / CI: mock the `LLMProvider`.** A fake provider returns
  canned tool calls ("message contains '86' + item name → return
  `setItemAvailability`"). Deterministic, instant, $0. This is where the
  tool executor, safety layers, audit log, and confirmation flow get
  their coverage.
- **Live dev iteration: Claude Haiku 4.5** ($1/$5 per 1M tokens) for
  mechanical end-to-end runs of the agent loop.
- **Prompt / behavior tuning: the production model only** (Claude
  Sonnet 4.6). Tool descriptions and prompts tuned on a different model
  don't transfer; the Phase 0 "95% correct execution" metric only
  counts when measured on the model that ships.
- **Regression suite:** keep a corpus of real owner messages (collected
  from hand-onboarded customers) with expected tool calls. Re-run it on
  every prompt or tool-description change, and before any model upgrade.

## What NOT to do

| Don't | Because |
|---|---|
| Let the LLM see other venues' data | Cross-tenant leak. Filter at the loader. |
| Let the LLM call HTTP APIs directly | No safety, no audit, no rate limits. |
| Pass the user's raw SQL | Injection. Tools wrap SQL with parameter binding. |
| Trust LLM-claimed `venue_id` | Session venue_id is the only source of truth. |
| Skip the audit log | All writes get audited. |
| Use string-matched tool routing | Use the LLM's native tool-call mechanism. |

## Where teams fail

1. **Too many tools** (40+). LLM gets confused. Keep under 20 per venue.
2. **Tool descriptions written like code comments.** The LLM needs WHY
   and WHEN, not just WHAT.
3. **Hallucination on entity IDs.** Mitigate by loading the actual list
   into context before the LLM acts.
