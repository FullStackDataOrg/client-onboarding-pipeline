"""
Extraction module for Google Ads spend data.

Google Ads uses deliberately different column names vs Meta (report_date vs date,
ad_group_id vs campaign_id, imps/clks vs impressions/clicks, cost_usd vs spend_cents).
This is the schema drift that the Bronze layer resolves.
"""

import os
import pandas as pd
from pathlib import Path

DATA_DIR = Path(os.environ.get("DATA_DIR", "/workspace/data"))


def extract_google_ads() -> pd.DataFrame:
    """Return raw Google Ads spend as a DataFrame with source-native column names."""
    csv_path = DATA_DIR / "google_ads_raw.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Google Ads CSV not found at {csv_path}. Run seed_data.py first."
        )
    df = pd.read_csv(csv_path, parse_dates=["report_date"])
    return df


if __name__ == "__main__":
    df = extract_google_ads()
    print(f"Google Ads: {len(df)} rows | {df['ad_group_id'].nunique()} ad groups")
    print(df.dtypes)
    print(df.head(3))
