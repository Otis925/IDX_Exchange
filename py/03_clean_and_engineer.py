"""
Task 3 — Clean Data and Engineer Features
Weeks 4-5: IDX Exchange MLS Analytics Internship

Week 4: Removes invalid rows and drops columns with >90% missing data.
Week 5: Adds derived columns useful for market analysis.

Reads from:
  data/processed/sold_with_rates.csv
  data/processed/listings_with_rates.csv

Saves to:
  data/processed/sold_clean.csv
  data/processed/listings_clean.csv
"""

import pandas as pd
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
PROCESSED_DIR = Path("data/processed")

INPUT_SOLD     = PROCESSED_DIR / "sold_with_rates.csv"
INPUT_LISTINGS = PROCESSED_DIR / "listings_with_rates.csv"

OUTPUT_SOLD     = PROCESSED_DIR / "sold_clean.csv"
OUTPUT_LISTINGS = PROCESSED_DIR / "listings_clean.csv"

# ── Load datasets ──────────────────────────────────────────────────────────────
print("=" * 60)
print("Loading enriched datasets ...")

sold     = pd.read_csv(INPUT_SOLD,     low_memory=False)
listings = pd.read_csv(INPUT_LISTINGS, low_memory=False)

print(f"Sold     loaded : {len(sold):,} rows, {sold.shape[1]} columns")
print(f"Listings loaded : {len(listings):,} rows, {listings.shape[1]} columns")

# ══════════════════════════════════════════════════════════════════════════════
# WEEK 4 — DATA CLEANING
# ══════════════════════════════════════════════════════════════════════════════

# ── Step 1: Drop columns with >90% missing values ──────────────────────────────
print("\n" + "=" * 60)
print("WEEK 4 — Step 1: Dropping columns with >90% missing ...")

def drop_high_missing(df: pd.DataFrame, threshold: float = 90.0) -> tuple[pd.DataFrame, list[str]]:
    """Drop columns where missing percentage exceeds threshold."""
    missing_pct = df.isnull().mean() * 100
    cols_to_drop = missing_pct[missing_pct > threshold].index.tolist()
    return df.drop(columns=cols_to_drop), cols_to_drop

sold_dropped_cols: list[str]
listings_dropped_cols: list[str]

sold,     sold_dropped_cols     = drop_high_missing(sold)
listings, listings_dropped_cols = drop_high_missing(listings)

print(f"  Sold     — dropped {len(sold_dropped_cols)} columns: {sold_dropped_cols}")
print(f"  Listings — dropped {len(listings_dropped_cols)} columns: {listings_dropped_cols}")
print(f"  Sold     remaining columns : {sold.shape[1]}")
print(f"  Listings remaining columns : {listings.shape[1]}")

# ── Step 2: Remove invalid rows from sold ──────────────────────────────────────
print("\n" + "=" * 60)
print("WEEK 4 — Step 2: Removing invalid rows from SOLD ...")

rows_before = len(sold)

# ClosePrice must be > 0
sold = sold[sold["ClosePrice"] > 0]
print(f"  After ClosePrice > 0       : {len(sold):,} rows  (removed {rows_before - len(sold):,})")

# ListPrice must be > 0
n = len(sold)
sold = sold[sold["ListPrice"] > 0]
print(f"  After ListPrice > 0        : {len(sold):,} rows  (removed {n - len(sold):,})")

# OriginalListPrice must be > 0 (only where it exists)
n = len(sold)
sold = sold[(sold["OriginalListPrice"].isnull()) | (sold["OriginalListPrice"] > 0)]
print(f"  After OriginalListPrice > 0: {len(sold):,} rows  (removed {n - len(sold):,})")

# LivingArea must be > 0 and <= 20,000 sq ft
n = len(sold)
sold = sold[(sold["LivingArea"].isnull()) | ((sold["LivingArea"] > 0) & (sold["LivingArea"] <= 20000))]
print(f"  After LivingArea 1–20000   : {len(sold):,} rows  (removed {n - len(sold):,})")

# DaysOnMarket must be >= 0
n = len(sold)
sold = sold[sold["DaysOnMarket"] >= 0]
print(f"  After DaysOnMarket >= 0    : {len(sold):,} rows  (removed {n - len(sold):,})")

print(f"\n  Sold total removed : {rows_before - len(sold):,} rows")
print(f"  Sold rows remaining: {len(sold):,}")

# ── Step 3: Remove invalid rows from listings ──────────────────────────────────
print("\n" + "=" * 60)
print("WEEK 4 — Step 3: Removing invalid rows from LISTINGS ...")

rows_before = len(listings)

# ListPrice must be > 0
listings = listings[listings["ListPrice"] > 0]
print(f"  After ListPrice > 0        : {len(listings):,} rows  (removed {rows_before - len(listings):,})")

# OriginalListPrice must be > 0 (only where it exists)
n = len(listings)
listings = listings[(listings["OriginalListPrice"].isnull()) | (listings["OriginalListPrice"] > 0)]
print(f"  After OriginalListPrice > 0: {len(listings):,} rows  (removed {n - len(listings):,})")

# LivingArea must be > 0 and <= 20,000 sq ft
n = len(listings)
listings = listings[(listings["LivingArea"].isnull()) | ((listings["LivingArea"] > 0) & (listings["LivingArea"] <= 20000))]
print(f"  After LivingArea 1–20000   : {len(listings):,} rows  (removed {n - len(listings):,})")

# DaysOnMarket must be >= 0
n = len(listings)
listings = listings[listings["DaysOnMarket"] >= 0]
print(f"  After DaysOnMarket >= 0    : {len(listings):,} rows  (removed {n - len(listings):,})")

print(f"\n  Listings total removed : {rows_before - len(listings):,} rows")
print(f"  Listings rows remaining: {len(listings):,}")

# ══════════════════════════════════════════════════════════════════════════════
# WEEK 5 — FEATURE ENGINEERING
# ══════════════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("WEEK 5 — Feature Engineering ...")

# ── Parse date columns ─────────────────────────────────────────────────────────
sold["CloseDate"]            = pd.to_datetime(sold["CloseDate"],            errors="coerce")
sold["ListingContractDate"]  = pd.to_datetime(sold["ListingContractDate"],  errors="coerce")
listings["ListingContractDate"] = pd.to_datetime(listings["ListingContractDate"], errors="coerce")

# ── Sold: date-based features ──────────────────────────────────────────────────
sold["close_year"]    = sold["CloseDate"].dt.year
sold["close_month"]   = sold["CloseDate"].dt.month
sold["close_quarter"] = sold["CloseDate"].dt.quarter
sold["list_year"]     = sold["ListingContractDate"].dt.year
sold["list_month"]    = sold["ListingContractDate"].dt.month

# ── Listings: date-based features ─────────────────────────────────────────────
listings["list_year"]  = listings["ListingContractDate"].dt.year
listings["list_month"] = listings["ListingContractDate"].dt.month

# ── Sold: price-based features ─────────────────────────────────────────────────
# Price per square foot
sold["price_per_sqft"] = (sold["ClosePrice"] / sold["LivingArea"]).round(2)

# How close the final sale price was to the list price (1.0 = sold at full ask)
sold["list_to_close_ratio"] = (sold["ClosePrice"] / sold["ListPrice"]).round(4)

# How much the price was reduced from original list to final list price
sold["price_reduction"]     = (sold["OriginalListPrice"] - sold["ListPrice"]).round(2)
sold["price_reduction_pct"] = ((sold["price_reduction"] / sold["OriginalListPrice"]) * 100).round(2)

# ── Listings: price-based features ────────────────────────────────────────────
listings["price_per_sqft"]      = (listings["ListPrice"] / listings["LivingArea"]).round(2)
listings["price_reduction"]     = (listings["OriginalListPrice"] - listings["ListPrice"]).round(2)
listings["price_reduction_pct"] = ((listings["price_reduction"] / listings["OriginalListPrice"]) * 100).round(2)

# ── Days-on-market buckets (both datasets) ─────────────────────────────────────
dom_bins   = [0, 7, 30, 90, float("inf")]
dom_labels = ["0-7 days", "8-30 days", "31-90 days", "90+ days"]

sold["dom_bucket"]     = pd.cut(sold["DaysOnMarket"],     bins=dom_bins, labels=dom_labels, right=True)
listings["dom_bucket"] = pd.cut(listings["DaysOnMarket"], bins=dom_bins, labels=dom_labels, right=True)

# ── Print feature engineering summary ─────────────────────────────────────────
print("\nNew columns added to SOLD:")
new_sold_cols = [
    "close_year", "close_month", "close_quarter",
    "list_year", "list_month",
    "price_per_sqft", "list_to_close_ratio",
    "price_reduction", "price_reduction_pct",
    "dom_bucket",
]
for col in new_sold_cols:
    non_null = sold[col].notna().sum()
    print(f"  {col}: {non_null:,} non-null values")

print("\nNew columns added to LISTINGS:")
new_listings_cols = [
    "list_year", "list_month",
    "price_per_sqft",
    "price_reduction", "price_reduction_pct",
    "dom_bucket",
]
for col in new_listings_cols:
    non_null = listings[col].notna().sum()
    print(f"  {col}: {non_null:,} non-null values")

# ── Quick sanity check on key engineered features ──────────────────────────────
print("\nSOLD — Engineered feature spot check:")
print(f"  price_per_sqft   median : ${sold['price_per_sqft'].median():,.0f}")
print(f"  list_to_close_ratio mean: {sold['list_to_close_ratio'].mean():.4f}")
print(f"  price_reduction  median : ${sold['price_reduction'].median():,.0f}")
print(f"  dom_bucket distribution :")
print(sold["dom_bucket"].value_counts().sort_index().to_string())

print("\nLISTINGS — Engineered feature spot check:")
print(f"  price_per_sqft   median : ${listings['price_per_sqft'].median():,.0f}")
print(f"  price_reduction  median : ${listings['price_reduction'].median():,.0f}")
print(f"  dom_bucket distribution :")
print(listings["dom_bucket"].value_counts().sort_index().to_string())

# ── Save final clean datasets ──────────────────────────────────────────────────
print("\n" + "=" * 60)

# Convert dom_bucket (Categorical) to string for CSV compatibility
sold["dom_bucket"]     = sold["dom_bucket"].astype(str)
listings["dom_bucket"] = listings["dom_bucket"].astype(str)

sold.to_csv(OUTPUT_SOLD, index=False)
print(f"Saved: {OUTPUT_SOLD}  ({len(sold):,} rows, {sold.shape[1]} columns)")

listings.to_csv(OUTPUT_LISTINGS, index=False)
print(f"Saved: {OUTPUT_LISTINGS}  ({len(listings):,} rows, {listings.shape[1]} columns)")

print("\nDone.")
