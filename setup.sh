#!/bin/bash
set -e

echo "==> Setting up Client Onboarding Pipeline..."

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt

mkdir -p data dagster_home

cat > .env << 'EOF'
DUCKDB_PATH=./data/warehouse.duckdb
DBT_PROFILES_DIR=./dbt_project
DAGSTER_HOME=./dagster_home
PYTHONPATH=./dagster_project
EOF

echo ""
echo "Done! Activate the environment and export vars:"
echo "  source .venv/bin/activate"
echo "  export \$(cat .env | xargs)"
echo ""
echo "Then run the pipeline:"
echo "  python ingestion/seed_data.py"
echo "  cd dbt_project && dbt deps && dbt parse && cd .."
echo "  dagster dev -f dagster_project/scale_army/definitions.py"
