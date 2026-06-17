from dagster import Definitions, load_assets_from_modules
from pipeline.assets import ingestion, dbt_assets as dbt_assets_module
from pipeline.resources import duckdb_resource, dbt_resource
from pipeline.schedules import daily_refresh
from pipeline.sensors import source_freshness_sensor

defs = Definitions(
    assets=[
        *load_assets_from_modules([ingestion]),
        dbt_assets_module.onboarding_dbt_assets,
    ],
    resources={
        "duckdb": duckdb_resource,
        "dbt": dbt_resource,
    },
    schedules=[daily_refresh],
    sensors=[source_freshness_sensor],
)
