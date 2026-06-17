"""
Extraction module for the ClientCo customer database.

The source system provides full snapshots (no CDC), so every run replaces the
entire raw.customers table. The dbt snapshot (snap_customers) handles history.
"""

import os
import pandas as pd
from pathlib import Path

DATA_DIR = Path(os.environ.get("DATA_DIR", "/workspace/data"))


def extract_customers() -> pd.DataFrame:
    """Return today's full customer snapshot as a DataFrame."""
    csv_path = DATA_DIR / "customers_raw.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Customers CSV not found at {csv_path}. Run seed_data.py first."
        )
    df = pd.read_csv(csv_path, parse_dates=["signup_date", "_loaded_at"])
    return df


if __name__ == "__main__":
    df = extract_customers()
    print(f"Customers: {len(df)} rows | plan distribution:")
    print(df["plan_tier"].value_counts())
    print(df.head(3))
