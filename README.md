# Australian Real Estate Intelligence (MVP)

This repository contains an end-to-end MVP scaffold for an Australian property intelligence platform.

## Implemented components

- Backend API (FastAPI)
  - `GET /health`
  - `GET /properties`
  - `POST /valuation` (CMA + deep analysis)
  - `GET /rankings/suburbs`
- Database layer (SQLAlchemy + PostgreSQL)
- Analytics services
  - investor score
  - deep analysis: conviction, edge, moat, fragility, data-depth
  - scenario stress testing and alpha signals
- Data ingestion scaffold
  - ABS snapshot loader
  - manual CSV property importer
- Frontend app (React + Vite)
   - landing page at `/` with waitlist flow
   - analysis app at `/app`
   - select property, run deep analysis, view rankings and scenario/risk outputs

## Start to finish setup (Windows PowerShell)

1. Copy backend environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Choose database mode:

   Local zero-setup mode (default): keep SQLite in `.env`.

   OR PostgreSQL mode with Docker:

   ```powershell
   docker compose up -d
   ```

3. Install backend dependencies:

   ```powershell
   pip install -r requirements.txt
   ```

4. Seed demo data:

   ```powershell
   python -m backend.scripts.seed_demo_data
   ```

5. Run backend API:

   ```powershell
   uvicorn backend.app.main:app --reload
   ```

   Windows-safe alternative (auto-picks free port):

   ```powershell
   powershell -ExecutionPolicy Bypass -File backend/scripts/start_backend.ps1
   ```

6. Open a second terminal and prepare frontend env:

   ```powershell
   Copy-Item frontend/.env.example frontend/.env
   ```

7. Install frontend dependencies:

   ```powershell
   Set-Location frontend
   npm install
   ```

8. Run frontend:

   ```powershell
   npm run dev
   ```

9. Open apps:

- API docs: http://127.0.0.1:8000/docs
- Landing page: http://127.0.0.1:5173
- Analysis app: http://127.0.0.1:5173/app

## Important notes

- This is an MVP foundation and uses seed/demo data unless you connect licensed feeds.
- Keep legal/data-source compliance controls in place before production rollout.

## Troubleshooting

- If backend fails with `[WinError 10013]`, another process is using or blocking the port.
- Use the auto-port script:

   ```powershell
   powershell -ExecutionPolicy Bypass -File backend/scripts/start_backend.ps1
   ```

- Or start on a different explicit port:

   ```powershell
   uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8010
   ```

## Free-Tier Supabase + Vercel Implementation

This repo now includes a free-tier deployment foundation:

- Supabase migration SQL: `supabase/migrations/001_free_tier_core.sql`
- Scheduled ingestion workflow: `.github/workflows/open-data-ingestion.yml`
- Supabase ingestion runner: `backend/scripts/ingest_open_data_supabase.py`

### 1. Apply Supabase schema

Run the SQL from `supabase/migrations/001_free_tier_core.sql` in your Supabase SQL editor.

### 2. Configure GitHub secrets

Set these repository secrets:

- `SUPABASE_DATABASE_URL` (Supabase pooled Postgres connection string)
- `ABS_API_URL` (optional ABS JSON endpoint; leave blank for fallback sample row)
- `OPEN_METRICS_CSV_URL` (optional CSV endpoint for suburb metrics; leave blank for fallback sample row)

### 3. Run ingestion manually (local)

From repository root:

```powershell
python -m backend.scripts.ingest_open_data_supabase --pipeline all --as-of-date 2026-03-27
```

### Phase 1 quickstart (recommended)

Use this one command to run open-data ingestion and print row counts used by the app:

```powershell
python -m backend.scripts.phase1_bootstrap --pipeline all --as-of-date 2026-03-27
```

Expected output includes counts for:

- `abs_indicators`
- `suburb_metrics`
- `pipeline_runs`

Pipelines:

- `abs` -> ABS indicators only
- `metrics` -> suburb metrics only
- `all` -> both

### 4. Run ingestion via GitHub Actions

Use workflow dispatch for manual runs, or rely on the included daily/weekly schedules.

### Notes

- Ingestion writes telemetry to `public.pipeline_runs`.
- Upserts are idempotent using unique keys:
   - `abs_indicators`: `(postcode, census_year)`
   - `suburb_metrics`: `(postcode, as_of_date, source)`

## Deploy Now: Supabase + Vercel

1. Create a Supabase project and copy the pooled Postgres URL.
2. Set backend environment values (where backend is hosted):
   - `DATABASE_URL` -> Supabase transaction pooler URL
     - Example: `postgresql+psycopg2://postgres.lqadaikjlcslzelmutmw:[YOUR-PASSWORD]@aws-1-ap-southeast-2.pooler.supabase.com:6543/postgres`
   - `ALLOWED_ORIGINS` -> your production frontend URL
   - `ALLOWED_ORIGIN_REGEX` -> `https://.*\\.vercel\\.app` (optional for preview deployments)
3. Deploy frontend to Vercel from the `frontend` directory.
   - `frontend/vercel.json` is included for SPA rewrites.
   - Set Vercel env var `VITE_API_BASE` to your backend public URL.
4. If you run ingestion through GitHub Actions, set `SUPABASE_DATABASE_URL` in repository secrets.
