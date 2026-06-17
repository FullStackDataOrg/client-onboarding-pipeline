import os
from pathlib import Path
from dagster_duckdb import DuckDBResource
from dagster_dbt import DbtCliResource

_DUCKDB_PATH = os.environ.get("DUCKDB_PATH", "/workspace/data/warehouse.duckdb")
_DBT_PROJECT_DIR = os.environ.get("DBT_PROJECT_DIR", "/workspace/dbt_project")

duckdb_resource = DuckDBResource(database=_DUCKDB_PATH)

dbt_resource = DbtCliResource(
    project_dir=_DBT_PROJECT_DIR,
    profiles_dir=_DBT_PROJECT_DIR,
)
