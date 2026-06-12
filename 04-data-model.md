# 04 · Data Model

Canonical schema. Handles every vertical (restaurants, hotels, tour
operators, retail) with the same backbone, extended via modules.

## Design principles

1. **Multi-tenant via `venue_id`** on every domain table. Row-level
   filtering at the data layer.
2. **Universal backbone, verticals on top.** Every venue has profile,
   catalog, customers, orders, marketing. Vertical specifics are
   additional tables.
3. **JSON attribute columns for within-vertical variation.** A pizza
   place needs `crust_type`; a wine bar needs `vintage`. Same
   `catalog_items` table; both in `attributes JSON`.
4. **Audit everything.** Every mutation goes through the tool layer,
   which writes an `audit_log` row.
5. **Soft-delete by default.** `deleted_at TIMESTAMP NULL` everywhere.

## Schema overview

```
                          ┌──────────────────┐
                          │     venues       │  ← tenants
                          └──┬───────────────┘
                             │
       ┌─────────────────────┼──────────────────────────────┐
       │                     │                              │
  ┌────▼────────┐    ┌───────▼────────┐           ┌─────────▼─────────┐
  │ venue_users │    │ venue_modules  │           │ venue_integrations│
  └─────────────┘    └────────────────┘           │ integration_id_map│
                                                  └───────────────────┘
                             │
       ┌─────────────────────┼──────────────────────────────┐
       │                     │                              │
       ▼                     ▼                              ▼
   CATALOG               CUSTOMERS + ORDERS             VERTICAL EXTENSIONS
   ─────────             ──────────────────             ──────────────────
   catalog_categories    customers                      rooms (hotels)
   catalog_items         orders                          room_bookings
   catalog_modifiers     order_items                     tours (tour ops)
                         payments                        tour_schedules
                                                         ticket_tiers

                          MARKETING                       SAFETY
                          ─────────                       ──────
                          email_templates                 audit_log
                          campaigns                       tool_calls
                          campaign_recipients             chat_messages
                          campaign_tracking               confirmations
                          campaign_clicks
```

## Core tables

### `venues`

```sql
CREATE TABLE venues (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  slug            VARCHAR(64) NOT NULL UNIQUE,
  name            VARCHAR(255) NOT NULL,
  type            ENUM('restaurant','cafe','bar','hotel','b&b',
                       'tour_operator','theater','escape_room',
                       'concert_venue','retail','spa','other') NOT NULL,
  timezone        VARCHAR(64) NOT NULL DEFAULT 'America/New_York',
  currency        CHAR(3) NOT NULL DEFAULT 'USD',
  locale          VARCHAR(16) NOT NULL DEFAULT 'en-US',
  address_line1   VARCHAR(255),
  address_line2   VARCHAR(255),
  city            VARCHAR(128),
  region          VARCHAR(64),
  postal_code     VARCHAR(32),
  country_code    CHAR(2),
  phone           VARCHAR(32),
  email           VARCHAR(255),
  website_url     VARCHAR(512),
  logo_url        VARCHAR(512),
  brand_colors    JSON,
  attribute_schema JSON,
  status          ENUM('active','suspended','archived') NOT NULL DEFAULT 'active',
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  deleted_at      TIMESTAMP NULL,
  INDEX idx_slug (slug),
  INDEX idx_type (type)
);
```

### `venue_users`

```sql
CREATE TABLE venue_users (
  id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  venue_id    BIGINT UNSIGNED NOT NULL,
  email       VARCHAR(255) NOT NULL,
  name        VARCHAR(255),
  role        ENUM('owner','manager','staff','viewer') NOT NULL,
  permissions JSON,
  password_hash    VARCHAR(255),
  last_login_at    TIMESTAMP NULL,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  deleted_at  TIMESTAMP NULL,
  UNIQUE KEY uniq_venue_email (venue_id, email),
  INDEX idx_venue (venue_id),
  FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE
);
```

### `venue_modules`

```sql
CREATE TABLE venue_modules (
  id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  venue_id    BIGINT UNSIGNED NOT NULL,
  module      ENUM('menu','hours','marketing','orders','rooms',
                   'tours','tickets','reservations','inventory','reviews',
                   'analytics','billing','spa','events') NOT NULL,
  enabled     TINYINT(1) NOT NULL DEFAULT 1,
  config      JSON,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_venue_module (venue_id, module),
  FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE
);
```

Default modules per venue type:

| Venue type | Default modules |
|---|---|
| restaurant / cafe / bar | menu, hours, marketing, orders |
| hotel / b&b | rooms, hours, marketing, reservations |
| tour_operator | tours, tickets, marketing |
| theater / escape_room / concert_venue | events, tickets, marketing |
| retail | inventory, hours, marketing, orders |

### `venue_integrations`

```sql
CREATE TABLE venue_integrations (
  id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  venue_id    BIGINT UNSIGNED NOT NULL,
  kind        ENUM('pos','delivery','reservations','ticketing','channel_manager',
                   'cms','comms','payments','analytics') NOT NULL,
  provider    VARCHAR(64) NOT NULL,
  credentials_encrypted TEXT,
  config      JSON,
  status      ENUM('pending','active','paused','error') NOT NULL DEFAULT 'pending',
  last_synced_at  TIMESTAMP NULL,
  last_error  TEXT,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_venue_kind (venue_id, kind),
  INDEX idx_provider (provider),
  FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE
);
```

### `integration_id_map`

Translates between our canonical IDs and each provider's external IDs.
One row per (integration, entity). Without this table no adapter can
push a targeted update ("86 item 47" needs DoorDash's ID for item 47).

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
  INDEX idx_venue (venue_id),
  FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE,
  FOREIGN KEY (integration_id) REFERENCES venue_integrations(id) ON DELETE CASCADE
);
```

Usage details in `07-integrations.md` → ID mapping.

## Catalog (universal)

```sql
CREATE TABLE catalog_categories (
  id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  venue_id    BIGINT UNSIGNED NOT NULL,
  name        VARCHAR(255) NOT NULL,
  display_order INT NOT NULL DEFAULT 0,
  description TEXT,
  image_url   VARCHAR(512),
  attributes  JSON,
  deleted_at  TIMESTAMP NULL,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_venue (venue_id),
  FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE
);

CREATE TABLE catalog_items (
  id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  venue_id    BIGINT UNSIGNED NOT NULL,
  category_id BIGINT UNSIGNED,
  name        VARCHAR(255) NOT NULL,
  description TEXT,
  base_price  DECIMAL(10,2),
  currency    CHAR(3) NOT NULL DEFAULT 'USD',
  available   TINYINT(1) NOT NULL DEFAULT 1,
  image_url   VARCHAR(512),
  display_order INT NOT NULL DEFAULT 0,
  attributes  JSON,
  deleted_at  TIMESTAMP NULL,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  INDEX idx_venue_category (venue_id, category_id),
  FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE
);

CREATE TABLE catalog_modifiers (
  id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  venue_id    BIGINT UNSIGNED NOT NULL,
  item_id     BIGINT UNSIGNED,
  name        VARCHAR(128) NOT NULL,
  type        ENUM('single','multi','quantity') NOT NULL DEFAULT 'single',
  required    TINYINT(1) NOT NULL DEFAULT 0,
  options     JSON,
  deleted_at  TIMESTAMP NULL,
  INDEX idx_venue_item (venue_id, item_id),
  FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE
);
```

Example `attributes` payloads:

```
restaurant pizza:    {"crust_type":"thin", "sizes_with_prices":[{"size":"medium","price":22}]}
wine bar:            {"varietal":"Sauvignon Blanc", "vintage":2021, "region":"Loire"}
hotel restaurant:    {"dietary":["vegetarian"], "spice_level":2}
tour operator:       {"duration_minutes":180, "group_size_max":12}
```

## Hours (universal)

```sql
CREATE TABLE business_hours (
  id            BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  venue_id      BIGINT UNSIGNED NOT NULL,
  day_of_week   TINYINT NOT NULL,                      -- 0=Sun, 6=Sat
  open_time     TIME,                                  -- NULL = closed
  close_time    TIME,
  service       VARCHAR(32) DEFAULT 'main',            -- 'main', 'happy_hour', 'brunch'
  effective_from DATE,
  effective_to   DATE,
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_venue_day (venue_id, day_of_week),
  FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE
);

CREATE TABLE special_hours (
  id            BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  venue_id      BIGINT UNSIGNED NOT NULL,
  date          DATE NOT NULL,
  open_time     TIME,
  close_time    TIME,
  reason        VARCHAR(128),
  is_closed     TINYINT(1) NOT NULL DEFAULT 0,
  INDEX idx_venue_date (venue_id, date),
  FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE
);
```

## Customers + orders (universal)

```sql
CREATE TABLE customers (
  id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  venue_id    BIGINT UNSIGNED NOT NULL,
  email       VARCHAR(255),
  phone       VARCHAR(32),
  name        VARCHAR(255),
  marketing_email_opt_in   TINYINT(1) NOT NULL DEFAULT 1,
  marketing_sms_opt_in     TINYINT(1) NOT NULL DEFAULT 0,
  total_orders             INT NOT NULL DEFAULT 0,
  total_spend              DECIMAL(12,2) NOT NULL DEFAULT 0,
  first_order_at  TIMESTAMP NULL,
  last_order_at   TIMESTAMP NULL,
  attributes  JSON,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_venue_email (venue_id, email),
  INDEX idx_venue_phone (venue_id, phone),
  INDEX idx_venue_last_order (venue_id, last_order_at),
  FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE
);

CREATE TABLE orders (
  id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  venue_id    BIGINT UNSIGNED NOT NULL,
  customer_id BIGINT UNSIGNED,
  source      ENUM('hosted_page','widget','doordash','ubereats','grubhub',
                   'square_pos','toast_pos','manual','phone','other') NOT NULL,
  external_id VARCHAR(128),
  status      ENUM('pending','confirmed','preparing','ready','completed',
                   'cancelled','refunded') NOT NULL DEFAULT 'pending',
  subtotal    DECIMAL(12,2) NOT NULL,
  tax         DECIMAL(12,2) NOT NULL DEFAULT 0,
  tip         DECIMAL(12,2) NOT NULL DEFAULT 0,
  fees        DECIMAL(12,2) NOT NULL DEFAULT 0,
  total       DECIMAL(12,2) NOT NULL,
  currency    CHAR(3) NOT NULL DEFAULT 'USD',
  fulfillment_type ENUM('dine_in','pickup','delivery','room_service') DEFAULT NULL,
  notes       TEXT,
  attributes  JSON,
  placed_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  fulfilled_at TIMESTAMP NULL,
  INDEX idx_venue_placed (venue_id, placed_at),
  INDEX idx_venue_customer (venue_id, customer_id),
  INDEX idx_external (source, external_id),
  FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
);

CREATE TABLE order_items (
  id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  order_id    BIGINT UNSIGNED NOT NULL,
  item_id     BIGINT UNSIGNED,
  item_name   VARCHAR(255) NOT NULL,
  quantity    INT NOT NULL DEFAULT 1,
  unit_price  DECIMAL(10,2) NOT NULL,
  line_total  DECIMAL(10,2) NOT NULL,
  modifiers   JSON,
  notes       VARCHAR(512),
  INDEX idx_order (order_id),
  FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
);
```

## Vertical extensions

### Hotels — `rooms`

```sql
CREATE TABLE rooms (
  id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  venue_id    BIGINT UNSIGNED NOT NULL,
  number      VARCHAR(32) NOT NULL,
  type        VARCHAR(64),
  capacity    INT NOT NULL DEFAULT 2,
  base_rate   DECIMAL(10,2),
  currency    CHAR(3) NOT NULL DEFAULT 'USD',
  amenities   JSON,
  status      ENUM('available','occupied','dirty','maintenance','blocked')
              NOT NULL DEFAULT 'available',
  attributes  JSON,
  deleted_at  TIMESTAMP NULL,
  INDEX idx_venue (venue_id),
  UNIQUE KEY uniq_venue_number (venue_id, number),
  FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE
);

CREATE TABLE room_bookings (
  id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  venue_id    BIGINT UNSIGNED NOT NULL,
  room_id     BIGINT UNSIGNED,
  customer_id BIGINT UNSIGNED,
  check_in    DATE NOT NULL,
  check_out   DATE NOT NULL,
  source      ENUM('hosted_page','booking_com','airbnb','walk_in','phone','other')
              NOT NULL,
  external_id VARCHAR(128),
  rate_per_night DECIMAL(10,2),
  total       DECIMAL(12,2),
  status      ENUM('pending','confirmed','checked_in','checked_out','cancelled')
              NOT NULL DEFAULT 'pending',
  INDEX idx_venue_check_in (venue_id, check_in),
  FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE,
  FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE SET NULL,
  FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE SET NULL
);

CREATE TABLE room_rates (
  id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  venue_id    BIGINT UNSIGNED NOT NULL,
  room_id     BIGINT UNSIGNED NOT NULL,
  date        DATE NOT NULL,
  rate        DECIMAL(10,2) NOT NULL,
  UNIQUE KEY uniq_room_date (room_id, date),
  FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
);
```

### Tour operators — `tours` + `ticket_tiers`

```sql
CREATE TABLE tours (
  id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  venue_id    BIGINT UNSIGNED NOT NULL,
  name        VARCHAR(255) NOT NULL,
  description TEXT,
  duration_minutes INT,
  capacity    INT,
  base_price  DECIMAL(10,2),
  currency    CHAR(3) NOT NULL DEFAULT 'USD',
  attributes  JSON,
  deleted_at  TIMESTAMP NULL,
  INDEX idx_venue (venue_id),
  FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE
);

CREATE TABLE tour_schedules (
  id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  tour_id     BIGINT UNSIGNED NOT NULL,
  starts_at   DATETIME NOT NULL,
  ends_at     DATETIME,
  capacity_override INT,
  status      ENUM('on_sale','paused','sold_out','cancelled','completed')
              NOT NULL DEFAULT 'on_sale',
  INDEX idx_tour_starts (tour_id, starts_at),
  FOREIGN KEY (tour_id) REFERENCES tours(id) ON DELETE CASCADE
);

CREATE TABLE ticket_tiers (
  id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  schedule_id BIGINT UNSIGNED NOT NULL,
  name        VARCHAR(128) NOT NULL,
  price       DECIMAL(10,2) NOT NULL,
  capacity    INT,
  sold        INT NOT NULL DEFAULT 0,
  INDEX idx_schedule (schedule_id),
  FOREIGN KEY (schedule_id) REFERENCES tour_schedules(id) ON DELETE CASCADE
);
```

Theaters / concert venues / escape rooms reuse this schema with different
UI naming ("Showtime" instead of "Departure").

## Marketing

```sql
CREATE TABLE email_templates (
  id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  venue_id    BIGINT UNSIGNED NOT NULL,
  slug        VARCHAR(64) NOT NULL,
  name        VARCHAR(150) NOT NULL,
  kind        ENUM('generic','welcome','order_confirmation','reservation',
                   'marketing','transactional','custom') NOT NULL DEFAULT 'generic',
  subject     VARCHAR(255) NOT NULL,
  body        MEDIUMTEXT NOT NULL,
  is_active   TINYINT(1) NOT NULL DEFAULT 1,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_venue_slug (venue_id, slug),
  FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE
);

CREATE TABLE campaigns (
  id              BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  venue_id        BIGINT UNSIGNED NOT NULL,
  channel         ENUM('email','sms','push') NOT NULL DEFAULT 'email',
  subject         VARCHAR(255) NOT NULL,
  body            MEDIUMTEXT,
  segment_json    JSON,
  template_id     BIGINT UNSIGNED,
  recipient_count INT NOT NULL DEFAULT 0,
  sent_count      INT NOT NULL DEFAULT 0,
  failed_count    INT NOT NULL DEFAULT 0,
  status          ENUM('draft','queued','sending','sent','partial','failed','cancelled')
                  NOT NULL DEFAULT 'draft',
  scheduled_for   TIMESTAMP NULL,
  created_by      BIGINT UNSIGNED,
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_venue_created (venue_id, created_at),
  FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE
);

CREATE TABLE campaign_recipients (
  id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  campaign_id BIGINT UNSIGNED NOT NULL,
  customer_id BIGINT UNSIGNED,
  email       VARCHAR(255),
  phone       VARCHAR(32),
  name        VARCHAR(255),
  status      ENUM('pending','sent','failed','bounced','unsubscribed')
              NOT NULL DEFAULT 'pending',
  error       TEXT,
  sent_at     TIMESTAMP NULL,
  INDEX idx_campaign (campaign_id),
  FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
);

CREATE TABLE campaign_tracking (
  id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  campaign_id BIGINT UNSIGNED NOT NULL,
  recipient_id BIGINT UNSIGNED NOT NULL,
  email       VARCHAR(255),
  token       VARCHAR(64) NOT NULL,
  open_count  INT NOT NULL DEFAULT 0,
  click_count INT NOT NULL DEFAULT 0,
  first_opened_at TIMESTAMP NULL,
  first_clicked_at TIMESTAMP NULL,
  last_ip     VARCHAR(45),
  last_user_agent VARCHAR(500),
  UNIQUE KEY uniq_token (token),
  INDEX idx_campaign (campaign_id)
);

CREATE TABLE campaign_clicks (
  id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  campaign_id BIGINT UNSIGNED NOT NULL,
  recipient_id BIGINT UNSIGNED NOT NULL,
  token       VARCHAR(64) NOT NULL,
  label       VARCHAR(64),
  url         TEXT,
  ip          VARCHAR(45),
  user_agent  VARCHAR(500),
  clicked_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_campaign (campaign_id)
);
```

## Safety (cross-cutting)

```sql
CREATE TABLE audit_log (
  id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  venue_id    BIGINT UNSIGNED NOT NULL,
  actor_user_id BIGINT UNSIGNED,
  actor_kind  ENUM('user','chatbot','cron','adapter','api') NOT NULL,
  entity_type VARCHAR(64) NOT NULL,
  entity_id   BIGINT UNSIGNED,
  action      VARCHAR(64) NOT NULL,
  before_json JSON,
  after_json  JSON,
  reason      TEXT,
  reversible  TINYINT(1) NOT NULL DEFAULT 1,
  reverted_at TIMESTAMP NULL,
  reverted_by BIGINT UNSIGNED,
  ip          VARCHAR(45),
  user_agent  VARCHAR(500),
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_venue_created (venue_id, created_at),
  INDEX idx_entity (entity_type, entity_id),
  FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE
);

CREATE TABLE chat_messages (
  id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  venue_id    BIGINT UNSIGNED NOT NULL,
  user_id     BIGINT UNSIGNED,
  conversation_id VARCHAR(64) NOT NULL,
  role        ENUM('user','assistant','tool','system') NOT NULL,
  content     MEDIUMTEXT,
  tool_calls  JSON,
  tool_result JSON,
  tokens_in   INT,
  tokens_out  INT,
  llm_model   VARCHAR(64),
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_venue_convo (venue_id, conversation_id, created_at),
  FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE
);

CREATE TABLE tool_calls (
  id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  venue_id    BIGINT UNSIGNED NOT NULL,
  user_id     BIGINT UNSIGNED,
  conversation_id VARCHAR(64),
  tool_name   VARCHAR(64) NOT NULL,
  args        JSON,
  result      JSON,
  duration_ms INT,
  idempotency_key VARCHAR(64),
  audit_log_id BIGINT UNSIGNED,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE KEY uniq_idempotency (idempotency_key),
  INDEX idx_venue_created (venue_id, created_at),
  FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE
);

CREATE TABLE confirmations (
  id          BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT,
  venue_id    BIGINT UNSIGNED NOT NULL,
  user_id     BIGINT UNSIGNED,
  conversation_id VARCHAR(64),
  pending_tool VARCHAR(64),
  pending_args JSON,
  reason      TEXT,
  expires_at  TIMESTAMP NOT NULL,
  status      ENUM('pending','approved','denied','expired') NOT NULL DEFAULT 'pending',
  resolved_at TIMESTAMP NULL,
  INDEX idx_venue_status (venue_id, status),
  FOREIGN KEY (venue_id) REFERENCES venues(id) ON DELETE CASCADE
);
```

## Multi-tenancy enforcement

Every query MUST filter by `venue_id`. The orchestrator binds `venueId`
to the session and refuses to act on a different one.

Belt-and-braces:

- **Application-side query helper** that requires `venue_id` on every CRUD
  call.
- **Database-side row-level security** (Postgres native; MySQL via views).
  Recommended once you hit 100+ venues.

## Indexing

- Every table with `venue_id` indexes it first.
- Multi-column indexes ordered by `venue_id` first.
- JSON `attributes` not indexed by default. If a specific attribute
  becomes a hot filter, add a generated column + index.

## Migrations

- Every schema change is a versioned migration.
- Backwards-compatible deploys: new column nullable + default; only
  enforce NOT NULL after backfill.
- Never drop a column in the same release that stops writing to it. Wait
  one release cycle.

## Deliberately omitted

- Spa appointments — add when a spa customer signs up
- Multi-location chains — single-location only; add `location_id` later
- Loyalty / points — Phase 6+
- Subscription billing for venues — handled by Stripe, not in this DB
- Email-to-bot inbound parsing — Phase 6+

Add tables when a paying customer needs the feature, not before.
