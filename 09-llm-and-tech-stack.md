# 09 · LLM and Tech Stack

## LLM choice

### Don't train your own

Frontier LLM training costs $10M–$100M+ in compute, 10–20 ML researchers,
and a multi-million-token proprietary dataset. The moment you ship,
you're behind whatever frontier just released. The moat is integrations
+ UX + data, not weights.

**Rent intelligence. Sell integration + workflow.**

### Default: Claude Sonnet 4.6 (Anthropic)

- **Best tool-use today.** Anthropic's `tool_use` is the most reliable
  structured-call mechanism.
- **Strong instruction-following.** Critical for safety guardrails.
- **200k context window.** Fits venue menu + recent orders + chat history.
- **Lower hallucination on structured tasks.**
- **Interactive-grade latency** (~1–2s).

Pricing (approximate, 2026):

- $3 per 1M input tokens
- $15 per 1M output tokens
- Prompt caching available (~10x cheaper on cached portion)

### Cost per venue

50 chat interactions/day, ~5k input tokens, ~500 output tokens per turn:

```
50 × (5,000 × $3/1M + 500 × $15/1M)
= 50 × ($0.015 + $0.0075)
= $1.13/day
≈ $34/month
```

With prompt caching: $9–15/month per active venue.

At $79–149/month subscription, comfortably covered.

### Alternative: GPT-4o (OpenAI)

Comparable quality + tool use. Marginally cheaper. Larger ecosystem.

- $2.50 per 1M input tokens
- $10 per 1M output tokens

### Cheap routing layer (later, not Day 1)

Most messages don't need a frontier model. Route simple intents to
templated responses or a small model:

```
                  User message
                       │
                       ▼
         ┌──────────────────────────┐
         │ Cheap classifier         │
         │ (small LLM / rules)      │
         └──────────┬───────────────┘
                    │
       ┌────────────┴─────────────────┐
       │                              │
   simple intent                  complex / multi-tool
       │                              │
       ▼                              ▼
   ┌────────────┐               ┌──────────────────┐
   │ Templated  │               │ Claude Sonnet    │
   │ response   │               │ agent loop with  │
   │ (no LLM)   │               │ tool use         │
   └────────────┘               └──────────────────┘
```

Drops cost 5–10x. Build after V1 ships and you have real usage data.

### What NOT to do

| Don't | Because |
|---|---|
| Train your own model | $10M+, 12+ months, immediately behind frontier |
| Build your own LLM provider | Inference at scale is its own engineering challenge |
| Use a tiny model for the orchestrator Day 1 | Quality is everything for agent reliability |
| Switch providers every quarter | Each change is engineering work |

### Provider abstraction

```typescript
interface LLMProvider {
  invoke(opts: {
    system: string;
    tools: ToolDefinition[];
    messages: Message[];
    maxTokens?: number;
  }): Promise<{
    content: string;
    tool_calls: ToolCall[];
    usage: { input: number; output: number };
  }>;
}

class ClaudeProvider implements LLMProvider { ... }
class GPTProvider    implements LLMProvider { ... }
class GeminiProvider implements LLMProvider { ... }
```

Provider is a config switch.

## Tech stack

### Frontend

| Choice | Reason |
|---|---|
| **Next.js 16** | Mature framework, good API routes, SSR for hosted pages |
| **Tailwind CSS** | Fast iteration on layouts |
| **TypeScript** | Type safety for tool definitions |
| **React 18+** | Default |

Pages needed:
- Marketing landing
- Sign-up + onboarding wizard
- Owner dashboard (chat + side panels)
- Public hosted venue page (`yourplatform.com/v/{slug}`)
- Widget bundle (embeddable script)
- Internal admin dashboard

### Backend

| Choice | Reason |
|---|---|
| **Node.js + TypeScript** | Shared language with frontend |
| **Next.js API routes** OR **standalone Node service** | API routes for V1; split out orchestrator if scaling needs |
| **MySQL 8 / Postgres 16** | Either works; Postgres has better JSON + row-level security |
| **Redis** | Cache + queue backend |
| **BullMQ** | Background jobs (adapter sync retries, scheduled campaigns) |

### LLM + tool layer

| Choice | Reason |
|---|---|
| **Anthropic SDK** | First-party, supports `tool_use` natively |
| **JSON Schema** for tool definitions | Standard, portable across providers |
| **Zod** for runtime validation | Catches LLM arg shape mismatches at the executor boundary |

### Integrations (SDKs)

| Provider | SDK |
|---|---|
| Square | Square Web SDK, REST API |
| Toast | REST API (no official Node SDK; use `axios`) |
| DoorDash | Partner API (REST) |
| Stripe | `stripe-node` |
| Email | SendGrid / Mailgun / Postmark Node SDK |
| Twilio | `twilio` npm package |
| Booking.com | XML/REST channel manager API |

### Auth + multi-tenancy

| Choice | Reason |
|---|---|
| **NextAuth.js** | Email + magic-link out of the box; OAuth providers for connections |
| **`openid-client` / Passport** for integration OAuth | Don't hand-roll |
| **Argon2** for password hashing | Modern default |
| **AWS Secrets Manager** or **Doppler** | Encrypted integration credentials |

### Hosting + infra

| Choice | Reason |
|---|---|
| **Vercel** | Next.js frontend + API |
| **AWS RDS** | Production DB |
| **AWS ElastiCache** | Redis |
| **AWS S3** | Image storage |
| **CloudFront** | Static asset CDN |
| **Sentry** | Error tracking |
| **Axiom / Datadog** | Log aggregation |
| **BetterStack** | Alerting |

Don't add Kafka, Kubernetes, custom service mesh, or GraphQL federation.
Over-engineering for year-1 scale (under 1000 venues, under 10k req/min).

### Observability

Two things matter:

1. **LLM cost per venue per day** — dashboard that catches runaway venues
   before they cost $500.
2. **Tool call latency + error rate** — every call timed; failures logged.

Build the dashboard from `tool_calls` and `chat_messages` tables.

### CI/CD

| Choice |
|---|
| GitHub Actions |
| Vercel preview deploys |
| Sentry release tracking |
| Migrations via Knex or Drizzle |

### Security baseline

| Practice |
|---|
| HTTPS only, HSTS enabled |
| Per-venue rate limits at the edge (Cloudflare / Vercel) |
| `SECURE`-flagged cookies for auth |
| Argon2 for password hashing |
| OWASP Top 10 audit before launch |
| Sentry source maps + alerts |
| Quarterly third-party pen test once profitable ($5k–15k) |
| Cyber liability insurance ($1–5M policy) |

### Added later

- **SOC 2 Type I** (then Type II) — start within 12 months. $40–80k Year 1.
- **GDPR / CCPA tooling** — for EU/CA customers.
- **Webhooks outbound** — let venues subscribe to events.
- **Public REST API + docs**.
- **Multi-region deployment**.
- **Voice (Twilio)**.
- **Mobile app**.

## Local dev setup

```bash
git clone <repo> && cd chatbot-platform
nvm use 20
npm install

cp .env.example .env.local
# fill in: ANTHROPIC_API_KEY, DATABASE_URL, REDIS_URL, etc.

docker-compose up -d   # MySQL + Redis
npm run db:migrate
npm run db:seed        # demo venue with sample data

npm run dev            # Next.js on :3000
npm run worker         # BullMQ workers
```

Goal: new engineer productive in <1 hour.

## Infra cost estimate (100 venues)

| Line | Monthly |
|---|---|
| Vercel (Pro) | $20 |
| AWS RDS (db.t4g.medium) | $80 |
| AWS ElastiCache (cache.t4g.small) | $40 |
| AWS S3 + CloudFront | $20 |
| Anthropic API (100 venues × $15) | $1,500 |
| Email provider (transactional + marketing) | $200–400 |
| Twilio (SMS) | $100–500 |
| Sentry, Axiom, BetterStack | $200 |
| Doppler / secrets | $40 |
| **Total** | **~$2,200–3,000/month** |

Per-venue infra: $22–30/month. At $79/month subscription, healthy
margin.

At 1,000 venues: ~$15–25k/month, per-venue ~$15–25. Margin improves with
scale (DB and infra mostly fixed; LLM scales linearly).
