"""
Task 2 — Validate, Summarize, and Enrich MLS Data
Weeks 2-3: IDX Exchange MLS Analytics Internship

Loads the Residential-only combined datasets from Week 1,
runs validation and exploratory summaries, then merges in
30-year fixed mortgage rates from FRED.
"""

import pandas as pd
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
PROCESSED_DIR = Path("data/processed")

INPUT_LISTINGS = PROCESSED_DIR / "combined_listings_residential.csv"
INPUT_SOLD     = PROCESSED_DIR / "combined_sold_residential.csv"

FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=MORTGAGE30US"

# ── Load datasets ──────────────────────────────────────────────────────────────
print("=" * 60)
print("Loading datasets ...")

listings = pd.read_csv(INPUT_LISTINGS, low_memory=False)
sold     = pd.read_csv(INPUT_SOLD,     low_memory=False)

print(f"Listings loaded : {len(listings):,} rows")
print(f"Sold     loaded : {len(sold):,} rows")

# ── Basic dataset info ─────────────────────────────────────────────────────────
for label, df in [("LISTINGS", listings), ("SOLD", sold)]:
    print("\n" + "=" * 60)
    print(f"{label} — Basic Info")
    print(f"  Rows    : {df.shape[0]:,}")
    print(f"  Columns : {df.shape[1]}")
    print(f"  Column names:")
    for col in df.columns:
        print(f"    {col}")
    print(f"\n  Data types:")
    for col, dtype in df.dtypes.items():
        print(f"    {col}: {dtype}")

# ── Confirm Residential filter ─────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Unique PropertyType values (should be only 'Residential'):")
print(f"  Listings : {listings['PropertyType'].unique().tolist()}")
print(f"  Sold     : {sold['PropertyType'].unique().tolist()}")

# ── Missing value summaries ────────────────────────────────────────────────────
def missing_value_report(df: pd.DataFrame) -> pd.DataFrame:
    """Build a per-column missing count and percentage table."""
    missing_count = df.isnull().sum()
    missing_pct   = (missing_count / len(df) * 100).round(2)
    report = pd.DataFrame({
        "column":          missing_count.index,
        "missing_count":   missing_count.values,
        "missing_percent": missing_pct.values,
    })
    return report.sort_values("missing_percent", ascending=False).reset_index(drop=True)

listings_missing = missing_value_report(listings)
sold_missing     = missing_value_report(sold)

print("\n" + "=" * 60)
print("LISTINGS — Missing Value Summary (top 20):")
print(listings_missing.head(20).to_string(index=False))

print("\n" + "=" * 60)
print("SOLD — Missing Value Summary (top 20):")
print(sold_missing.head(20).to_string(index=False))

# ── Flag columns with more than 90% missing ────────────────────────────────────
print("\n" + "=" * 60)
listings_high_missing = listings_missing[listings_missing["missing_percent"] > 90]
sold_high_missing     = sold_missing[sold_missing["missing_percent"] > 90]

print(f"LISTINGS — columns with >90% missing ({len(listings_high_missing)}):")
for _, row in listings_high_missing.iterrows():
    print(f"  {row['column']}: {row['missing_percent']}%")

print(f"\nSOLD — columns with >90% missing ({len(sold_high_missing)}):")
for _, row in sold_high_missing.iterrows():
    print(f"  {row['column']}: {row['missing_percent']}%")

# ── Numeric distribution summaries ────────────────────────────────────────────
# Fields present in the sold dataset
SOLD_NUMERIC_COLS = [
    "ClosePrice",
    "LivingArea",
    "DaysOnMarket",
    "ListPrice",
    "OriginalListPrice",
]

# Fields present in the listings dataset
LISTINGS_NUMERIC_COLS = [
    "ListPrice",
    "OriginalListPrice",
    "LivingArea",
    "DaysOnMarket",
]

def numeric_summary(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """Return min/max/mean/median/p25/p75/count for selected numeric columns."""
    # Only keep columns that actually exist in this dataframe
    available = [c for c in cols if c in df.columns]
    rows = []
    for col in available:
        series = pd.to_numeric(df[col], errors="coerce").dropna()
        rows.append({
            "column": col,
            "count":  int(series.count()),
            "min":    series.min(),
            "p25":    series.quantile(0.25),
            "median": series.median(),
            "mean":   series.mean(),
            "p75":    series.quantile(0.75),
            "max":    series.max(),
        })
    return pd.DataFrame(rows)

listings_numeric = numeric_summary(listings, LISTINGS_NUMERIC_COLS)
sold_numeric     = numeric_summary(sold,     SOLD_NUMERIC_COLS)

print("\n" + "=" * 60)
print("LISTINGS — Numeric Distribution Summary:")
print(listings_numeric.to_string(index=False))

print("\n" + "=" * 60)
print("SOLD — Numeric Distribution Summary:")
print(sold_numeric.to_string(index=False))

# ── Save validation reports ────────────────────────────────────────────────────
listings_missing.to_csv(PROCESSED_DIR / "listings_missing_value_report.csv", index=False)
sold_missing.to_csv(    PROCESSED_DIR / "sold_missing_value_report.csv",     index=False)
listings_numeric.to_csv(PROCESSED_DIR / "listings_numeric_summary.csv",      index=False)
sold_numeric.to_csv(    PROCESSED_DIR / "sold_numeric_summary.csv",           index=False)

print("\n" + "=" * 60)
print("Saved: listings_missing_value_report.csv")
print("Saved: sold_missing_value_report.csv")
print("Saved: listings_numeric_summary.csv")
print("Saved: sold_numeric_summary.csv")

# ── Fetch 30-year fixed mortgage rate from FRED ────────────────────────────────
print("\n" + "=" * 60)
print("Fetching 30-year fixed mortgage rate from FRED ...")

rates = pd.read_csv(FRED_URL)

# Rename columns to readable names
rates.columns = ["date", "rate_30yr_fixed"]

# Parse the date column
rates["date"] = pd.to_datetime(rates["date"])

# Drop rows where the rate is missing (FRED uses '.' for missing values)
rates["rate_30yr_fixed"] = pd.to_numeric(rates["rate_30yr_fixed"], errors="coerce")
rates = rates.dropna(subset=["rate_30yr_fixed"])

print(f"  Weekly rate rows fetched: {len(rates):,}")
print(f"  Date range: {rates['date'].min().date()} to {rates['date'].max().date()}")

# Convert weekly rates to monthly averages
rates["year_month"] = rates["date"].dt.to_period("M")
monthly_rates = (
    rates.groupby("year_month")["rate_30yr_fixed"]
    .mean()
    .round(4)
    .reset_index()
)

print(f"  Monthly rate rows after averaging: {len(monthly_rates):,}")

# ── Enrich sold dataset ────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Enriching SOLD dataset with mortgage rates ...")

# Create year_month from CloseDate
sold["CloseDate"] = pd.to_datetime(sold["CloseDate"], errors="coerce")
sold["year_month"] = sold["CloseDate"].dt.to_period("M")

sold_enriched = sold.merge(monthly_rates, on="year_month", how="left")

missing_rate_sold = sold_enriched["rate_30yr_fixed"].isnull().sum()
print(f"  Sold rows missing mortgage rate after merge: {missing_rate_sold:,}")

# ── Enrich listings dataset ────────────────────────────────────────────────────
print("Enriching LISTINGS dataset with mortgage rates ...")

# Create year_month from ListingContractDate
listings["ListingContractDate"] = pd.to_datetime(
    listings["ListingContractDate"], errors="coerce"
)
listings["year_month"] = listings["ListingContractDate"].dt.to_period("M")

listings_enriched = listings.merge(monthly_rates, on="year_month", how="left")

missing_rate_listings = listings_enriched["rate_30yr_fixed"].isnull().sum()
print(f"  Listings rows missing mortgage rate after merge: {missing_rate_listings:,}")

# ── Save enriched datasets ─────────────────────────────────────────────────────
# Convert Period column to string before saving (Period is not CSV-serializable)
sold_enriched["year_month"]     = sold_enriched["year_month"].astype(str)
listings_enriched["year_month"] = listings_enriched["year_month"].astype(str)

sold_enriched.to_csv(    PROCESSED_DIR / "sold_with_rates.csv",     index=False)
listings_enriched.to_csv(PROCESSED_DIR / "listings_with_rates.csv", index=False)

print("\n" + "=" * 60)
print(f"Saved: sold_with_rates.csv     ({len(sold_enriched):,} rows)")
print(f"Saved: listings_with_rates.csv ({len(listings_enriched):,} rows)")

print("\nDone.")
