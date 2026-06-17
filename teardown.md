# Teardown Guide

Three levels depending on how much you want to reset.

---

## Level 1 — Stop services (keep everything, resume later)

```bash
docker compose down
```

Stops and removes the container. The DuckDB warehouse, raw CSVs, and dbt artifacts are preserved in `./data/` and `./dbt_project/target/` (volume-mounted). Resume with:

```bash
docker compose up -d
```

---

## Level 2 — Full container teardown (keep data)

Remove container, network, and the built image:

```bash
docker compose down --rmi local
```

Data in `./data/` and generated artifacts remain untouched. Next `docker compose up --build -d` rebuilds the image from scratch but skips seed data generation.

---

## Level 3 — Complete reset (remove all generated files)

Wipe the warehouse, raw CSVs, dbt artifacts, and the container:

```bash
# Stop and remove container + image
docker compose down --rmi local

# Remove generated data files
rm -f data/warehouse.duckdb data/meta_ads_raw.csv data/google_ads_raw.csv data/customers_raw.csv

# Remove dbt build artifacts
rm -rf dbt_project/target/ dbt_project/dbt_packages/ dbt_project/logs/

# Remove local dagster home (if running locally)
rm -rf dagster_home/
```

After this, the repo is back to a clean state. Start from scratch with:

```bash
docker compose up --build -d
docker compose exec onboarding python ingestion/seed_data.py
docker compose exec onboarding bash -c "cd /workspace/dbt_project && dbt deps && dbt parse"
# Then materialise all in the Dagster UI → http://localhost:3000
```

---

## Useful one-liners

```bash
# View running container logs
docker compose logs -f onboarding

# Open a shell inside the container
docker compose exec onboarding bash

# Check DuckDB warehouse size
du -sh data/warehouse.duckdb

# List all tables in the warehouse
docker compose exec onboarding python -c "
import duckdb
con = duckdb.connect('/workspace/data/warehouse.duckdb')
print(con.execute(\"SELECT table_schema, table_name FROM information_schema.tables ORDER BY 1,2\").fetchdf().to_string())
"

# Kill the dbt docs server if it's running in the background
docker compose exec onboarding bash -c "pkill -f 'dbt docs serve' || true"
```
