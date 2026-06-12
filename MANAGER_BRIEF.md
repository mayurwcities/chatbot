# Manager Brief — What's Possible, What's Not, and Where It Breaks

A plain-English explainer for the venue chatbot platform. Every "not
possible" item includes the exact point where it breaks, with a real
example.

---

## PART 1 — What IS possible (and how)

### 1. Owners manage their venue by chatting with an AI

**Possible. This is the product.**

> Owner types: "Mark the lobster roll as sold out."
> The AI updates our database, pushes the change to DoorDash and the
> venue's website widget, and replies: "Done. Lobster Roll is 86'd on
> your menu and DoorDash."

Why it works now (and didn't 3 years ago):

- LLM "tool calling" is reliable — the AI picks the correct structured
  action ~95% of the time.
- Multimodal AI reads menu photos/PDFs — onboarding becomes a 5-minute
  chat instead of hours of form-filling.
- Big platforms (Square, DoorDash, Booking.com, Eventbrite) now have
  stable merchant APIs.

### 2. One platform, many venue types

**Possible — via modules.** Restaurants get menu + hours + marketing
tools. Hotels get rooms + bookings. Tour operators get tickets +
schedules. Same backbone (chat, safety, customers, marketing) for all.

> A boutique hotel with a restaurant and wine tastings just enables
> three modules: rooms + menu + tickets. No custom build.

**Constraint:** verticals ship one at a time. Restaurants first, hotels
~month 11, tours ~month 14. (See Part 2, item 6.)

### 3. The venue's data appears everywhere it needs to

**Possible — because WE are the source of truth and we publish outward:**

| Channel | How |
|---|---|
| Venue has no website | We auto-generate a hosted page: `ourplatform.com/v/joes-burgers` |
| Venue has a website (WordPress, Wix, Squarespace, custom) | One `<script>` tag embeds our widget showing live menu/hours/booking |
| DoorDash, Uber Eats, Square, Toast, Booking.com, Eventbrite | One adapter per platform, using their official APIs |
| The venue's own customers | Email + SMS campaigns sent from chat |

> Owner changes a price once in chat → website widget, hosted page, and
> DoorDash all update. That's the pitch: one chat window, everything
> syncs.

### 4. A safety system that prevents the AI from breaking a business

**Possible, and non-negotiable.** Ten layers, including:

- **Confirmation before anything risky:** "That promo would go to 487
  customers, est. cost $0.49 — confirm?"
- **Undo:** owner types "undo" → last change reverts.
- **Audit log:** "Who changed the pizza price yesterday at 6 PM?" — we
  always know.
- **Limits:** the AI physically cannot delete more than 1 thing per
  action, or email 500 people without explicit approval.
- **Step-up auth:** a $1,200 refund requires clicking a link sent to the
  owner's email — chat alone can't do it.

### 5. Renting AI instead of building it

**Possible and cheap.** We use Claude (Anthropic) via API. Cost per
active venue: $9–35/month. Subscription price: $79–249/month. Healthy
margin, and we can swap AI providers in about a week if needed.

---

## PART 2 — What is NOT possible (and exactly where it breaks)

### 1. "Plug into any venue's existing website and let the AI edit it"

**Not possible as a product.** This is an unsolved research problem.

**Where it breaks:**

- A website is not a database. To change a site you must change the
  system that generates it — and every venue's system is different
  (WordPress + 30 plugins, Wix, Squarespace, hand-coded HTML from 2014).
- AI agents that "click around" a website admin panel are demos, not
  products. They break on every theme update, popup, or layout change.
- No owner will hand an AI the keys to their live website unattended.
  The trust story is dead on arrival.

> Example: the AI logs into a venue's WordPress to update a price. The
> menu is inside a page-builder plugin's custom layout. The AI edits the
> wrong block, the page layout collapses, and the venue's site is broken
> during dinner service. Who do they call? Us. What can we do? Nothing —
> it's not our system.

**What we do instead (same outcome, buildable):** the chat edits OUR
database; their existing site shows the data through our widget — one
script tag, works on any site. The owner experiences "I typed it, my
website changed." The implementation is solid.

### 2. "Directly access and edit the customer's own database"

**Not possible for ~95% of venues, and a bad idea for the rest.**

**Where it breaks:**

- **Most venues have no database we can reach.** Wix and Squarespace are
  closed platforms. Square, Toast, DoorDash are cloud systems that
  expose APIs, never databases. There is nothing to "get access" to.
- **Every database is different.** One WordPress site keeps its menu in
  a plugin table, another in a JSON blob, another hardcoded in HTML.
  There is no standard. Each customer becomes a one-off
  reverse-engineering project that breaks on their next plugin update.
- **Writing behind an app's back corrupts it.** Apps assume they own
  their database. A direct write skips the app's caches, validation, and
  plugins — the site shows stale data or breaks, and we're debugging
  someone else's stack in production.
- **Per-customer work doesn't scale.** One Square adapter serves every
  Square customer forever. One custom-database integration serves one
  customer until it breaks.

> Example: we get MySQL credentials for a custom restaurant site and
> update a price directly. The site caches its menu page — customers
> still see the old price for hours. The owner blames us. Next month
> their developer renames a table and our integration silently dies.

### 3. "Use their APIs, store nothing on our server" (pure pass-through)

**Getting APIs is good — it's literally our adapter plan. But "no data
on our side" still breaks.** APIs solve access, not the need for our own
record.

**Where it breaks:**

- **The AI needs context every message.** To match "lobster roll" to the
  right item, the menu must be in front of the AI. Pass-through means
  re-downloading the full catalog from Square on every chat message —
  1–3 seconds of lag per turn and we hit their API rate limits fast. The
  fix is caching the menu… and a cache IS data on our server. Back to
  square one, with a worse version of it.
- **Undo and audit require stored history.** "Undo" means knowing the
  previous value. "Who changed what" means a log. Both are data we keep.
  Store nothing → no safety stack → first incident kills the product.
- **Whose API is "the truth"?** A venue on Square + DoorDash + our
  hosted page has three copies of the menu. If they disagree, someone
  must hold the reconciled master copy. That master copy is, by
  definition, a database of record. That's us.
- **~30% of our customers have no API at all.** Small venues with no
  POS, no delivery apps — just our hosted page. For them OUR database is
  the only place their menu exists. We must build it anyway.
- **Marketing/CRM has nowhere else to live.** Customer lists, opt-ins,
  campaign stats — no third-party API stores those for us. Half the
  product's value is inherently our data.
- **A pure pass-through is fragile and moat-less.** If our whole product
  is a thin layer over someone else's API, one revoked key or ToS change
  kills us, and customers can churn with zero switching cost.

> Example: an owner types "undo" after a bad bulk price change. In a
> pass-through design we have no record of the old prices — Square's API
> doesn't keep them for us. We literally cannot undo. That single moment
> destroys trust.

**The sound version of this idea (already in our plan):** for venues
with a POS, treat the POS as authoritative and our database as a synced
mirror — owner edits on the Square terminal, we pull it in, push it to
DoorDash. Our copy still exists (for AI context, undo, audit, CRM); we
just defer to the POS on conflicts.

### 4. Training our own AI model

**Not possible on any sane budget.**

**Where it breaks:** $10M–100M in compute, 10–20 ML researchers, 12+
months — and the day we ship, Anthropic/OpenAI/Google have already
released something better. Our moat is integrations + workflow + the
venue data we accumulate, not model weights. We rent intelligence and
sell the product around it.

### 5. "AI handles everything, zero friction"

**Not safe to promise.** LLMs make mistakes.

**Where it breaks:**

> Owner: "Clean up the menu." AI interprets this as "delete the Pizza
> category" — 12 items vanish mid–dinner rush. Without
> confirmation/undo/audit, that venue churns, tells every owner they
> know, and the product's reputation is finished.

**What we promise instead:** the AI does everything *routine* in one
shot (single edits, questions, reports), and asks one tap of
confirmation for anything bulk, destructive, or costly. Friction only
where mistakes are expensive.

### 6. All verticals + all integrations at launch

**Not possible with a small team. Sequencing is the plan, not a
limitation we apologize for.**

**Where it breaks:**

- Each integration (DoorDash, Square, Uber Eats, Toast…) is 2–4 months
  end-to-end including certification. Five in parallel = all of them
  half-broken.
- Four verticals at once = a data model designed in the abstract for
  customers we don't have yet, and nothing works well anywhere.

**The sequence:** Restaurants (now) → DoorDash (~month 7) → Square +
hotels (~month 11) → tickets/tours (~month 14) → Uber Eats, Toast,
self-serve (~month 16–18). Two integrations a quarter is realistic;
"every platform by month 6" is not.

### 7. Self-serve onboarding from day 1

**Not wise.** Real small-venue owners quit at the first confusing error.

**The plan:** founder personally hand-onboards the first 10 customers,
we learn where they struggle, THEN we automate sign-up (~month 16). The
AI-powered onboarding (upload a menu photo → profile auto-built) comes
at that stage too.

---

## PART 3 — The one-paragraph summary for any stakeholder

> We are NOT building an AI that edits other people's websites or
> databases — that breaks technically (no access, no standards, no
> safety) and commercially (no trust, no scale). We ARE building the
> system of record that venues control through chat: our database holds
> the truth, and it publishes everywhere the venue needs — their
> existing website (via widget), a hosted page, DoorDash/Square/
> Booking.com (via official APIs), and their customers' inboxes. The
> owner's experience is identical to the magic version — "I typed it
> and it changed everywhere" — but this version is buildable in 18
> months by 4 people for ~$1–1.5M, with a safety net that ensures the
> AI never breaks a customer's business.

---

## Quick reference table

| Idea | Verdict | Breaks at |
|---|---|---|
| Chat controls venue operations | ✅ Build | — |
| Widget + hosted page for venue websites | ✅ Build | — |
| Official-API adapters (DoorDash, Square…) | ✅ Build, one at a time | — |
| 10-layer safety stack | ✅ Build, day 1 | — |
| Rent AI (Claude/GPT via API) | ✅ Build | — |
| AI edits arbitrary websites | ❌ Never | No access, no standards, breaks on any site change, zero trust |
| Direct access to customers' databases | ❌ Never | Most have none; rest are all different; direct writes corrupt apps |
| APIs with zero data stored on our side | ❌ Never | AI context, undo, audit, conflict resolution, no-API venues, CRM all need our DB |
| Train our own LLM | ❌ Never | $10M+, instantly obsolete |
| All verticals + integrations at once | ❌ Sequence instead | 2–4 months each; parallel = everything half-broken |
| Self-serve onboarding day 1 | ❌ Month 16+ | Owners quit at first error; learn from hand-onboarding first |
