# Openings Tracker (replaces Compare tab) — Design

**Date:** 2026-08-27
**Status:** Approved, pending implementation plan

## Context

`static/texas_alcohol_explorer.html` currently has three tabs: Explorer, Nearby, Compare. Compare lets a
user pick up to 5 venues and see a side-by-side monthly receipts table.

We're replacing Compare with a **new/closed venue tracker** ("Openings" tab). Rationale (from prior
conversation): the app's likely paying audience — CRE brokers, investors, distributor sales reps, multi-unit
operators — cares more about *which venues are opening or closing* than about manually comparing named
venues against each other. It's also a feature the closest known competitor (BoozeReports) doesn't
explicitly offer, so it's a differentiation angle.

## Goal

Show, for a selected Month/Year (and optional City/ZIP), which Mixed Beverage (MB) permits were newly
issued and which were recently cancelled/surrendered — surfacing likely openings *before* a venue starts
reporting sales, and likely closures shortly after they happen.

## Data source

Switches from the receipts dataset (`naix-2893`, used elsewhere in the app) to a different Texas Open Data
Portal dataset for this tab: **TABC License Information** —
`https://data.texas.gov/resource/7hf9-qc9f.json`.

Relevant fields (confirmed via live query against the resource):

| Field | Meaning |
|---|---|
| `license_type` | 2-char code; filter to `MB` (Mixed Beverage) to match the rest of the app's scope |
| `original_issue_date` | Date this specific license was **first ever** issued for this location — does not change on renewal. This is the "new venue" signal. |
| `current_issued_date` | Most recent (re)issuance date — changes on renewal. **Not used** for "new," to avoid re-flagging routine renewals as new openings. |
| `primary_status` | `Active`, `Expired`, `Cancelled`, `Surrendered`, `Suspended`, etc. |
| `status_change_date` | Date of last status change — used with `primary_status` for the "closed" signal |
| `trade_name`, `owner` | Venue name / legal owner |
| `address`, `city`, `zip`, `county` | Location (zip is 9-digit, e.g. `"770816967"` — needs first-5 matching against the app's existing zip filter, which expects 5-digit input) |

No cross-referencing with `naix-2893` or `tx_venues_geo.json` is required for this feature — it's a
self-contained query against the license dataset. (Tapping a row still opens the existing sales-history
modal, which *does* hit `naix-2893` — see Interactions below.)

## Queries

**New Permits section:**
```
license_type='MB' AND original_issue_date >= '<month-start>' AND original_issue_date < '<next-month-start>'
[AND city='<city>'] [AND starts_with(zip, '<5-digit-zip>')]
```

**Recently Closed section:**
```
license_type='MB' AND primary_status IN ('Cancelled','Surrendered')
AND status_change_date >= '<month-start>' AND status_change_date < '<next-month-start>'
[AND city='<city>'] [AND starts_with(zip, '<5-digit-zip>')]
```

Both use the same Month/Year and City/ZIP filter controls already present on Explorer (reuse the existing
filter-bar markup/pattern, not new components).

## Layout

Tab bar: `Compare` → **`Openings`**. Reuse the existing Compare tab's SVG icon as-is (no new artwork) — only
the label and page content change.

Page has one shared filter bar (Month, Year, City, ZIP — no Taxpayer/Business Name field, since this isn't
a receipts search) above two stacked sections, each an independent table styled like Explorer's venue
table:

- **New Permits** — columns: Location (trade_name), City, Address, Issue Date, Owner
- **Recently Closed** — columns: Location, City, Address, Status, Status Change Date, Owner

Each section has its own empty state (e.g., "No new MB permits issued in June 2026" /
"No closures in June 2026 for Dallas") — zero results for a given city/month is expected and not an error.

## Interactions

- **Row tap** → reuse the existing sales-history modal (same one Explorer/Nearby use), which queries
  `naix-2893` by `location_name`/`taxpayer_name`/address for that venue's receipts history.
  - For a brand-new permit, this will commonly show no filings yet — that's expected and itself
    informative ("permitted, not yet reporting = not open yet").
  - For a closed venue, this shows their trailing sales history — useful for judging whether they were
    doing well before closing.
- **Export CSV** — one button per section, same pattern as the existing Explorer/Compare export buttons.

## Removal scope

Delete (not hide) from `static/texas_alcohol_explorer.html`:
- Compare page markup (`#compare-page` block)
- Compare tab button in the nav bar
- Compare-specific JS: `cmpLiveSearch`, `cmpClearSearch`, `runComparison`, `clearComparison`,
  `exportCompareCSV`, and any other `cmp*`-prefixed functions/state
- Compare-specific CSS (`.cmp-*`, "Compare tab" / "Compare search results list" comment blocks)

Confirm nothing else in the file references `cmp*` identifiers before deleting (the history modal is shared
and must NOT be removed — only the Compare-page-specific wiring around it).

## Implementation workflow

- New git branch off `main` in the `personal-dashboard` repo (not a separate project — this is a single
  self-contained HTML file; a separate project would mean duplicating shared CSS/JS and reconciling two
  copies later, which is more risk, not less).
- Build the new tab, verify live in the browser preview (same approach used earlier this session to test
  Explorer/Nearby/Compare — check console errors, confirm real query results render, confirm modal still
  opens correctly from the new tables).
- Only merge to `main` once verified working end-to-end.

## Open risks / things to confirm during implementation

- Dataset freshness: last known update was 2026-07-14 — confirm it's still updating on a reasonable
  cadence before relying on it for a "current month" view; if it lags, the Month/Year picker's most recent
  option(s) may come back empty even when real openings/closures exist.
- `zip` in this dataset is 9-digit unformatted (`ZIP+4` concatenated, e.g. `"770816967"`) — needs
  first-5-digit prefix matching against the existing ZIP filter input, not exact match.
- Large `owner` name strings (e.g., corporate franchise owners) may need the same truncation treatment used
  elsewhere in the app's tables.

## Out of scope (this change)

- Map/visual view of openings/closures (a separately-discussed future upgrade, not bundled here)
- Cross-referencing new permits against `tx_venues_geo.json` for geocoding
- Any non-MB license types
