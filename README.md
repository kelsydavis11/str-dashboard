# STR Dashboard (Phase 1)

Read-only Streamlit reporting over the STR Google Sheet. It **does not modify**
the sheet or the Apps Script. It reuses the existing Booking.com-sync OAuth
credentials (`../token.json`) — no separate auth system.

## Run

```bash
cd dashboard
.venv/bin/python -m streamlit run app.py
```

Then open http://localhost:8501. First run needs the venv:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

## What it reads

- **Primary fact table:** `Confirmed Bookings` (reservations across Airbnb +
  Booking.com). No other tab is read in Phase 1.
- **Auth:** `google.oauth2.credentials.Credentials.from_authorized_user_file`
  on `../token.json`, scope `spreadsheets` (must match the scope the token was
  granted; a narrower scope fails to refresh). Read calls only.
- **Sheet ID:** read from `../.env` (`GOOGLE_SHEET_ID`).

## Pages

Overview · Revenue & pace · Operations · Property comparison · Cancellations.
Global sidebar filters: property, platform, booking status, check-in range,
booked-on range.

## Metric rules

- **Cancelled and invalid-date rows are excluded** from all revenue/occupancy
  metrics; they appear only on the Cancellations tab.
- **Net payout** (`revenue_net`, manual override honoured when present) is the
  preferred revenue measure; **Guest total** is kept as a separate gross figure.
- **Occupied nights** use check-in → check-out (checkout night not counted),
  allocated night-by-night so cross-month stays split correctly.

## Assumptions (Phase 1)

1. **Occupancy / RevPAR assume N always-available units** (N = number of
   properties in the current filter) across the selected check-in window.
   Owner-blocked / maintenance nights are **not** modelled. The `Calendar` tab
   could refine true availability later.
2. **Booking pace** attributes each booking's net payout to its **check-in
   month**; **monthly occupancy** spreads nights across calendar months.
3. **ADR** shown two ways: net payout / night and guest total / night.

## Known data-quality issues (documented, not fixed upstream)

These live in the source data. Per instruction, they are handled defensively
here and reported in-app (see the "Data quality & assumptions" expander), not
patched in the Apps Script.

1. **`Net payout` is stored as text** (`"$1,430"`) — parsed to a number here.
   `Guest total` is numeric. Inconsistent typing in the sheet.
2. **Booking.com rows carry no fee breakdown and no guest headcount** — only
   Net payout and Guest total are populated for them, so those two are the only
   cross-platform-comparable money fields. (~22 rows affected.)
3. **Dates are dd/mm/yyyy** — parsed with `dayfirst=True`.
4. **Cancellations** are identified by `Status = "Cancelled"` (and/or
   `Cancelled on` populated) — clean in the current data (12/53).
5. **Small dataset** (~53 rows) — metrics are inherently noisy.

If any of these should instead be fixed at the source (e.g. store Net payout as
a number, populate Booking.com guest counts), that's an upstream Apps Script /
scraper change — flagged here for a decision rather than made unilaterally.
