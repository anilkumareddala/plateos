# PlateOS v5 — Analytics, Reporting & Owner Mobile Companion

## Launch

Open `index.html` directly in Chrome, Edge, or Safari. No dependencies or server setup are required for this browser demonstration. All previously built Kiosk, POS, KDS, Omnichannel, Menu, People, Floor, Devices and security views are retained.

To view financial reports, choose a restaurant and branch, keep the demo role on **Owner** or **Manager**, then select **Reports & analytics**. Use the five tabs: Sales summary, PMIX & trends, Taxes & exceptions, X / Z & batch, and Custom builder. The **Owner mobile** navigation item shows the embedded phone-width experience.

## Financial reporting

- Date filter: today, 7 days, 30 days, or custom inclusive start and end dates. Current business day is computed using the selected branch's `America/Chicago` timezone.
- Scope: selected branch; only the Owner demo role can aggregate all branches of the active restaurant. Switching to another brand starts a new scope.
- Metrics: gross sales, discounts, net sales, transaction count, average check, tax, tips, tender split between cash and card, and hourly net sales.
- Grouped sales: Category, Item, Hour, Server, Payment Type, Order Type, Channel, Location (owners), and Date.
- PMIX: item quantities, mix %, gross, discounts, net sales.
- Exceptions: demo void activity, recorded manager override voids, taxes, discounts, and per-shift counted-versus-expected cash variance.
- Each report table can be exported to Excel `.xlsx` or CSV. These are **real client-generated downloads**, not mislabeled text files. `.xlsx` uses minimal Office Open XML inside a ZIP archive and is fully offline-capable.

## Live data semantics and sample fixtures

The prototype has no payment gateway or backend. Consequently, v5 seeds dated, explicitly labeled **illustrative settled-sale fixtures** for both restaurant brands and their branches. All charts, groupings, exports, and the rule-based analyst calculate actual results *from that browser demo ledger*; displayed values are not hardcoded in the chart UI.

POS payments recorded in v2-v4 are also included when the browser records mark them paid and synchronized. Pending-sync and refunded payments are excluded from positive sales. Merely placing an unpaid Kiosk/QR/aggregator order does **not** create booked sales. This distinction prevents order queue volume from being misrepresented as settled revenue. Invoice drafts are not included as collected sales.

For item-based split POS payments, item attribution follows the paid check part. Amount-based splits are not reliably item attributable and are treated as unallocated so that product mix is not falsely duplicated.

For production, replace this fixture ledger with a server-side, immutable transaction/settlement ledger that handles taxation, refunds, payments, chargebacks, discounts, and processor reconciliation correctly. The example uses a constant 8.25% tax for UI demonstration; it is **not** a jurisdiction-aware tax engine or accounting system.

## End-of-day operations

- **X-Report:** generates a nonmutating shift financial readout.
- **Z-Report:** requires an owner/manager, shift and business date, opening float, counted cash, and a confirmation. Records a branch-specific simulated end-of-shift snapshot and blocks duplicate Z records for the same branch/date/shift.
- **Cash variance:** counted cash minus expected cash (opening float + cash tenders + recorded cash tips +/- paid-in/out/drops).
- **Credit card batch:** creates a **simulated batch** record; the application does not contact or settle with any card processor.
- A Z snapshot does *not* legally close a fiscal day, lock transactions, or create a processor deposit. Production closeout needs transactional locking, reconciliation, and a certified provider integration as needed.

## Custom reports and bookkeeper schedules

Save or load a report grouping/date/scope preset. Export the current computed table as CSV or `.xlsx`. A saved template can store a validated bookkeeper email address and daily, weekly or monthly cadence. **Email is never sent by this browser app.** The UI accurately labels the schedule as `configuration-only`. Production implementation needs an authenticated scheduler, verified sender, bookkeeper consent, delivery telemetry, and access-controlled attachment generation.

## “Ask AI” analyst

The question bar on Reports and Overview is a deterministic, local rules-based natural language demo that calculates answers against the same financial fixture and security event store. Supported questions include lunch sales vs last Tuesday, highest voids, highest earning branch, cash vs card, top sellers, tax and general sales totals. The answer panel includes mini comparison charts where supported. For other questions, it gives a transparent list of supported topics rather than inventing an answer. **No LLM, retrieval API or external AI is connected in v5.**

## Owner mobile

The Owner App is a sleek responsive mobile-viewport *preview inside the web app*, showing today's net sales, ticket count, average ticket, cash/card, and branch breakdown. It is not a native App Store or Play Store build, and it has no push notifications or real back-office API. The `Owner` demo role sees all locations of the active brand; `Manager` sees the selected branch only. `Cashier` and `Server` cannot navigate to reports or the owner mobile view.

## Browser tests and screenshots

- `test_analytics.py`: reports, Ask AI data answers, group changes, templates, schedule preference, real `.xlsx` export, X/Z and batch simulation, owner mobile, restaurant switching.
- `test_analytics_deep.py`: 390px mobile layout, owner/manager/cashier access, all-branch vs single-branch separation, tenant isolation, CSV export.
- Previous suite: `test_ops.py`, `test_omni.py`, `test_pos.py`, `test_pos_advanced.py`, `test_sync.py` passed after v5 integration. Run via `python <filename>` (requires Playwright and a local Chromium for automated tests only).
- Screenshots named `preview-v5-*` are actual browser captures of the new interface, not generated concept art.

## Security and production limitations

All persistence currently uses local browser storage. Sample PINs, role switching, end-of-day snapshots, and local security events are **not** secure against browser manipulation. A sellable multi-tenant SaaS requires server-enforced tenant and location membership, protected accounting/processor credentials, immutable append-only financial/audit events, well-defined restaurant business days and timezone transitions, an authorization/authentication service, background job orchestration, a real card processor, and a tenant-aware real-time event system.
