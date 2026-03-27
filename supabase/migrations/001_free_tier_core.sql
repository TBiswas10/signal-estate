-- Free-tier core schema for Vercel + Supabase deployment.
-- Run in Supabase SQL editor or via supabase migration tooling.

create extension if not exists pgcrypto;

create table if not exists public.suburb_metrics (
  id uuid primary key default gen_random_uuid(),
  suburb text not null,
  state text not null,
  postcode text not null,
  median_price numeric,
  annual_growth_pct numeric,
  rental_yield_pct numeric,
  days_on_market_avg integer,
  source text not null default 'open_data',
  as_of_date date not null,
  created_at timestamptz not null default now(),
  unique (postcode, as_of_date, source)
);

create table if not exists public.abs_indicators (
  id uuid primary key default gen_random_uuid(),
  postcode text not null,
  census_year integer not null,
  median_household_income numeric,
  unemployment_rate_pct numeric,
  population integer,
  notes text,
  source text not null default 'abs',
  created_at timestamptz not null default now(),
  unique (postcode, census_year)
);

create table if not exists public.properties (
  id uuid primary key default gen_random_uuid(),
  external_id text,
  address text not null,
  suburb text not null,
  state text not null,
  postcode text not null,
  property_type text not null,
  bedrooms integer not null default 0,
  bathrooms integer not null default 0,
  carspaces integer not null default 0,
  land_size_sqm numeric,
  listing_price numeric,
  listing_url text,
  source text not null default 'manual_csv',
  as_of_date date not null,
  created_at timestamptz not null default now(),
  unique (address, postcode, as_of_date, source)
);

create table if not exists public.pipeline_runs (
  id uuid primary key default gen_random_uuid(),
  pipeline_name text not null,
  source_name text not null,
  status text not null,
  records_processed integer not null default 0,
  records_failed integer not null default 0,
  freshness_minutes integer,
  error_message text,
  started_at timestamptz not null default now(),
  completed_at timestamptz
);

create table if not exists public.saved_reports (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  property_id uuid references public.properties(id) on delete set null,
  score numeric,
  payload_json jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

-- Legacy schema repair: if tables already exist from an earlier revision,
-- ensure required columns and constraints exist before creating indexes/policies.

alter table if exists public.suburb_metrics add column if not exists source text;
alter table if exists public.suburb_metrics add column if not exists as_of_date date;

update public.suburb_metrics set source = 'open_data' where source is null;
update public.suburb_metrics set as_of_date = current_date where as_of_date is null;

alter table if exists public.suburb_metrics alter column source set default 'open_data';
alter table if exists public.suburb_metrics alter column source set not null;
alter table if exists public.suburb_metrics alter column as_of_date set not null;

alter table if exists public.abs_indicators add column if not exists source text;
update public.abs_indicators set source = 'abs' where source is null;
alter table if exists public.abs_indicators alter column source set default 'abs';
alter table if exists public.abs_indicators alter column source set not null;

alter table if exists public.properties add column if not exists source text;
alter table if exists public.properties add column if not exists as_of_date date;
update public.properties set source = 'manual_csv' where source is null;
update public.properties set as_of_date = current_date where as_of_date is null;
alter table if exists public.properties alter column source set default 'manual_csv';
alter table if exists public.properties alter column source set not null;
alter table if exists public.properties alter column as_of_date set not null;

alter table if exists public.pipeline_runs add column if not exists records_processed integer;
alter table if exists public.pipeline_runs add column if not exists records_failed integer;
alter table if exists public.pipeline_runs add column if not exists freshness_minutes integer;
alter table if exists public.pipeline_runs add column if not exists error_message text;

update public.pipeline_runs set records_processed = 0 where records_processed is null;
update public.pipeline_runs set records_failed = 0 where records_failed is null;

alter table if exists public.pipeline_runs alter column records_processed set default 0;
alter table if exists public.pipeline_runs alter column records_failed set default 0;
alter table if exists public.pipeline_runs alter column records_processed set not null;
alter table if exists public.pipeline_runs alter column records_failed set not null;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'uq_suburb_metrics_postcode_as_of_source'
      and conrelid = 'public.suburb_metrics'::regclass
  ) then
    alter table public.suburb_metrics
      add constraint uq_suburb_metrics_postcode_as_of_source unique (postcode, as_of_date, source);
  end if;
end $$;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'uq_abs_indicators_postcode_census_year'
      and conrelid = 'public.abs_indicators'::regclass
  ) then
    alter table public.abs_indicators
      add constraint uq_abs_indicators_postcode_census_year unique (postcode, census_year);
  end if;
end $$;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'uq_properties_address_postcode_as_of_source'
      and conrelid = 'public.properties'::regclass
  ) then
    alter table public.properties
      add constraint uq_properties_address_postcode_as_of_source unique (address, postcode, as_of_date, source);
  end if;
end $$;

create index if not exists idx_suburb_metrics_postcode_date on public.suburb_metrics (postcode, as_of_date desc);
create index if not exists idx_suburb_metrics_suburb_state_date on public.suburb_metrics (suburb, state, as_of_date desc);
create index if not exists idx_abs_indicators_postcode_year on public.abs_indicators (postcode, census_year desc);
create index if not exists idx_properties_postcode_date on public.properties (postcode, as_of_date desc);
create index if not exists idx_pipeline_runs_pipeline_started on public.pipeline_runs (pipeline_name, started_at desc);

alter table public.suburb_metrics enable row level security;
alter table public.abs_indicators enable row level security;
alter table public.properties enable row level security;
alter table public.saved_reports enable row level security;

-- Public read for open analytics data.
drop policy if exists p_suburb_metrics_public_read on public.suburb_metrics;
create policy p_suburb_metrics_public_read
  on public.suburb_metrics
  for select
  using (true);

drop policy if exists p_abs_indicators_public_read on public.abs_indicators;
create policy p_abs_indicators_public_read
  on public.abs_indicators
  for select
  using (true);

-- Optional authenticated read of imported properties.
drop policy if exists p_properties_auth_read on public.properties;
create policy p_properties_auth_read
  on public.properties
  for select
  to authenticated
  using (true);

-- Users can read and write only their own saved reports.
drop policy if exists p_saved_reports_own_select on public.saved_reports;
create policy p_saved_reports_own_select
  on public.saved_reports
  for select
  to authenticated
  using (auth.uid()::text = user_id::text);

drop policy if exists p_saved_reports_own_insert on public.saved_reports;
create policy p_saved_reports_own_insert
  on public.saved_reports
  for insert
  to authenticated
  with check (auth.uid()::text = user_id::text);

drop policy if exists p_saved_reports_own_delete on public.saved_reports;
create policy p_saved_reports_own_delete
  on public.saved_reports
  for delete
  to authenticated
  using (auth.uid()::text = user_id::text);
