"""
Fetch 30-Year Fixed Mortgage Rates from FRED
Weeks 2-3 (continued): IDX Exchange MLS Analytics Internship

Downloads the weekly 30-year fixed mortgage rate series (MORTGAGE30US)
from the Federal Reserve Economic Data (FRED) public CSV endpoint.
No API key required.

Saves two outputs:
  data/processed/fred_rates_weekly.csv  — raw weekly rates
  data/processed/fred_rates_monthly.csv — monthly averages (used for merging)
"""

import pandas as pd
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_WEEKLY  = PROCESSED_DIR / "fred_rates_weekly.csv"
OUTPUT_MONTHLY = PROCESSED_DIR / "fred_rates_monthly.csv"

# FRED public CSV endpoint — no API key needed
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"

# ── Fetch weekly rates ─────────────────────────────────────────────────────────
print("=" * 60)
print("Fetching 30-year fixed mortgage rate from FRED ...")

rates = pd.read_csv(FRED_URL)

# Rename columns to readable names
rates.columns = ["date", "rate_30yr_fixed"]

# Parse date column
rates["date"] = pd.to_datetime(rates["date"])

# FRED uses '.' for missing values — coerce to NaN and drop
rates["rate_30yr_fixed"] = pd.to_numeric(rates["rate_30yr_fixed"], errors="coerce")
rates = rates.dropna(subset=["rate_30yr_fixed"]).reset_index(drop=True)

print(f"  Weekly rows fetched : {len(rates):,}")
print(f"  Date range          : {rates['date'].min().date()} to {rates['date'].max().date()}")
print(f"  Rate range          : {rates['rate_30yr_fixed'].min()}% to {rates['rate_30yr_fixed'].max()}%")

# ── Save weekly rates ──────────────────────────────────────────────────────────
rates.to_csv(OUTPUT_WEEKLY, index=False)
print(f"\nSaved: {OUTPUT_WEEKLY}")

# ── Compute monthly averages ───────────────────────────────────────────────────
rates["year_month"] = rates["date"].dt.to_period("M")

monthly = (
    rates.groupby("year_month")["rate_30yr_fixed"]
    .mean()
    .round(4)
    .reset_index()
)

# Convert Period to string so the CSV is readable
monthly["year_month"] = monthly["year_month"].astype(str)

print(f"\nMonthly average rows : {len(monthly):,}")
print(f"\nMost recent 6 months:")
print(monthly.tail(6).to_string(index=False))

# ── Save monthly rates ─────────────────────────────────────────────────────────
monthly.to_csv(OUTPUT_MONTHLY, index=False)
print(f"\nSaved: {OUTPUT_MONTHLY}")

print("\nDone.")
