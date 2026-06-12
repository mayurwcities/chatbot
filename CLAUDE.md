# Claude Context — Venue Chatbot Platform

Context for future Claude sessions invoked in `/Users/wcities/ReactStudy/chatbot`.

## What this project is

A chat-first venue management SaaS. Owners of restaurants, hotels, tour
operators, and retail shops manage everything (menus, hours, rooms, tickets,
customer marketing, third-party platform sync) by talking to an LLM agent.

**Status:** pre-build. Documentation only. No code yet. New project — no
reuse from any existing codebase.

## How to be useful here

| If the user asks about… | Read |
|---|---|
| Architecture / data model | `03-architecture.md`, `04-data-model.md` |
| The chat agent loop | `05-chat-orchestrator.md` |
| A specific vertical | `06-multi-vertical-modules.md` |
| Third-party integrations | `07-integrations.md` |
| Safety / failure modes | `08-safety-and-guardrails.md` |
| LLM choice | `09-llm-and-tech-stack.md` |
| Phasing / what to build next | `10-roadmap.md` |
| Budget / team / risk | `11-team-budget-risks.md` |
| Locking a decision | `12-decisions-now-vs-later.md` |
| The full restaurant journey (signup → go-live → daily ops) | `13-restaurant-end-to-end-flow.md` |
| Explaining to a stakeholder | `MANAGER_BRIEF.md` |

## Hard "no"s

- Building or training a custom LLM. Use Claude or GPT via API.
- "Edit arbitrary websites with AI." Not a buildable product foundation.
  We are the database of record; we publish outward via widgets, hosted
  pages, and API adapters.
- Direct access to customers' own databases. Most venues have none to
  give (Wix, Squarespace, Toast expose APIs, never DBs); the rest are
  all different, and writes behind the app's back corrupt it.
- Stateless API pass-through ("use their APIs, store nothing"). Undo,
  audit, LLM context, conflict resolution, CRM, and no-API venues all
  require our own database. APIs are the adapter layer, not a
  replacement for the DB of record.
- Multi-vertical at launch. Restaurants first, then hotels, then tours,
  then retail. Sequenced.
- Multiple third-party integrations in parallel. One at a time.
- Self-serve onboarding before 10 hand-held customers.
- Skipping the safety stack to ship faster.

## Tone for advice

The author is a working developer building this from scratch with a small
team. Wants buildable advice, realistic timelines (months, not weeks),
honest complexity flags, and the simplest architecture that works.

## File conventions

- `NN-name.md` for design docs read in sequence
- All-caps for meta-files (`README.md`, `CLAUDE.md`)
- Markdown only. No source code in this folder.
