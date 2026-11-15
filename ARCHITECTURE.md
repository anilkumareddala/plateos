# PlateOS SaaS Architecture — implementation blueprint

## Current deliverable

This iteration is a browser-only demonstration with realistic user journeys. It is not yet a deployed SaaS, real-time backend, payment processor, device-management service, fiscal receipt engine, or legally compliant restaurant POS. UI modes share a browser-persisted mock order/inventory store and are scoped to an active brand/location.

## Target system boundaries

```text
Guest QR Web / Kiosk PWA ─┐
POS Register / Handheld ──┼──> API Gateway + Identity ──> Tenant API (menus/pricing/orders)
Back Office Web ──────────┤                              |                 |
Kitchen Display PWA ──────┘                              |                 +-- Postgres + row-level tenant security
                                                         +-- Transactional Outbox
                                                               |
                                                               v
                                                       Order event broker
                                                         /       |       \
                                                      KDS WS   Receipts   Reporting

Payments: provider-controlled tokenization/terminals; webhooks -> Payment Service -> Outbox
Device heartbeat: device service -> status monitor (per location)
```

## Tenant model and authorization

- Tenant = restaurant organization / contracted customer. Each tenant has multiple brands; each brand has multiple locations. One identity may have memberships in multiple tenants, with location-scoped privileges.
- Every mutable domain record is explicitly tenant-scoped. Put `tenant_id` on every transaction and tenant-owned reference table; use foreign keys that include tenant identifiers where appropriate.
- The server **never trusts tenant_id, location_id, price, discount or tax from the client** without authorization and recomputation. Auth derives permitted scopes from membership. PostgreSQL RLS is defense in depth, not a replacement for application authorization.
- Owner vs GM vs cashier vs cook vs guest authorization is enforced on every endpoint; staff authentication uses audited role and location assignments. Kiosks get short-lived, location-bound device credentials with minimal actions.

## Suggested service/modules

| Module | Capabilities |
|---|---|
| Tenancy / identity | SSO/email login, memberships, invitations, roles, location switcher, device tokens |
| Catalog | Menus, dayparts, location override, item variants, modifier cardinality, item 86/sold-out flags |
| Ordering | Draft cart, server price quote, validated place order with idempotency key, order state |
| Kitchen | Route items to stations, per-line ready state, cook-time telemetry, expo, bump/reopen |
| Payments | Certified terminal integration, payment intent, capture, refund, tips, settlement, webhooks |
| Service | Table assignment, courses, split checks, takeout delivery handoff |
| Reporting | Sales summaries, tax, comps/voids, channel mix, labor and menu mix |
| Devices | Enrollment, heartbeat, printer routing, firmware/config, offline sync |
| Audit | State transitions, item availability changes, staff overrides, reconciliation changes |

## Example endpoint contract

- `GET /v1/brands` — all brands authorized for caller.
- `GET /v1/locations/:locationId/menu?at=...` — server-effective menu and daypart, stock and price.
- `PATCH /v1/locations/:locationId/item-availability/:itemId` — staff-only mark sold-out/in-stock, with audit event.
- `POST /v1/locations/:locationId/order-quotes` — validate cart modifiers and return calculated line totals/tax.
- `POST /v1/locations/:locationId/orders` — commit quote, require `Idempotency-Key`.
- `GET /v1/locations/:locationId/kitchen/tickets?station=...` — read queue and resume cursor.
- `PATCH /v1/locations/:locationId/kitchen/ticket-lines/:lineId` — per-item workflow with version number / optimistic lock.
- `GET /v1/locations/:locationId/events` — SSE/WebSocket KDS updates with event IDs and resync.

## Core relational model

```sql
CREATE TABLE tenants (
  id uuid PRIMARY KEY, name text NOT NULL
);
CREATE TABLE brands (
  id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES tenants(id), name text NOT NULL
);
CREATE TABLE locations (
  id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES tenants(id),
  brand_id uuid NOT NULL REFERENCES brands(id), name text NOT NULL,
  time_zone text NOT NULL
);
CREATE TABLE orders (
  id uuid PRIMARY KEY, tenant_id uuid NOT NULL REFERENCES tenants(id),
  brand_id uuid NOT NULL REFERENCES brands(id),
  location_id uuid NOT NULL REFERENCES locations(id),
  order_number bigint NOT NULL, channel text NOT NULL,
  status text NOT NULL, subtotal_cents bigint NOT NULL,
  tax_cents bigint NOT NULL, total_cents bigint NOT NULL,
  currency char(3) NOT NULL DEFAULT 'USD', created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE (tenant_id, location_id, order_number)
);
-- Add tenant-scoped menu/modifier tables, order lines, payment records,
-- station-ticket lines and an immutable audit/outbox log.
```

The skeleton illustrates explicit tenant IDs; a real migration should add **composite tenant-owned foreign keys** and row-level security policies for every applicable table, along with required constraints/indexes.

## Reliability and edge cases

1. Validate a modifier's minimum/maximum choices and availability at checkout on the server; reject stale prices. Never rely on UI-disabled controls alone.
2. On order creation, atomically write order + line items + kitchen outbox event. A background relay publishes after commit, retries safely; consumers deduplicate by event ID.
3. Implement KDS reconnects with cursor resume and full snapshot reconciliation. Support per-station completion and conflict handling on multiple KDS screens.
4. Keep POS and KDS functioning under interrupted connectivity using scoped encrypted outbox/cache where hardware policy allows, with explicit staff guidance for offline sales. Avoid duplicate captures/orders during replay.
5. For QR order placement, calculate pricing and tax at the chosen location; prohibit cross-location product injection and handle menu changes without silent repricing.
6. Protect sensitive actions (void, discount, refunds, comp, shift-close) by location RBAC + manager override + audit reason.
7. Expand test suite: e2e kiosk→KDS, tenant isolation, modifier validation, stale availability, payment webhook duplicate, printer failure, and offline recovery.

## Implementation milestones

- **M1 (delivered):** Responsive shell, demo brand/location scoping, kiosk/QR preview, modifiers, stock flags, cart, POS, live-in-browser kitchen queue, back-office pages.
- **M2:** API, database, auth/RBAC, server-side pricing, true streaming events, admin CRUD, integration tests.
- **M3:** PCI-provider payment terminal integration, receipts/printers, refunds/tips, cash management, reconciliation.
- **M4:** Offline resilience, device enrollment, observability, production reporting, compliance and deployment automation.

## POS Register / Server Handheld (added prototype module)

### Domain objects in the mock store

- `checks[]`: `id`, `brandId`, `locationId`, `service`, `table`, `guestName`, `units[]`, `parts[]`, `status`, optional `loyaltyId`. Each `unit` represents one ordered item for item-level splitting and contains `id`, menu item, price in cents, modifiers, kitchen notes, and a `sent` flag.
- `parts[]` per check: `id`, `unitIds` when item-assignable, `amountCents`, `kind` (`items` or `amount`), `paid` and payment reference. Even and custom splits allocate currency in integer cents; item splits allocate the current part's amount proportionally and conserve every cent. Paid parts are immutable in the UI.
- `payments[]`: illustrative tender, tip, discount, loyalty redemption, method, backup-reader flag, local sync state, simulation marker. **Not a real ledger** or gateway transaction.
- `offlineQueue[]`: demo FIFO local events for pending kitchen orders and cash records. On restoring simulated connectivity, a replay guard deduplicates kitchen order IDs in the current browser store.
- `posSettings[brandId:locationId]`: simulated connection, backup reader selection, and illustrative cash dual-pricing toggle.
- `loyalty[]`: fictional brand-scoped guest wallets; `invoices[]`: fictional tenant/location-scoped catering invoices and preview-only URLs.

### Production APIs & services to add

| API / event | Required behavior |
| --- | --- |
| `POST /v1/locations/{id}/checks` | Create table/counter/takeout/bar tab check; reject duplicate open table checks; enforce tenant/location authorization |
| `POST /v1/checks/{id}/lines` | Verify menu version, availability, modifier constraints; price atomically and append an ordered unit batch |
| `POST /v1/checks/{id}/send` | Idempotent per unsent batch; produce transactional outbox event for routed KDS tickets |
| `POST /v1/checks/{id}/split` | Validate whole-cent conservation, tax allocation, split child lineage, no paid-part reallocation, optimistic revision |
| `POST /v1/checks/{id}/merge` | Lock both checks, same tenant/location, refuse paid or incompatible states; retain audit trail and original lineage |
| `POST /v1/checks/{id}/payment-intents` | Authorize the selected check part with processor, handle terminal session and failover capabilities; never accept offline card swipes as successful |
| `POST /v1/payments/webhooks` | Signed, idempotent provider webhooks with an immutable ledger, refund support, dispute states and settlement reconciliation |
| `GET /v1/tables`, `GET /v1/checks` | Scoped, role-aware data including open occupancy, computed balances, and stable revision numbers |
| `POST /v1/loyalty/lookup`, `.../redeem` | Rate-limited lookup with verified identity; atomic points redemption and earning tied to settled payments |
| `POST /v1/catering/invoices` | Generate hosted, expiring payment links through processor; email delivery and reconciliation; authenticated customer access |
| `POST /v1/devices/sync` | Device-enrolled, encrypted, idempotent offline replay with monotonic sequence numbers, offline caps and reconciliation |

**Key invariant:** All check and payment mutations must include a server-validated tenant and location scope. A server-owned currency ledger must ensure that **sum of child parts + credits + settled amounts = original check gross total** even across repeated splits, refunds and merged checks. Prevent changes to already settled portions. Maintain atomic inventory consistency and order version conflict handling.

### Payment-processor and regulatory boundaries

- EMV/contactless readers (including Clover Go) are not interchangeable through an app-level toggle alone. Confirm provider API support, merchant account compatibility, certified devices, fallback policies and reconciliation before shipping.
- Card and QR Pay-at-Table must be processed with supported certified hardware, payment intent APIs, hosted checkout, and verified webhooks; card details must never enter the app's own database or localStorage.
- Offline cash requires signed device identity, secure local persistence, auditable receipt/number sequences, sync and reconciliation policies, loss/conflict recovery, access controls and restricted actions. An offline browser tab cannot promise safe auto-sync or revenue integrity.
- Dual pricing / cash discounts require local legal, processor, card-network, tax and receipt/disclosure review. The prototype's **3% illustrative discount** is not a legal rate recommendation.
- Loyalty redemption and invoice payments must only settle after confirmed server-side payment statuses; prevent redemption/award race conditions, duplicates and abuse.


---

## PlateOS v3 architecture — Omnichannel, KDS and Device Operations

### Canonical ticket ingestion and source adapters

```text
POS / Handheld / Table QR / Kiosk / Website
AI Phone Provider → Signed Webhook Adapter
Uber Eats / DoorDash / Grubhub / Zomato / Swiggy → Provider Adapters
                         │
               API gateway / tenant resolver
                         │
           Idempotent order ingestion service
    [signature validation, store mapping, source-order key,
     menu/modifier mapping, validation, price reconciliation]
                         │
         PostgreSQL transaction + outbox event
                         │
   event bus (order.created / order.updated / order.cancelled)
             ├── KDS station ticket projector
             ├── POS + owner order read models
             ├── customer status service
             └── delivery acknowledgement callbacks
```

**Canonical order fields**: `tenant_id`, `location_id`, `order_id`, `channel`, `channel_order_id`, `source_event_id`, `service_type`, `table_id?`, `check_id?`, `created_at`, `status`, `amounts`, `tax`, `payments`, `order_lines` (quantity, modifiers, notes, station, state), `integration_ref`, `provider_ack_state`. Enforce a unique `(tenant_id, location_id, channel, channel_order_id)` and an independent event idempotency key; reject/merge duplicates on retry, never double-fire kitchen tickets. Provider menu item identifiers must be mapped to internal IDs before accepting an external order. Validate cancellations and changes against ticket state and channel support. Most marketplaces have independent tax/pricing calculations; reconciliations are mandatory.

**Simulated v3 implementation**: `db.orders[]`, `origin:'injected-simulated-adapter'`, and `prepLines` are browser-local. There are no provider secrets, subscription callbacks or remote events.

### Kitchen ticket state machine

Suggested production tables:

```sql
kitchen_ticket(
  tenant_id, location_id, id, order_id, created_at, version, status
)
kitchen_ticket_line(
  tenant_id, location_id, id, kitchen_ticket_id, order_line_id,
  station_id, qty, prep_status, assigned_at, started_at, ready_at,
  completed_at, version
)
station_route(
  tenant_id, location_id, category_id, station_id,
  optional_item_override_id, priority
)
kitchen_ticket_event(
  tenant_id, location_id, ticket_line_id, actor_device_id,
  transition, occurred_at, idempotency_key, revision
)
```

A bump is a `new → preparing → ready → completed` transition with optimistic locking and authorized station/device identity. Reject stale bumps from a second KDS screen or duplicate event. Compute aggregate order status only from all active station line statuses. Ticket aging / SLA thresholds must use trusted server time (not the browser device clock). KDS screens subscribe to a tenant/location/station-filtered event stream and replay from a durable cursor after reconnect.

### Floor occupancy and table state

Production occupancy is primarily derived from table/check state, not a kitchen ticket alone. Relationship: `floor_zone → floor_table → service_session → check → order`. Bind check creation/close/transfer and kitchen ticket events to a materialized floor read model. Account for check merge/split, table transfer, paid-but-seated checks, table resets and shared tables. The v3 UI derives these states from open mock POS checks and existing order tickets only.

### Devices health, discovery and printing

Recommended infrastructure: a per-location **trusted on-premise print/device agent** running on supported hardware, registered through device credentials and certificate-backed identity. Agent securely enumerates devices through approved OS drivers / mDNS / SNMP where permitted, identifies supported printer models and registers IP/USB/Bluetooth endpoints. Device heartbeats/last seen are ingested server-side and surfaced via WebSocket; heartbeat expiration marks offline after configurable grace period. Firmware/device capabilities, station printer routing, print queue retry/deduplication, paper and cover states (when supported), automatic failover, and test-print audit should be included. Never expose admin LAN scan endpoints or print raw network commands from a public browser. The **v3 Discover/Test print** controls change only mock records and cannot access devices.

### Security and quality gates

- Require server-side tenant ID from authenticated membership and validate location membership for *every* read/write and subscription. Prevent external webhook source store IDs from choosing a tenant outside the adapter's enrolled account.
- Keep provider credentials encrypted and rotated; verify webhook signatures and timestamp/replay windows. Rate limit ingestion, log source order IDs and verify menu mapping.
- Persist audit trails for voids, station bumps, changes to availability/routing, device enrollment, printer diagnostics and payment state.
- For production mobile/offline operations, use secure storage, ordered outbox with idempotency and conflict resolution; no reliance on `localStorage` as a financial record.
- Load-test busy hour spikes, mixed station tickets, cancellations, offline reconnect, out-of-order provider retries and per-location device failures before pilots.


---

## v4 · Back-office production architecture

### Tenant, location and catalog schema

Use these relationships under a tenant-enforced authorization boundary:

```
tenant(id)
  └─ location(id, tenant_id, timezone)
  └─ category(id, tenant_id, name, sort_index)
  └─ item(id, tenant_id, category_id, base_price_minor, active, photo_asset_id)
  └─ modifier_group(id, tenant_id, required, min_select, max_select)
        └─ modifier_option(id, group_id, price_delta_minor)
  └─ item_modifier_group(item_id, modifier_group_id)
  └─ location_item_price(tenant_id, location_id, item_id, override_price_minor)
  └─ location_item_availability(tenant_id, location_id, item_id, disabled_at, until_at, by_user_id, reason, version)
  └─ location_daypart(tenant_id, location_id, name, start_local_time, end_local_time)
  └─ item_daypart(tenant_id, item_id, daypart_id)
  └─ location_item_hours(tenant_id, location_id, item_id, local_start_time, local_end_time)
```

- Include tenant ID and authenticated branch membership in every read/write. Apply composite foreign keys, PostgreSQL RLS where appropriate, and strict object-store tenant isolation for uploaded photos. Disallow cross-tenant references even through guessed IDs.
- Price/availability changes are versioned and published with a durable outbox. Validate schedule and stock at **server-side checkout**, capture a priced-order snapshot, and reject stale carts with a helpful reprice/unavailable response. Multiple simultaneous kiosks must not oversell stock; use inventory reservations or atomic decrements when inventory counts are implemented.
- Store explicit IANA branch time zones. Evaluate time windows against local wall clock, accounting for DST gaps/folds and midnight crossing; expiry is an absolute UTC instant. Use expiration jobs / cache invalidation plus read-time checks so stale local clients cannot bypass 86 expiration or stockouts.
- Photo upload: signed uploads, verified image type and dimensions, malware scanning as appropriate, image transformation/CDN, accessible alt text, tenant-level object ACLs and file-size limits. Browser base64 stored in `localStorage` is temporary demo-only behavior.

### Employee identity, timekeeping and corrections

```
employee(id, tenant_id, role, status, pay_rate_minor, ...)
employee_location(employee_id, location_id, role_override, ...)
punch_event(id, tenant_id, location_id, employee_id, action, occurred_at_utc, device_id, created_at_utc, idempotency_key)
punch_correction(id, punch_event_id, old_effective_at_utc, new_effective_at_utc, manager_id, reason, created_at_utc)
```

- Treat punches as append-only and corrections as separate versioned records; a projection supplies the latest effective punch while preserving original values and every prior revision. Strong audit protections require write-once/retention controls, immutable or externally sealed logs, and separation of duties for approval.
- Require user login/device enrollment plus a PIN verified server-side against a slow salted password hash (or managed credential verifier), rate limit attempts, protect against replay, and prevent sharing global PINs across organizations. Never ship valid PIN secrets in frontend JavaScript.
- Time clock calculations must handle multiple shifts, breaks, overtime, DST, rate changes, corrections and jurisdictional labor-law requirements. Manager changes may require employee acknowledgments and payroll-integrated history. Do not use mock accrued labor as finalized payroll.
- Define tip pool policy (eligibility, split formula, tip pooling restrictions by jurisdiction, time window, credit/cash separation, rounding, payouts, tax/export) per location with audit and employee statements. Card tips should be reconciled against real settled payment records rather than orders.

### Manager approvals / access control

- Server permissions: `owner`, `manager`, `cashier`, `server`, with tenant and location memberships plus granular scopes for `manage_menu`, `view_reports`, `view_labor`, `view_cash`, `void_item`, `discount_large`, `refund_payment`, and `cash_drawer_adjust`.
- For sensitive staff-initiated requests, create an `approval_request` with initiator, tenant/location, target entity/version, amount, action, mandatory reason, expiry and status. Manager authorization must be bound to that **specific** operation and version, not a generic session unlock. Revalidate target and scopes at commit.
- Record an append-only `security_event` with source device, actor, approver, reason, before/after, idempotency key and UTC timestamp; forward to immutable or remotely retained security logging. All drawer/refund mutations must be transactional and reconcile with cash books, payment provider and tills. High discounts and certain refunds may require stricter tiered approval thresholds.
- The v4 **role selector and example PINs are demonstration conveniences**. They do not enforce real identity, tenant or drawer authorization. The browser's audit history is not immutable against local tampering.

### Release caveats

PlateOS v4 is an **interactive standalone frontend**, not a certified POS, PCI-compliant payment processor, payroll system, or backend-driven SaaS. It uses `localStorage`/BroadcastChannel for demo synchronization only. Before selling to separate restaurants, build server tenancy, authorization and authentication, persistent transactional database, object/media storage, reliable outbox synchronization, receipts, certified payment/refund integrations, monitoring and backups. See the v1–v3 sections above for omnichannel and hardware production architecture.

---

# v5 — Production analytics, closeouts, reporting and owner companion

The v5 browser implementation is an interactive frontend demo, not a certified accounting backend. Its reporting artifacts, closeouts, scheduled-email settings, and natural-language answers currently operate on a browser-local dataset.

## Recommended production data path

1. Each paid `check_part` creates an immutable `payment_attempt`, `payment_authorized` and/or `payment_captured` event; recognize sales according to a documented accounting policy, independent of kitchen/aggregator order ingestion.
2. Preserve item-level line snapshots, modifiers, channel, location, service mode, server attribution, taxes, discounts, tips, fees, payment method, processor transaction ID, and timestamps.
3. Refunds and reversals append compensating ledger entries rather than mutating settled facts. Idempotency keys prevent duplicate webhooks/batch posting.
4. Feed an event-driven reporting read model, partitioned by `tenant_id` and keyed by `location_id`, `business_date` (restaurant timezone), channel, menu category/item, employee, and payment method. A fresh snapshot must reconcile to the primary payment ledger.
5. Role authorization checks must run in database/API before returning customer/financial data. The owner may query their own tenant's locations only, a manager only assigned locations, and service employees cannot read privileged financial totals.
6. Use indexable daily/hourly aggregates, query timeouts, and request limits to keep multi-location analytics fast; preserve drill-down to original ledger events and clear data-freshness indicators.
7. Exports run through a tenant-scoped report job, produce short-lived signed URLs with column-level permissions, and log who requested/downloaded each artifact.

Suggested durable tables: `payment_ledger_entries`, `order_line_snapshots`, `shift_registers`, `cash_count_events`, `register_movements`, `closeout_snapshots`, `card_processor_batches`, `report_definitions`, `report_schedules`, `report_job_runs`, `audit_events`, `report_exports` and `tenant_user_memberships`.

## Closeout / batch safeguards

- X report is a read-only snapshot.
- Z report should be an explicitly authorized, idempotent transaction scoped to `tenant_id`, `location_id`, `business_date`, `shift_id`; it should preserve the input ledger watermark, expected drawer math, counted cash, cash variances and approving manager. A closed shift requires documented late-posting adjustments.
- A processor batch is not settled when a button is clicked. Integrate the provider's official batch/settlement API and asynchronous webhook results, compare processor transaction totals with internal ledger, log pending/failed/reconciled states, and surface exceptions.
- Require dual control for cash variance thresholds; maintain tamper-evident logs and enforce retention, payroll and tax policies.

## Report scheduling

Store validated report grouping, date period, scope and signed-in creator. Run scheduled jobs only on backend task runners using the tenant's timezone, and send transactional mail via a verified provider. Enforce recipient allowlists and data-access consent; encrypt or expire exported attachments and record successful and failed deliveries.

## Natural-language analytics

v5's rules-based demo has no model inference. A production LLM feature must translate permitted user questions into validated preapproved metrics (not arbitrary SQL), apply server-side tenant/location authorization to every retrieval, clearly label fiscal definitions and time windows, disclose missing data, and log its evidence and calculation path. Responses should trace to specific aggregation job versions and payment ledger watermarks.

## Owner app deployment

The responsive owner viewport can be promoted to a PWA, followed by native packages if the market needs push alerts, mobile biometric auth, or deep platform integration. Use real-time WebSockets/SSE with reconnect and stale-data indicators; owners see only their own tenants, even across multiple branches.
