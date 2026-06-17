# Client Onboarding Pipeline

Production-shaped ELT pipeline that turns a freshly-signed enterprise client's raw media spend data into a fully modelled, analytics-ready warehouse.

**Stack:** DuckDB · dbt · Dagster · Docker · Python 3.11  
**Architecture:** Medallion (Raw → Bronze → Silver → Gold)  
**Diagram:** [architecture.mmd](architecture.mmd) · **Tools:** [stack.json](stack.json)

---

## What this builds

ClientCo runs paid advertising on Meta and Google. Their raw data lands in three source systems with completely different schemas. This pipeline:

1. **Ingests** raw CSVs into DuckDB via Dagster Python assets (idempotent, `CREATE OR REPLACE`)
2. **Conforms** heterogeneous schemas in a Bronze view layer (rename, type-cast, no storage cost)
3. **Unifies** both ad platforms into a single spend grain in Silver (`UNION ALL`)
4. **Snapshots** the customer dimension with SCD Type 2 (`dbt snapshot`, `check` strategy)
5. **Models** a star schema in Gold (fact table + dimensions + BI mart)
6. **Tests** every layer with dbt data contracts (36 tests across `unique`, `not_null`, `relationships`, `accepted_values`, singular)
7. **Orchestrates** everything on a 06:00 UTC schedule with a source freshness sensor in Dagster

---

## Quick start

> Requires Docker Desktop with WSL 2 integration enabled.

```bash
# 1. Build image and start container
docker compose up --build -d

# 2. Generate synthetic raw data (90 days × 80 campaigns, 5,000 customers)
docker compose exec onboarding python ingestion/seed_data.py

# 3. Install dbt packages and emit the manifest Dagster reads
docker compose exec onboarding bash -c "cd /workspace/dbt_project && dbt deps && dbt parse"

# 4. Open Dagster UI → http://localhost:3000
#    Click "Materialize all" — runs raw ingestion → dbt build in one pass
```

---

## Runbook

| Command | What it does |
|---|---|
| `python ingestion/seed_data.py` | Generate/refresh CSVs. Run **twice** to shift ~50 customer plan tiers for SCD2 demo |
| `dbt deps` | Install dbt-utils package into `dbt_packages/` |
| `dbt parse` | Compile models → emit `target/manifest.json` (required by dagster-dbt) |
| `dbt build` | Run all models + tests in dependency order |
| `dbt snapshot` | Capture SCD2 changes in `snap_customers` |
| `dbt test` | Run all 36 generic and singular tests |
| `dbt source freshness` | Check `_loaded_at` SLAs declared in `_sources.yml` |
| `dbt docs generate` | Write `target/catalog.json` from live warehouse |

**dbt docs (local):**
```bash
docker compose exec onboarding bash -c "cd /workspace/dbt_project && dbt docs generate"
cd dbt_project/target && python3 -m http.server 8081
# → http://localhost:8081
```

---

## Warehouse layout

| Schema | Type | Rows | Purpose |
|---|---|---|---|
| `raw.meta_ads_spend` | DuckDB table | 4,500 | Source-native Meta schema |
| `raw.google_ads_spend` | DuckDB table | 2,700 | Source-native Google schema |
| `raw.customers` | DuckDB table | 5,000 | Full daily snapshot |
| `bronze.br_meta__spend` | dbt view | — | Renamed + typed |
| `bronze.br_google__spend` | dbt view | — | Schema drift resolved |
| `bronze.br_app__customers` | dbt view | — | Typed, `_loaded_at` cast |
| `silver.stg_spend` | dbt table | 7,200 | UNION ALL across platforms |
| `silver.stg_customers` | dbt incremental | 5,000 | `unique_key=customer_id` |
| `snapshots.snap_customers` | dbt snapshot | 5,000+ | SCD Type 2, `check` strategy |
| `gold.dim_campaign` | dbt table | 80 | Surrogate key per platform+campaign |
| `gold.dim_date` | dbt table | 1,096 | Calendar 2024–2026 |
| `gold.fct_daily_spend` | dbt table | 7,200 | Fact grain: campaign × day |
| `gold.agg_channel_performance` | dbt table | 180 | Daily BI mart by channel |

---

## Project structure

```
client-onboarding-pipeline/
├── Dockerfile / docker-compose.yml
├── requirements.txt / setup.sh          # local venv bootstrap
├── ingestion/
│   ├── seed_data.py                     # deterministic data generator (rng seed=42)
│   └── extract_meta.py / extract_google.py / extract_customers.py
├── dbt_project/
│   ├── models/
│   │   ├── bronze/   _sources.yml (freshness SLAs) + 3 views
│   │   ├── silver/   stg_spend (table) + stg_customers (incremental)
│   │   └── gold/     dim_date, dim_campaign, fct_daily_spend, agg_channel_performance
│   ├── snapshots/    snap_customers.sql
│   ├── tests/        assert_spend_is_non_negative.sql
│   ├── macros/       generate_surrogate_key.sql
│   └── seeds/        channel_mapping.csv
└── dagster_project/pipeline/
    ├── assets/       ingestion.py + dbt_assets.py
    ├── resources.py / schedules.py / sensors.py
    └── definitions.py
```

---

## Verification checklist

- [ ] Dagster asset graph shows full lineage: `raw_*` → bronze → silver → gold
- [ ] All 5 DuckDB schemas present: `raw`, `bronze`, `silver`, `gold`, `snapshots`
- [ ] `dbt test` — 36 tests pass, 0 failures
- [ ] `fct_daily_spend` has exactly 7,200 rows (90 × 80), no duplicates
- [ ] Re-running ingestion + `dbt build` produces identical results (idempotency)
- [ ] Second `seed_data.py` run + `dbt snapshot` creates new SCD2 rows with `dbt_valid_to` set
- [ ] `dbt source freshness` — all 3 sources PASS immediately after a pipeline run

---

## Key concepts demonstrated

| Concept | Where |
|---|---|
| Idempotent raw loads | `ingestion.py` — `CREATE OR REPLACE TABLE` |
| Schema drift handling | `br_google__spend.sql` — rename at bronze |
| Medallion architecture | Bronze views → Silver tables → Gold star schema |
| UNION ALL conforming | `stg_spend.sql` |
| Incremental models | `stg_customers.sql` — `unique_key` + `is_incremental()` |
| SCD Type 2 | `snap_customers.sql` — `check_cols` strategy |
| Surrogate keys | `dim_campaign.sql` — `dbt_utils.generate_surrogate_key` |
| Data contracts | `_gold.yml` — `relationships`, `expression_is_true`, singular tests |
| dagster-dbt integration | `dbt_assets.py` — manifest → asset graph |
| Source freshness SLAs | `_sources.yml` + `sensors.py` |
