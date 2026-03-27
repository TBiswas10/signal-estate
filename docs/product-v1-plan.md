# Product V1 Plan (Execution Now)

## Goal
Turn the current analytics MVP into a decision product users can act on daily.

## Phase 1 (Implemented in this pass)

- Decision workflow scaffold in app UI:
  - Discover -> Shortlist -> Compare -> Decide -> Monitor
- Onboarding state in app:
  - first-session checklist with dismiss persistence
- Shortlist mechanics:
  - local watchlist toggle and persistence (localStorage)
- Comparison mechanics:
  - secondary property selection and side-by-side comparison panel
- Trust surface:
  - confidence tier, backend heartbeat, and data freshness status card
- Health API improvement:
  - return freshness metadata from latest pipeline runs

## Phase 2 (Next)

- Auth-backed watchlist and saved reports in frontend using existing `/user/*` APIs
- Explainable comparable sales panel with adjustment rationale
- Saved decision memo templates and export (PDF/markdown)
- Strategy presets (growth, cashflow, balanced)

## Phase 3 (Launch Quality)

- Alerts (email/in-app) on valuation/risk/freshness changes
- Portfolio mode with thesis tracking and drift alerts
- Personalization loop from user feedback on recommendations
- Pricing/packaging boundaries (Free vs Pro)

## Acceptance for Phase 1

- User can complete a guided workflow from property discovery to compare and shortlist.
- User can see whether insights are trustworthy via confidence and freshness indicators.
- UI is responsive on mobile and desktop.
