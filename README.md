# Venue Chatbot Platform

A chat-controlled multi-vertical management system for small venues —
restaurants, hotels, tour operators, retail. Owners manage their venue
(menu, hours, rooms, tickets, marketing, customer outreach) by typing or
speaking to an AI chat assistant. The platform is the canonical source of
truth; data publishes outward to multiple channels (a JS widget for the
venue's existing website, our hosted page if they have none, third-party
platforms via adapters, SMS/email to their customers).

## Thesis

> The chat edits OUR database. The database publishes to wherever the
> venue wants its data to appear.

We do not edit arbitrary websites. We give venues a chat interface that
controls their operational data and synchronises to the third-party
platforms they already use.

## Documents

| File | Covers |
|---|---|
| [`01-vision.md`](01-vision.md) | The idea, who it's for, success criteria |
| [`02-what-works-vs-what-doesnt.md`](02-what-works-vs-what-doesnt.md) | Approaches that ship + traps to avoid |
| [`03-architecture.md`](03-architecture.md) | High-level system architecture |
| [`04-data-model.md`](04-data-model.md) | Schema, multi-vertical via modules |
| [`05-chat-orchestrator.md`](05-chat-orchestrator.md) | Agent loop, tool registry, decision flow |
| [`06-multi-vertical-modules.md`](06-multi-vertical-modules.md) | One platform across verticals |
| [`07-integrations.md`](07-integrations.md) | Adapter pattern, third-party APIs |
| [`08-safety-and-guardrails.md`](08-safety-and-guardrails.md) | Ten-layer guardrail stack |
| [`09-llm-and-tech-stack.md`](09-llm-and-tech-stack.md) | LLM choice, infra |
| [`10-roadmap.md`](10-roadmap.md) | Phased build plan |
| [`11-team-budget-risks.md`](11-team-budget-risks.md) | Headcount, run rate, risks |
| [`12-decisions-now-vs-later.md`](12-decisions-now-vs-later.md) | What to lock, what to defer |
| [`EMAIL_TO_MANAGER.md`](EMAIL_TO_MANAGER.md) | What's possible, what's not |
| [`MANAGER_BRIEF.md`](MANAGER_BRIEF.md) | Plain-English explainer: possible vs not, where each bad approach breaks |

## Quickstart

1. Read `01-vision.md`
2. Read `02-what-works-vs-what-doesnt.md`
3. Read `10-roadmap.md`
4. Skim the rest as needed

## Status

Pre-build. Documentation phase. No code. Greenfield project — no shared
infrastructure with any existing codebase.

## Decision log

`12-decisions-now-vs-later.md` — keep current.
