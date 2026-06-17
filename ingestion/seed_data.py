#!/usr/bin/env python3
"""
Deterministic synthetic data generator for the client onboarding pipeline.

Generates 90 days of media spend across Meta and Google Ads, plus 5000 customers.
Re-running after the first time shifts a small cohort of customer plan tiers to
demonstrate SCD2 change capture in snap_customers.

Usage:
    python ingestion/seed_data.py
"""

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import date, timedelta, datetime

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

rng = np.random.default_rng(42)

START_DATE = date(2024, 1, 1)
DAYS = 90
dates = [START_DATE + timedelta(days=i) for i in range(DAYS)]

# ---------------------------------------------------------------------------
# Meta Ads — 50 campaigns, columns: date, campaign_id, campaign_name,
#            impressions, clicks, spend_cents
# ---------------------------------------------------------------------------
N_META = 50
META_TYPES = ["Brand", "Prospecting", "Retargeting", "Lookalike", "Seasonal"]
meta_ids = [f"MC_{i:04d}" for i in range(1, N_META + 1)]
meta_names = [f"Meta {META_TYPES[i % len(META_TYPES)]} {i:02d}" for i in range(N_META)]

meta_rows = []
for day in dates:
    for cid, cname in zip(meta_ids, meta_names):
        impressions = int(rng.integers(1_000, 50_000))
        clicks = int(impressions * rng.uniform(0.01, 0.05))
        cpm = rng.uniform(5.0, 25.0)
        spend_cents = int(impressions / 1000 * cpm * 100)
        meta_rows.append({
            "date": day.isoformat(),
            "campaign_id": cid,
            "campaign_name": cname,
            "impressions": impressions,
            "clicks": clicks,
            "spend_cents": spend_cents,
        })

meta_df = pd.DataFrame(meta_rows)
meta_df.to_csv(DATA_DIR / "meta_ads_raw.csv", index=False)
print(f"[meta]     {len(meta_df):>6} rows  |  {meta_df['campaign_id'].nunique()} campaigns")

# ---------------------------------------------------------------------------
# Google Ads — 30 ad groups, deliberately different column naming vs Meta
# Columns: report_date, ad_group_id, ad_group_name, imps, clks, cost_usd
# ---------------------------------------------------------------------------
N_GOOGLE = 30
GOOGLE_TYPES = ["Search-Brand", "Search-Generic", "Shopping", "Display", "YouTube"]
google_ids = [f"GA_{i:04d}" for i in range(1, N_GOOGLE + 1)]
google_names = [f"Google {GOOGLE_TYPES[i % len(GOOGLE_TYPES)]} {i:02d}" for i in range(N_GOOGLE)]

google_rows = []
for day in dates:
    for gid, gname in zip(google_ids, google_names):
        imps = int(rng.integers(500, 30_000))
        clks = int(imps * rng.uniform(0.02, 0.08))
        cpc = rng.uniform(0.50, 3.00)
        cost_usd = round(clks * cpc, 2)
        google_rows.append({
            "report_date": day.isoformat(),
            "ad_group_id": gid,
            "ad_group_name": gname,
            "imps": imps,
            "clks": clks,
            "cost_usd": cost_usd,
        })

google_df = pd.DataFrame(google_rows)
google_df.to_csv(DATA_DIR / "google_ads_raw.csv", index=False)
print(f"[google]   {len(google_df):>6} rows  |  {google_df['ad_group_id'].nunique()} ad groups")

# ---------------------------------------------------------------------------
# Customers — 5000 rows simulating a daily full snapshot from the app DB.
# Re-running upgrades ~50 customers to the next plan tier so that
# `dbt snapshot` records a new SCD2 row with a fresh dbt_valid_from.
# ---------------------------------------------------------------------------
N_CUSTOMERS = 5_000
PLAN_TIERS = ["free", "starter", "growth", "enterprise"]
PLAN_WEIGHTS = [0.40, 0.30, 0.20, 0.10]

FIRST_NAMES = [
    "Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry",
    "Iris", "Jack", "Karen", "Leo", "Mia", "Nathan", "Olivia", "Paul",
    "Quinn", "Rachel", "Sam", "Tara", "Uma", "Victor", "Wendy", "Xander",
    "Yara", "Zoe",
]
LAST_NAMES = [
    "Smith", "Jones", "Williams", "Brown", "Davis", "Miller", "Wilson",
    "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris",
    "Martin", "Thompson", "Garcia", "Martinez", "Robinson", "Clark",
]

first = rng.choice(FIRST_NAMES, N_CUSTOMERS)
last = rng.choice(LAST_NAMES, N_CUSTOMERS)
customer_ids = list(range(1, N_CUSTOMERS + 1))
emails = [f"{f.lower()}.{l.lower()}{i}@clientco.example" for i, f, l in zip(customer_ids, first, last)]
full_names = [f"{f} {l}" for f, l in zip(first, last)]
plan_tiers = rng.choice(PLAN_TIERS, N_CUSTOMERS, p=PLAN_WEIGHTS).tolist()
signup_dates = [
    (date(2022, 1, 1) + timedelta(days=int(rng.integers(0, 730)))).isoformat()
    for _ in range(N_CUSTOMERS)
]

customers_csv = DATA_DIR / "customers_raw.csv"

if customers_csv.exists():
    # Second-run mode: upgrade ~50 customers to the next plan tier to demo SCD2.
    existing = pd.read_csv(customers_csv)
    upgrade_indices = rng.choice(N_CUSTOMERS, size=50, replace=False)
    for idx in upgrade_indices:
        current = plan_tiers[idx]
        tier_pos = PLAN_TIERS.index(current)
        if tier_pos < len(PLAN_TIERS) - 1:
            plan_tiers[idx] = PLAN_TIERS[tier_pos + 1]
    print(f"[customers] Re-run detected — upgrading {len(upgrade_indices)} plan tiers for SCD2 demo")

loaded_at = datetime.utcnow().isoformat(timespec="seconds") + "Z"

customers_df = pd.DataFrame({
    "customer_id": customer_ids,
    "email": emails,
    "full_name": full_names,
    "plan_tier": plan_tiers,
    "signup_date": signup_dates,
    "_loaded_at": loaded_at,
})
customers_df.to_csv(customers_csv, index=False)
print(f"[customers] {len(customers_df):>6} rows  |  loaded_at={loaded_at}")

print("\nSeed data written to ./data/")
