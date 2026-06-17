import os
import pandas as pd
from pathlib import Path
from dagster import asset, AssetExecutionContext
from dagster_duckdb import DuckDBResource

DATA_DIR = Path(os.environ.get("DATA_DIR", "/workspace/data"))


@asset(
    group_name="raw",
    description="Daily campaign performance from Meta Ads. Idempotent load via CREATE OR REPLACE.",
    compute_kind="python",
)
def raw_meta_ads_spend(context: AssetExecutionContext, duckdb: DuckDBResource) -> None:
    csv = DATA_DIR / "meta_ads_raw.csv"
    df = pd.read_csv(csv)
    with duckdb.get_connection() as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS raw")
        conn.execute(
            "CREATE OR REPLACE TABLE raw.meta_ads_spend AS "
            "SELECT *, CURRENT_TIMESTAMP AS _loaded_at FROM df"
        )
    context.add_output_metadata({
        "num_rows": len(df),
        "campaigns": int(df["campaign_id"].nunique()),
        "path": str(csv),
    })


@asset(
    group_name="raw",
    description="Daily ad-group performance from Google Ads (different schema vs Meta — schema drift).",
    compute_kind="python",
)
def raw_google_ads_spend(context: AssetExecutionContext, duckdb: DuckDBResource) -> None:
    csv = DATA_DIR / "google_ads_raw.csv"
    df = pd.read_csv(csv)
    with duckdb.get_connection() as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS raw")
        conn.execute(
            "CREATE OR REPLACE TABLE raw.google_ads_spend AS "
            "SELECT *, CURRENT_TIMESTAMP AS _loaded_at FROM df"
        )
    context.add_output_metadata({
        "num_rows": len(df),
        "ad_groups": int(df["ad_group_id"].nunique()),
        "path": str(csv),
    })


@asset(
    group_name="raw",
    description="Full customer snapshot from the ClientCo app DB. CREATE OR REPLACE — no CDC.",
    compute_kind="python",
)
def raw_customers(context: AssetExecutionContext, duckdb: DuckDBResource) -> None:
    csv = DATA_DIR / "customers_raw.csv"
    df = pd.read_csv(csv)
    with duckdb.get_connection() as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS raw")
        conn.execute(
            "CREATE OR REPLACE TABLE raw.customers AS "
            "SELECT * EXCLUDE (_loaded_at), _loaded_at::TIMESTAMP AS _loaded_at FROM df"
        )
    context.add_output_metadata({
        "num_rows": len(df),
        "plan_distribution": df["plan_tier"].value_counts().to_dict(),
        "path": str(csv),
    })
