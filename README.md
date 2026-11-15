# PlateOS — Back Office Operations (Menu, People, Manager Controls)

**A single, self-contained interactive restaurant SaaS prototype.** Extract the release ZIP and open `index.html` in a modern browser. No install or server is needed to explore the screens. The implementation builds on the v3 omnichannel queue, KDS, floor/device views, POS and kiosk. This is a **local demo**, not a deployed multi-tenant backend or production payment/payroll system.

## What's new in v4

### Dynamic menu manager

- **Menu & inventory** → tabs for **Items**, **Categories**, **Modifier groups**, **Dayparts & hours**.
- Items can be created, edited and deleted; category and modifier-group CRUD is available with referential-deletion safeguards. Item editor includes name/SKU, description, category, prep station, base price, **per-location override**, dayparts, optional item-hour window, required group, optional add-on group, and **photo upload** (compressed client-side before storing locally). Changes propagate to the shared kiosk, QR/web preview, POS and simulated order source within the same browser.
- Required modifiers must be selected before an order can be added. Both optional and required **option upcharges** are reflected in item prices. Existing sample items are mapped to editable modifier groups.
- Configurable dayparts are **Breakfast 05:00–11:00**, Lunch 11:00–16:00, Dinner 16:00–22:00, **Late-Night 22:00–02:00** by default, using the chosen branch's configured time zone. Overnight windows are supported. Menu daypart picker can preview other dayparts, but ordering checks actual local daypart and location-specific item hours.
- **86** from back-office item list with manual/next 5PM/next morning/custom auto-return; **one-tap 86** or restore directly from POS cards. Item availability is shared across ordering surfaces and evaluated against expiry time. Visible pages refresh on a minute cadence (and same-origin tabs sync through localStorage/BroadcastChannel). Manual 86 stays unavailable until restored.
- Item catalog, categories and modifier groups are **tenant-level**; item 86 records, daypart schedules, item-hour windows and price overrides are **location-level**. Existing orders retain their original sale prices as snapshots.

### People, timecards, tips and labor

- **POS register → Time clock** opens a PIN modal supporting **Clock in**, **Start break**, **End break**, **Clock out**, with valid shift transitions. Also available from **People & labor**.
- Manager **Timecards & labor** shows per-punch records, effective timestamp, original timestamp, and edit history. **Correct** adds a distinct correction record without modifying the original punch; **Revision history** shows each change and reason. Managers and owners only can edit.
- **Labor cost % = estimated accrued hourly wages / net paid sales (excluding estimated sales tax)** for the selected branch. It is computed from demo punch durations, hourly rates and paid POS records, recalculating on each render. This is a demo KPI, not a compliant payroll or accounting calculation.
- **Tip pool** shows card and cash tips separately, with an illustrative weighted-hours allocation by eligible staff and per-employee breakdown. Tips from refunded payments are excluded. Illustrative paid payments and initial shifts seed a meaningful dashboard at the first location.

### Roles, manager overrides and security log

- A **Preview staff role** selector in the top bar (mobile: in sidebar) demonstrates Owner, Manager, Cashier and Server. Owner/Manager can access menu editing, reports, labor, cash controls and Security Activity; Cashier/Server see service modes but not restricted management views. **This is UI-only demonstration; anyone can change roles in the browser.**
- Register **Void** is supported for **unsent, unpaid item-based check lines**; previously sent items require a separate cancellation workflow not included here. **Large discount · 20%**, **Refund**, and **Cash drawer Paid-In, Paid-Out and Drop** are provided as demo actions.
- On Cashier/Server actions, a **Manager PIN + mandatory reason** is required. Managers and owners may approve their own action with a required reason. Successful operations append an entry in **Security Activity**, including time, action, initiating employee, approving employee, reason and details. Invalid PIN or insufficient reason does not authorize an override.
- All security/timecard records remain in browser storage only. They are **not tamper-proof**. Production must use server-signed identity, tenant-scoped authorization, hashed PIN verification with rate limits, an append-only audit ledger, payment processor refunds, and secure offline handling.

## Demo employee PINs — fictional, never production credentials

| Brand | Owner | Manager | Cashier | Server |
|---|---|---|---|---|
| Juniper & Co. | 1001 | 2002 | 3003 | 4004 |
| Saffron Table | 1101 | 2202 | 3303 | 4404 |

To demo a manager approval: select **Sam Patel · Cashier** (Juniper), open **POS register**, choose **Dine in → Table 04**, select **Void** beside an unsent item, enter manager PIN **2002** plus a reason of at least five characters, and approve. Switch to **Morgan Lee · Manager** → **Security activity** to see the complete event entry. You can also try **Large discount**, **Cash drawer**, or **Refunds**.

To demo menu availability: **Menu & inventory → 86 item → 86 until next 5PM**, then open **Self-order kiosk** or **POS** to confirm that item is disabled. To demo scheduling, open **Dayparts & hours** and adjust a boundary, or create an item with its own time window.

To demo timecards: choose **People & labor → Timecards & labor → Correct** and enter a new timestamp and reason. The original value stays visible; select **revision history** for the audit chain. The POS time clock accepts staff PINs for valid transitions.

## Validation

- `python test_ops.py` — menu/category/modifier CRUD, per-location pricing, daypart windows, scheduled 86 expiry semantics, persisted timecard corrections and revision history, PIN time clock, tips, permissions, manager approvals for void, discount, refund and drawer events, tenant scope and mobile layout.
- `python test_omni.py` — unified queue and all v3 KDS/floor/device flows including mobile.
- `python test_pos.py` — original POS workflow, splits, offline sync and catering invoices.

These tests use Playwright and a Chromium binary; the app itself needs only a modern browser. If this project is deployed on a web origin, its mock state synchronizes across tabs **of the same browser and origin**, not across restaurant devices.

---

# PlateOS — Multi-tenant Restaurant Operations Demo

An interactive, dependency-free demo of a B2B restaurant POS, guest kiosk/QR menu, unified omnichannel queue, station-routed KDS, live floor and device-health monitoring, and back-office. This is a **local mock prototype**, not a payment- or production-ready POS system.

## Run

Open `index.html` in a modern browser. No installation or build step is required. For local development with HTTP serving, run `python3 -m http.server 8080` in this directory and visit `http://localhost:8080`.

## Demo flows

1. Use **Brand** and **Location** switches in the top bar to change tenant scope.
2. Open **Self-order kiosk**. Choose a daypart, category, dish, required option (e.g. spice), and any optional add-ons. Add multiple dishes to the cart and **Place order**.
3. Open **Kitchen display**. The ticket appears in the **New orders** lane for its prep station; click **Bump ticket** to advance that station from New → Preparing → Ready → Completed.
4. Open **Menu & inventory**. Toggle any item to sold out. It is immediately disabled and badged as 86’d in the kiosk for that location, without affecting other locations.
5. Try **POS register** to send a staff ticket to the same kitchen queue.
6. View demo-scoped data in **Overview**, **Reports**, **Staff**, **Floor**, and **Devices**.
7. For cross-tab synchronization, open two tabs on the same browser origin. The mock state uses `localStorage` and `BroadcastChannel`.

## Architecture, current milestone

- **Data isolation**: `brandId` + `locationId` are explicit on each order; 86'd item state uses `brandId:locationId` keys. All selectors and views scope to the active location.
- **Single source of truth**: browser-persisted mock DB (`plateos-mock-db-v1`). Kiosk and POS submit to the same `orders[]`, consumed by KDS, dashboard, and reports. The KDS tracks each ticket line by prep station; the aggregate order lifecycle is `new → preparing → ready → completed`.
- **Business constraints**: prices recomputed from modifiers at order time; required selection enforced; unavailable products are disabled in the menu and validated again before order submission. Uses a demo-only 8.25% tax rate.
- **Dayparts**: location time zone drives the auto selection; demo users may override to Breakfast, Lunch, or Dinner. Menu items have explicit `days[]` availability.
- **UX**: responsive desktop/tablet/mobile shell, large action targets, category browsing, search, item configuration modal, location switcher, mobile cart.

## Before selling as a production SaaS

The prototype deliberately has **no backend, real payment processing, authentication, or persistent real-time server**. Recommended production architecture:

- **Frontend**: Next.js/React + TypeScript for Back Office; tablet-safe PWA clients for POS/KDS/Kiosk; a hosted QR storefront with tenant-specific branded URLs.
- **Backend**: TypeScript/NestJS or Kotlin/Spring Boot; PostgreSQL with strictly enforced tenant/brand/location boundaries (tenant key on every scoped table, RLS defense in depth); Redis for transient routing; event bus for order events; WebSocket/SSE for live kitchen feeds.
- **Core tables**: `tenants`, `brands`, `locations`, `users`, `memberships`, `roles`, `devices`, `menus`, `menu_items`, `modifier_groups`, `modifier_options`, `item_availability`, `orders`, `order_lines`, `line_modifiers`, `payments`, `refunds`, `kitchen_tickets`, `ticket_line_status`, `audit_events`.
- **Reliable order submission**: server-assigned order numbers scoped per location; idempotency keys on placement and payment callbacks; pricing/tax recomputation on the server; transactional order + outbox event creation. Kitchen station routing with per-line preparation state, retry/replay semantics, and offline device resilience.
- **Payments**: use a PCI-compliant payment provider and supported certified hardware. Never store raw PAN/card data. Handle capture, tipping, refunds, split tender, settlement, taxes, and reconciliation through audited payment flows.
- **Security**: tenant-aware authN/authZ with least-privilege location RBAC, device enrollment, short-lived credentials, encrypted secrets, signed webhook verification, rate limits, immutable audit trails, backups and data retention.
- **Ops**: per-location terminal health, uptime monitoring, automated tests for tenant boundaries, contract tests, staged deployments and data migration process, SLOs and alerts.

## Limitations of this demo

- All figures, orders, staff, devices and locations are fictitious demo data.
- Tax percentage is a mock fixed value; real tax computation is location-, item-, and service-dependent.
- KDS station routing and independent station status are implemented in the browser mock; production needs device-authorized station updates, retries, deduplication and reconciliation.
- No actual guest checkout, payment, hardware connection, or networking exists. "Live" describes immediate mock-client updates, not a hosted production service.
- Browser storage can be cleared with developer tools. This is not secure multi-tenant persistence; it's a scoping demonstration.

## Standalone QR storefront preview

The admin kiosk page has **Preview guest storefront** and **Copy QR link** actions. Guest preview hides all management navigation. The link uses the parameters `?guest=1&brand=juniper&location=uptown&channel=qr`; when the app is hosted over HTTPS, opening that link provides the standalone guest ordering UI, and orders created there are labeled `Table QR`. To share it to a real guest device, host the static app at an accessible URL; opening `file://` is only a local demo.

## NEW — POS Register & Server Handheld (interactive module)

Select **POS register** in the sidebar. The same interface works as a desktop register or a touch-friendly handheld (switch using **Register / Server handheld**). Existing kiosk, KDS, and back-office views remain available. POS checks are isolated by both the selected brand and location.

### Order taking and kitchen routing

1. Select **Dine in** → choose a table from the floor map, or start a **Takeout**, **Counter**, or **Bar tab** check. A bar tab requires a guest name. The **Floor & tables** management page uses these same open checks; tapping a table there opens the POS.
2. Add an item. Required modifier groups block the **Add** action until selected; optional add-ons adjust the unit price. Add free-text **Kitchen notes** for the line item (e.g. allergy instructions).
3. Choose **Send to kitchen**. Only unsent line items are sent, allowing multiple rounds of service on one check without resending old items. The new ticket appears in the location-specific KDS. Notes and modifiers are visible on tickets.
4. Demo checks are seeded for **Juniper & Co. / Dallas · Uptown** at tables **04, 08, 12**, plus a **Taylor Brooks** bar tab. Saffron Table has its own sample check. The simulated restaurant data is fictional.

### Splitting and merging

- Choose **Split** on an open check, select an unpaid part, and split **Evenly** (2–8 ways), **By items** (individual quantity-1 units), or by **Custom dollar amount**. Parts include proportional tax. You can select a newly created part and split it again, without disturbing paid parts.
- Choose **Merge** on an open dine-in table check and select another unpaid dine-in check in the *same location*. The source table becomes available, and its line items and unpaid bill parts transfer to the destination. Merging checks with paid portions is intentionally blocked.
- Each part can be paid separately. A check closes only after all its parts have simulated payment records. Once closed, its table becomes available again.

### Payments, cash pricing, tipping, loyalty

- **Tap / Chip / Swipe**: choose the card entry mode and toggle the simulated **Backup Clover Go Reader** selection. These are illustrative device/processor interfaces only; no physical device is contacted and no payment is authorized.
- **Cash**: enter cash tender, optional tip, and inspect change due. Cash may be recorded offline.
- **QR Pay-at-Table**: select it for a dine-in check, copy the *local demo* payment URL, or use **Simulate payment**. For cross-device real QR checkout, integrate a hosted payment provider and backend.
- **Cash dual pricing**: enable **Cash dual pricing** in the POS toolbar. Checkout and **Customer-facing display** then show the unadjusted card price and a **3% demo cash discount**. The discount is applied only to cash records. Pricing and taxes are demonstrative, not a legal/compliance configuration.
- **Tipping**: choose no tip or 10%, 15%, 18%, or 20% for card/cash/QR demo payments.
- **Loyalty**: in checkout enter the fictional phone **5551234567** (or **5559876543** for Juniper); lookup and redeem points at **100 points = $1**, earning **1 point per $1** paid before tips. The loyalty wallet is scoped to the restaurant brand.
- **Catering invoices**: from the POS heading choose **Catering invoices**; enter name, email, dollar total and memo; generate a **demo preview link**. The link is *not a real payment link* and cannot be shared to browsers without the same local mock data. A mock invoice payment state can be simulated.

### Offline simulation and queue

1. Select **Simulate offline**. The amber banner reports the count of queued local events. Send an order: it is added to a browser-side queue and intentionally **does not** appear in KDS yet.
2. Select **Checkout** on a check, choose **Cash** (card and QR are disabled), enter sufficient tender, and record it. The local transaction is marked `pending_sync`, and an event is queued.
3. Select **Restore connection**. The queue automatically replays **once** into the mock local data store and the tickets appear in KDS. The browser `online` event also triggers replay if offline simulation is disabled.

**Important:** This queue is a browser `localStorage` and `BroadcastChannel` mock. It is **not a reliable offline sync protocol** or a financial source of truth; it has no server durability, conflict resolution, reconciliation, or secure multi-device storage.

### Demo vs. production

The module intentionally simulates payments, loyalty and invoicing and does not collect bank/card information. Do **not** use this demo to accept real payments or manage real cash drawers. For commercial operation implement certified hardware/processor integrations, PCI-scoped checkout, payment-webhook reconciliation, device-authenticated encrypted offline storage, durable transaction and order idempotency, tax computation by location, legal cash-discount disclosure, and server-side tenant authorization.


---

# NEW — v3 Omnichannel Order Queue, Station KDS & Live Operations

The existing kiosk, POS/handheld, check splitting, simulated payments, catering, menu, reports, and owner dashboard remain in the same `index.html`. This version adds three integrated experiences in the sidebar:

### Omnichannel orders

- **Unified location-scoped order stream** with source badges, age, kitchen status, order value, service type, menu lines, a ticket detail drawer, live counts, and overdue indicators.
- Channels are **POS Register**, **Server Handheld**, **Table QR**, **Self-Order Kiosk**, **Website**, **AI Phone Assistant**, **Uber Eats**, **DoorDash**, **Grubhub**, **Zomato**, and **Swiggy**. The Kiosk and POS write to the same `orders[]` array; seeded third-party/AI/website orders and the channel simulator are **fictional demo adapter data**.
- Filter by status/channel, search ticket number, item or table, and select **View ticket** to inspect line-item station assignment and preparation state.
- To demo a new marketplace ticket: select **DoorDash** (or any channel) in **Channel simulator**, choose a menu item and quantity, then press **Simulate incoming order**. It appears in the unified queue **and** KDS immediately. This does not authenticate to or ingest data from real marketplace APIs.
- Regular POS register orders now identify as **POS Register** and POS orders created with the **Server handheld** layout identify as **Server Handheld**. Standalone guest (`?guest=1&...`) orders identify as **Table QR** by default or **Website** when `channel=website` is supplied.

### Station-routed Kitchen Display System

- Station tabs: **All stations**, **Grill**, **Tandoor**, **Fry**, **Bar**, **Cold**.
- Each incoming order receives persistent `prepLines` at initial creation/first migration. Prep lines contain the menu index, assigned station, and stage. Status is maintained **independently for each kitchen station**; a Bar bump never changes the Grill lines from the same guest order.
- Auto-route using branch-specific menu category rules, with item-level overrides: for example Tikka/Paneer/Naan → Tandoor, samosas/fries/cauliflower → Fry, drinks → Bar, cold dishes → Cold, most mains → Grill. Choose **Station routing** to edit per-category routing for **future** orders at the selected branch. Existing tickets retain their assigned station.
- Ticket timer from `createdAt` is color-coded **green under 8 minutes**, **amber 8–14 minutes**, **red 15+ minutes**. The timer refreshes every 15 seconds while the view is visible. Every station ticket has a 48px+ **Bump ticket** control, advancing New → Preparing → Ready → Completed.
- The unified order status becomes Ready only when **all station portions** are Ready or completed. The order is Completed when all portions are bumped complete. The same branch order also appears in the owner dashboard and reports.

### Live Floor & Tables

- **Floor & tables** shows 15 interactive tables divided into **Dining room**, **Patio**, and **Bar area**, with a zone switch, occupancy, open-check monetary value, related active kitchen ticket count, seated duration, and derived state (Available, Order taking, In kitchen, Ready to serve, Occupied).
- Select a table to open its existing check in POS or create a new table check. A table releases when its check closes.
- Data is scoped by selected restaurant brand/location. Live activity is derived from POS checks plus KDS ticket status; there are **no occupancy sensors**.

### Live Devices & Hardware

- Each demo branch has seven individual device entries: **Front Counter Register**, **Patio Server Handheld**, **Grill KDS Screen**, **Expo KDS Screen**, **Kitchen Printer**, **Receipt Printer**, and **Guest Ordering Kiosk**.
- Show per-device online/offline state, *example* LAN IP (`192.168.10.x`), simulated discovery, device type and last-seen indicator. Filter online/offline. Choose **Set offline / Set online** to simulate a status change.
- **Simulate IP scan** sets simulated discovery results for online demo devices. It **does not** scan the network.
- **Test print** is provided on printer rows only; online printers emit a browser-local audit event and toast, while offline test-print buttons are disabled. **No real printing takes place.** Recent device events are shown in a log panel.

### Scope & persistence

- All objects are tenant/branch scoped by `brandId`, `locationId` and per-branch `stationRoutes`/`deviceFleet` keys. Existing browser data is migrated in place on load, retaining previous POS checks and earlier order tickets. Stored under `plateos-mock-db-v1` in browser `localStorage`; use private browsing or clear the site's storage to reset sample fixtures.
- Kiosk → POS → queue → KDS → floor and device updates are all handled by a single browser-local mock DB, with `BroadcastChannel`/`storage` event support for **tabs at the same browser origin** (not a real cloud sync service).
- Fictitious external-channel tickets seed on first load for multiple locations, including example website, AI Phone, DoorDash, Uber Eats, Grubhub, Zomato, Swiggy, Server Handheld and Table QR orders.

### Production wiring (NOT implemented)

**Marketplace integrations:** Secure provider OAuth/webhook credentials, connector adapters for each channel/region, signature verification, canonical order normalization, tenant-to-store mapping, event idempotency, menu mapping, acknowledgement/cancellation/fulfillment webhooks and reconciled refunds. Regulatory/provider certification may be required. The frontend simulator does not contact those providers.

**Real device discovery and printing:** Browsers cannot perform unrestricted LAN scans or raw ESC/POS printing. Deploy a permissioned on-premise device agent / print bridge to discover supported IP/USB/Bluetooth printers, enroll peripherals, stream authenticated heartbeats, and deliver test print commands to printer drivers. Keep diagnostics and device credentials per location.

**Multi-tenant SaaS:** Identity/RBAC, server-side tenant access control, PostgreSQL, WebSockets/SSE, durable event bus/outbox, mobile device enrollment, audit logging, payment-provider integrations, secure sync and real observability. This remains a **UI and interaction demo**, not a commercial, certified or real-time backend.

### Test suite

Run `python test_omni.py` if Chromium and Playwright are installed. It covers channel injection, station assignment and independent bumping, routing edit, floor-to-POS linking, simulated printer testing, discovery, tenant/location filtering and 390px mobile overflow. `python test_pos.py` covers critical existing POS check, offline and invoice workflows. Browser HTTP navigation can be restricted in some sandbox runners; `test_omni_cross_tab.py` is provided as an optional same-origin browser integration test when your environment allows local HTTP pages.

---

## PlateOS v5 — Analytics, reporting & Owner Mobile

Open **Reports & analytics** for time-filtered gross/net/tax sales, hourly trends, cash/card, channel/category/employee attribution, product mix, voids, discounts and shift cash variance. The **Custom builder** allows saved presets and genuine offline CSV/`.xlsx` downloads. Configure a bookkeeper's email and cadence (stored as a preference; the browser prototype does *not* send mail). **X / Z & batch** provides read-only X reports and simulated closeout/batch records. **Owner mobile** displays an interactive web-based phone viewport with today’s sample pulse across owner-accessible branches. An **Ask AI** bar answers supported financial questions via deterministic rules over the local demo ledger; no external LLM is connected.

For comprehensive instructions, calculations, scope, limitations, and acceptance tests, see [V5_RELEASE_NOTES.md](V5_RELEASE_NOTES.md).
