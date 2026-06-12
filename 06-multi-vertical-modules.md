# 06 · Multi-Vertical via Modules

How one platform serves restaurants, hotels, tour operators, and retail.

## Core idea

A **module** is a bundle of:

- Database tables (or table extensions)
- Tools the LLM can call
- Per-vertical prompt augmentations
- Optional UI components
- Optional adapter slots

Modules are enabled per venue. A venue's enabled modules determine which
tools the LLM sees and which tables it can read/write.

```
                    venue_type → default modules
   ┌──────────────────────────────────────────────────────────┐
   │ restaurant  → menu, hours, marketing, orders             │
   │ cafe        → menu, hours, marketing, orders             │
   │ bar         → menu, hours, marketing, orders             │
   │ hotel       → rooms, hours, marketing, reservations      │
   │ b&b         → rooms, hours, marketing, reservations      │
   │ hotel + restaurant → rooms + menu + ... (multi-module)   │
   │ tour_operator → tours, tickets, marketing                │
   │ theater     → events, tickets, marketing                 │
   │ retail      → inventory, hours, marketing, orders        │
   │ spa         → services, schedules, marketing             │
   └──────────────────────────────────────────────────────────┘
```

Owners can add or remove modules. A pizza place hosting trivia nights can
add the `events` module.

## Modules catalog

| Module | Tools | Tables touched | Default for |
|---|---|---|---|
| `menu` | `listMenu`, `addMenuItem`, `updateMenuItem`, `setItemAvailability`, `addCategory`, `removeCategory`, `addModifier` | catalog_categories, catalog_items, catalog_modifiers | restaurant, cafe, bar |
| `hours` | `setHours`, `addSpecialHours`, `setClosedForDate` | business_hours, special_hours | every venue |
| `marketing` | `searchCustomers`, `sendCampaign`, `previewCampaign`, `listCampaigns`, `getCampaignStats`, `createTemplate` | customers, campaigns, campaign_*, email_templates | every venue |
| `orders` | `listOrders`, `getOrder`, `updateOrderStatus`, `refundOrder`, `manualOrder` | orders, order_items, payments | restaurant, cafe, bar, retail |
| `rooms` | `listRooms`, `setRoomStatus`, `setRoomRate`, `blockDates`, `unblockDates`, `addRoomBooking` | rooms, room_bookings, room_rates | hotel, b&b |
| `reservations` | `listReservations`, `addReservation`, `cancelReservation`, `setTableAvailability` | reservations, tables | restaurants taking reservations, hotels |
| `tours` | `listTours`, `createTour`, `updateTour`, `addSchedule`, `setScheduleStatus` | tours, tour_schedules | tour_operator |
| `tickets` | `addTicketTier`, `updateTicketTier`, `setTourSaleState`, `markAttendeeCheckedIn` | ticket_tiers, attendees | tour_operator, theater, escape_room, concert_venue |
| `events` | `createEvent`, `addOccurrence`, `cancelEvent` | events, event_occurrences | theater, concert_venue |
| `inventory` | `listProducts`, `addProduct`, `updateProduct`, `setStock`, `adjustStock` | catalog_items, inventory_movements | retail |
| `services` | `listServices`, `addService`, `updateService`, `addAppointment` | services, appointments | spa, salon, fitness |
| `reviews` | `listReviews`, `replyToReview`, `requestReview` | reviews | every venue (optional) |
| `analytics` | `topSellingItems`, `customerCount`, `revenueByPeriod`, `repeatRate` | derived | every venue |

## Per-module notes

### `menu`

- **Sizes** (small/medium/large pizza) live in `attributes.sizes_with_prices`,
  not as separate items. Cleaner CRM.
- **Modifiers** in `catalog_modifiers` shared across items.
- **Availability** is a boolean toggle, not deletion. Allows re-enabling
  without losing history.

Sample `addMenuItem` description:

> Adds a new menu item to a category. Extract: name (required), category
> (required — pick from listCategories), base_price (required unless size
> pricing), description, dietary tags, vertical-specific attributes from
> the venue schema. If category doesn't exist, ask before creating.

### `hours`

Two tables:

- `business_hours` for the recurring weekly schedule
- `special_hours` for overrides (holidays, private events, closures)

Natural-language phrases to handle:
- "Close early today at 6"
- "We're closed Christmas day"
- "Lunch is 11 to 2 every weekday"
- "Open till 1am Friday and Saturday"

### `marketing`

Tools:

- `searchCustomers({filter})` — segmentation
- `sendCampaign({segment, channel, template, subject, body})` — confirms
  when recipient count > 100
- `previewCampaign(...)` — show what would happen
- `getCampaignStats(campaignId)` — opens, clicks, revenue

Confirmation example:

> User: "Send 15% off to anyone who ordered pizza in the last 30 days."
> Assistant: "That's 487 customers. Estimated cost: $0.49. Confirm?"
> User: "Yes"
> Assistant calls `sendCampaign({..., confirmation_token: 'xyz'})`.

### `orders`

- `listOrders({status, limit})` — "what's pending right now?"
- `getOrder(orderId)` — drill in
- `updateOrderStatus(orderId, status)` — pending → preparing → ready → completed
- `refundOrder(orderId, amount, reason)` — confirmation + role check
- `manualOrder({customer, items, fulfillment})` — phone-in orders

### `rooms`

State machine:

```
              available ←──────────────── checked_out
                  │                            ▲
              book  │                          │
                  ▼                            │
              reserved → checked_in → occupied ┘
                  │                          │
                  └────── cancel ────────────┘

  blocked  ←→  maintenance  ←→  dirty
```

Tools:

- `setRoomStatus(roomId, status)`
- `setRoomRate(roomId, rate, dateRange?)`
- `blockDates(roomId, dateRange, reason?)`
- `addRoomBooking({roomId, guestName, checkIn, checkOut, source})`
- `listAvailableRooms({checkIn, checkOut})`

Examples:
- "Mark 302 as occupied" → `setRoomStatus(302, 'occupied')`
- "Block 514 from June 1-7 for maintenance" → `blockDates(514, '2026-06-01', '2026-06-07', 'maintenance')`
- "Increase weekend rates by $50" → `setRoomRate(*, current+50, weekends)` (bulk → confirms)

### `tickets`

- `createTour({name, duration, capacity, description})`
- `addSchedule({tourId, datetime, capacityOverride?})`
- `addTicketTier({scheduleId, name, price, capacity})`
- `setTourSaleState(scheduleId, state)` — on_sale / paused / sold_out
- `markCheckedIn(attendeeId)`

### `inventory` (retail)

- `addProduct({name, price, sku, stock, attributes})`
- `setStock(productId, quantity)`
- `adjustStock(productId, delta, reason)`
- `listLowStock(threshold)`

## Multiple modules per venue

A venue can run several modules. Orchestrator surfaces the union of tools
to the LLM.

Example: a boutique hotel with a restaurant, spa, and ticketed wine
tasting events:

```
modules enabled:
  - rooms          (hotel core)
  - reservations   (hotel)
  - menu           (restaurant)
  - hours          (universal)
  - services       (spa)
  - tickets        (wine tastings)
  - events         (wine tastings)
  - marketing      (universal)

LLM sees: union of all the above (~25 tools)
```

**Tool budget:** target ≤20 tools per venue (see `05-chat-orchestrator.md`
→ Where teams fail). A multi-module venue like the one above goes over —
when that happens, trim before shipping: drop read-only tools the venue
never uses, merge near-duplicates (`blockDates`/`unblockDates` → one tool
with a flag), or gate rarely-used tools behind an intent pre-check so
they're only included when the message warrants them.

## Per-vertical prompt augmentation

Same `addMenuItem` tool exists for a pizza place, a wine bar, and a hotel
restaurant. What differs is the per-venue guidance appended to the system
prompt.

```json
venue.attribute_schema:
{
  "catalog_items": {
    "crust_type":        { "type": "enum", "values": ["thin","thick","stuffed"] },
    "sizes_with_prices": { "type": "array", "shape": { "size": "string", "price": "number" } },
    "spice_level":       { "type": "number", "min": 0, "max": 5 }
  }
}

venue.prompt_guidance:
"When the user describes a pizza, always extract sizes_with_prices. The
standard sizes are small/medium/large/family. Spice levels are 0–5."
```

## Bootstrapping a new vertical

Adding gyms / fitness:

1. **Schema**: add tables (`classes`, `class_schedules`, `memberships`,
   `check_ins`)
2. **Module declaration**: register in the modules catalog
3. **Tools**: implement (`addClass`, `bookClass`, `cancelMembership`, …)
   with safety guards
4. **Prompt guidance**: per-vertical examples
5. **Venue type**: add `gym` to the enum
6. **Default modules**: declare auto-enabled set
7. **Adapters (optional)**: Mindbody, ClassPass

No core changes.

## What stays universal across all verticals

- Chat orchestrator
- Safety stack
- Customers + orders
- Marketing
- Hours
- Authentication, billing, multi-tenancy

Build these well once. Add modules vertically.

## When NOT to create a module

| Situation | Do instead |
|---|---|
| Small extension of an existing module | Add a tool to that module |
| One-off for one customer | Decline or charge for custom |
| Crosses vertical lines (e.g. "calendar") | UI concept mapping to multiple modules, not a module |

A module is justified when it has its own table set AND its own tools AND
will be enabled for multiple venues.
