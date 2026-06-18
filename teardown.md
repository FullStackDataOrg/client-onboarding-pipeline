# Project Teardown — Decisions, Trade-offs & Roadmap

This document captures the engineering thought process behind the pipeline: why each component was built the way it was, what was deliberately left out, and where the project goes next.

---

## 1. Architectural Decisions

### Why medallion architecture (Raw → Bronze → Silver → Gold)?

The alternative is a single transformation layer that cleans and models in one pass. The problem with that approach is that any bug in the transformation logic corrupts the only copy of the data — there is no recovery without re-pulling from the source.

Medallion gives you three independent blast radii:
- **Raw** is immutable after load. If dbt breaks, raw is untouched.
- **Bronze** breaks? Re-run bronze only. Raw is fine.
- **Gold** breaks? Re-run gold only. Silver is your recovery point.

Each layer also has a clear single responsibility, which makes debugging fast and onboarding a second engineer straightforward.

---

### Why views for Bronze, not tables?

Bronze is rename-and-type — it adds no information. Making it a view means:
- Zero storage cost (Bronze "tables" would just duplicate Raw)
- Always fresh against Raw with no incremental logic needed
- If Raw schema changes, Bronze reflects it immediately — you only need to update the cast

The trade-off: every query that touches Bronze triggers a scan of the Raw table. For DuckDB at this scale (sub-million rows) that is sub-second. At Snowflake scale, you would materialise Bronze as tables and schedule a refresh — but the SQL is identical, only the `+materialized` config changes.

---

### Why UNION ALL in Silver rather than a JOIN?

Meta and Google Ads data has the same grain (one row per campaign per day) but different column names. A JOIN would imply a relationship between rows from two systems. A UNION ALL correctly models this as "two identical shapes of data being stacked" — the conformed dimension pattern.

The deliberate schema drift between `meta_ads_raw.csv` (using `date`, `campaign_id`, `spend_cents`) and `google_ads_raw.csv` (using `report_date`, `ad_group_id`, `cost_usd`) exists to demonstrate that Bronze's job is to absorb source system idiosyncrasies so that Silver never has to know about them.

---

### Why `CREATE OR REPLACE` for raw loads?

The simplest form of idempotency for full-refresh sources. Re-running the same ingestion job on the same data produces identical results — no duplicate rows, no partial states. The trade-off is that it is not efficient for large tables: it replaces the entire table even if only 1% of rows changed.

For sources with CDC (Change Data Capture), the right pattern is `MERGE` / `INSERT ... ON CONFLICT`. The customers source would benefit from this in production — but since ClientCo provides full snapshots (no CDC), `CREATE OR REPLACE` is correct here.

---

### Why an incremental model for `stg_customers`?

`stg_customers` uses `unique_key='customer_id'` and filters on `_loaded_at` for incremental runs. The `unique_key` makes re-runs idempotent: if the same customer appears in two consecutive loads, the second run updates the row rather than inserting a duplicate.

The alternative — a full-refresh table — would work, but it would rebuild 5,000 rows every run even if zero customers changed. Incremental is the right pattern as soon as the source table is large enough that a full rebuild is expensive.

---

### Why `dbt snapshot` with `check` strategy, not `timestamp`?

Two snapshot strategies exist:
- **timestamp** — compares a `updated_at` column between runs. Fast, but requires the source system to maintain a reliable updated timestamp. ClientCo's app DB does not.
- **check** — compares the values of specified columns (`plan_tier`, `email`). Works on any source, no `updated_at` column needed.

`check` is slightly more expensive (it hashes the values on every run) but is the only viable option when you do not control the source schema. In practice for a 5,000-row customer table the cost is negligible.

---

### Why do snapshots read from Raw directly, not from Bronze?

The snapshot needs to see every change the source system produces — including changes that Bronze might silently alter (e.g. if Bronze applied a default value to a null column). Snapshots sitting directly on Raw means the SCD2 history is a faithful record of what the source actually said, not what Bronze decided to show.

---

### Why surrogate keys in Gold?

`dim_campaign` uses `{{ dbt_utils.generate_surrogate_key(['platform', 'campaign_id']) }}`. This is necessary because Meta and Google Ads could independently assign the same numeric `campaign_id` to different campaigns. A surrogate key that combines platform + campaign_id guarantees uniqueness across the warehouse regardless of what source systems do.

It also decouples warehouse identity from business keys. If ClientCo migrates from Meta to TikTok and recycles campaign IDs, the surrogate key absorbs the collision — the downstream fact table foreign keys remain stable.

---

### Why `dagster-dbt` over running dbt as a subprocess?

A subprocess call (`subprocess.run(["dbt", "build"])`) would run the entire dbt project as a black box from Dagster's perspective. Dagster would show one asset ("dbt build ran") with no internal lineage.

`dagster-dbt` reads the dbt manifest and registers every model as a first-class Dagster asset. This means:
- Full lineage from raw Python assets through every dbt model to the gold layer in one graph
- Individual model re-runs from the UI (select `fct_daily_spend` only → Dagster translates to `dbt build --select fct_daily_spend`)
- dbt test results surface as asset checks in the Dagster UI
- Partial materialisations — Dagster knows which upstream assets are already fresh

---

## 2. Trade-offs & What Was Deliberately Left Out

| Decision | What was chosen | What was rejected | Why |
|---|---|---|---|
| Warehouse | DuckDB (file-based) | Snowflake | Zero cost, zero setup for development. Same SQL dialect — one `profiles.yml` block swaps to Snowflake |
| Bronze materialisation | Views | Tables | No storage cost; bronze adds no new information |
| Raw load strategy | `CREATE OR REPLACE` | `MERGE` / upsert | Sources are full-refresh — no CDC available |
| Snapshot strategy | `check` on `plan_tier`, `email` | `timestamp` | Source DB does not expose a reliable `updated_at` |
| Surrogate key | `dbt_utils.generate_surrogate_key` | Natural keys | Natural keys can collide across platforms |
| dbt integration | `dagster-dbt` with manifest | subprocess | Full per-model lineage and asset checks in Dagster |
| Container runtime | Single Docker Compose service | Kubernetes / separate services | Right-sized for a portfolio project; swap to K8s for multi-client prod |
| Data | Synthetic (deterministic seed) | Public Kaggle datasets | No public multi-platform paid-media dataset exists; synthetic gives full control over schema drift |

---

## 3. Features Implemented

| Feature | Layer | File |
|---|---|---|
| Idempotent raw loads | Ingestion | `assets/ingestion.py` |
| Multi-platform schema drift resolution | Bronze | `br_google__spend.sql` |
| Conformed spend grain (UNION ALL) | Silver | `stg_spend.sql` |
| Incremental deduplication | Silver | `stg_customers.sql` |
| SCD Type 2 customer history | Snapshots | `snap_customers.sql` |
| Star schema with surrogate keys | Gold | `dim_campaign.sql`, `fct_daily_spend.sql` |
| Date spine dimension | Gold | `dim_date.sql` |
| BI-ready denormalised mart | Gold | `agg_channel_performance.sql` |
| 36 data quality tests | All layers | `_sources.yml`, `_silver.yml`, `_gold.yml`, `tests/` |
| Full Dagster lineage (raw → gold) | Orchestration | `dbt_assets.py` |
| 06:00 UTC daily schedule | Orchestration | `schedules.py` |
| Source freshness SLAs | Bronze sources | `_sources.yml` |
| Source freshness sensor | Orchestration | `sensors.py` |
| dbt docs with lineage graph | Documentation | `dbt docs generate` |

---

## 4. Stretch Goals & Next Steps

### Stretch Goal 1 — Second client (multi-tenant)
**What:** Onboard `ClientCo B` using the same dbt models routed to separate schemas via `dbt vars`.

**How:** Pass `--vars '{"client": "clientco_b"}'` at runtime and use `{{ var('client') }}` in model configs to route to `clientco_b_bronze`, `clientco_b_silver`, etc. No SQL duplication — same models, different schema targets.

**Why it matters:** This is the core Scale-Army multi-tenant pattern. The interview question is "how do you onboard a second client without duplicating code?" — this is the answer.

---

### Stretch Goal 2 — Exposure declarations
**What:** Add `exposures.yml` declaring a Metabase dashboard as the downstream consumer of `agg_channel_performance`.

**How:**
```yaml
# dbt_project/models/exposures.yml
exposures:
  - name: channel_performance_dashboard
    type: dashboard
    maturity: high
    url: https://metabase.clientco.internal/dashboard/42
    depends_on:
      - ref('agg_channel_performance')
    owner:
      name: Analytics Team
```

**Why it matters:** Exposures appear in `dbt docs` as downstream nodes — the lineage graph extends all the way from `raw.meta_ads_spend` to the BI dashboard. This is how you prove data lineage end-to-end in a real audit.

---

### Stretch Goal 3 — Partitioned backfill
**What:** Convert `fct_daily_spend` to a Dagster partitioned asset by day. Backfill 90 days from the UI by selecting a date range.

**How:** Add `@asset(partitions_def=DailyPartitionsDefinition(start_date="2024-01-01"))` to the dbt asset and pass the partition date to dbt as a variable. Dagster handles parallel backfill execution.

**Why it matters:** Partitioned assets are the production pattern for large fact tables where you cannot afford a full rebuild. It also demonstrates Dagster's partial materialisation UI, which is a strong interview differentiator.

---

### Stretch Goal 4 — Real API ingestion
**What:** Replace `seed_data.py` with actual Meta Marketing API and Google Ads API calls.

**How:** The extract modules (`extract_meta.py`, `extract_google.py`) are already structured as importable functions — swap the CSV read for an API call. The Dagster asset and all downstream dbt SQL are unchanged.

**Why it matters:** Demonstrates that the pipeline abstraction is real — ingestion is decoupled from transformation. The Bronze layer's job (absorb schema quirks) stays relevant even with real API responses.

---

### Stretch Goal 5 — CI/CD with dbt test gating
**What:** GitHub Actions workflow that runs `dbt build --select state:modified+` on every pull request and blocks merge if any test fails.

**How:** Use dbt's state-aware selection with `--state ./prod-manifest` to run only models and their downstream dependents that changed. Gate the PR with a required status check.

**Why it matters:** Data contracts enforced at PR time — tests are not optional. This is what "data as code" means in practice.

---

## 5. Teardown Commands

```bash
# Stop services, keep all data
docker compose down

# Full reset — remove container, image, and all generated files
docker compose down --rmi local
rm -f data/warehouse.duckdb data/meta_ads_raw.csv data/google_ads_raw.csv data/customers_raw.csv
rm -rf dbt_project/target/ dbt_project/dbt_packages/ dbt_project/logs/ dagster_home/
```

Restart from clean state:
```bash
docker compose up --build -d
docker compose exec onboarding python ingestion/seed_data.py
docker compose exec onboarding bash -c "cd /workspace/dbt_project && dbt deps && dbt parse"
# Materialise all → http://localhost:3000
```
