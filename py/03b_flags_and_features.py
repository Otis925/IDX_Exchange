"""
Task 3b — Date/Geo Flags and Week 6 Feature Engineering
Weeks 4-6: IDX Exchange MLS Analytics Internship

Fills the remaining deliverable requirements from Weeks 4-5 and Week 6
that were not included in 03_clean_and_engineer.py:

  Weeks 4-5 additions:
    - Date consistency flags (listing_after_close_flag,
      purchase_after_close_flag, negative_timeline_flag)
    - Geographic data quality flags (missing_coords_flag,
      zero_coords_flag, positive_longitude_flag, out_of_state_flag)
    - Negative bedrooms / bathrooms flags

  Week 6 additions:
    - listing_to_contract_days (PurchaseContractDate - ListingContractDate)
    - contract_to_close_days  (CloseDate - PurchaseContractDate)
    - close_to_original_list_ratio (ClosePrice / OriginalListPrice)
    - YrMo (e.g. "2024-01") derived from CloseDate

  Segment summary tables saved to data/processed/:
    - segment_by_county.csv
    - segment_by_subtype.csv
    - segment_by_list_office.csv

Reads from:
  data/processed/sold_with_districts.csv
  data/processed/listings_with_districts.csv

Saves updated files back to the same paths, then re-runs 06 and 07
inputs are automatically up to date.
"""

import pandas as pd
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
PROCESSED_DIR = Path("data/processed")

INPUT_SOLD     = PROCESSED_DIR / "sold_with_districts.csv"
INPUT_LISTINGS = PROCESSED_DIR / "listings_with_districts.csv"

OUTPUT_SOLD     = PROCESSED_DIR / "sold_with_districts.csv"
OUTPUT_LISTINGS = PROCESSED_DIR / "listings_with_districts.csv"

OUTPUT_SEG_COUNTY  = PROCESSED_DIR / "segment_by_county.csv"
OUTPUT_SEG_SUBTYPE = PROCESSED_DIR / "segment_by_subtype.csv"
OUTPUT_SEG_OFFICE  = PROCESSED_DIR / "segment_by_list_office.csv"

# ── Load ───────────────────────────────────────────────────────────────────────
print("=" * 60)
print("Loading datasets ...")

sold     = pd.read_csv(INPUT_SOLD,     low_memory=False)
listings = pd.read_csv(INPUT_LISTINGS, low_memory=False)

print(f"Sold     loaded : {len(sold):,} rows, {sold.shape[1]} columns")
print(f"Listings loaded : {len(listings):,} rows, {listings.shape[1]} columns")

# ── Parse date columns ─────────────────────────────────────────────────────────
DATE_COLS_SOLD = ["CloseDate", "ListingContractDate", "PurchaseContractDate"]
for col in DATE_COLS_SOLD:
    if col in sold.columns:
        sold[col] = pd.to_datetime(sold[col], errors="coerce")

if "ListingContractDate" in listings.columns:
    listings["ListingContractDate"] = pd.to_datetime(listings["ListingContractDate"], errors="coerce")

# ══════════════════════════════════════════════════════════════════════════════
# WEEKS 4-5 — DATE CONSISTENCY FLAGS
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("WEEKS 4-5 — Date Consistency Flags (SOLD) ...")

# ListingContractDate should not be after CloseDate
sold["listing_after_close_flag"] = (
    sold["ListingContractDate"].notna() & sold["CloseDate"].notna() &
    (sold["ListingContractDate"] > sold["CloseDate"])
)

# PurchaseContractDate should not be after CloseDate
if "PurchaseContractDate" in sold.columns:
    sold["purchase_after_close_flag"] = (
        sold["PurchaseContractDate"].notna() & sold["CloseDate"].notna() &
        (sold["PurchaseContractDate"] > sold["CloseDate"])
    )
else:
    sold["purchase_after_close_flag"] = False
    print("  WARNING: PurchaseContractDate not found — purchase_after_close_flag set to False")

# Any date ordering violation
sold["negative_timeline_flag"] = (
    sold["listing_after_close_flag"] | sold["purchase_after_close_flag"]
)

print(f"\n  listing_after_close_flag   : {sold['listing_after_close_flag'].sum():,} rows")
print(f"  purchase_after_close_flag  : {sold['purchase_after_close_flag'].sum():,} rows")
print(f"  negative_timeline_flag     : {sold['negative_timeline_flag'].sum():,} rows "
      f"({sold['negative_timeline_flag'].mean()*100:.2f}% of all sold)")

# ══════════════════════════════════════════════════════════════════════════════
# WEEKS 4-5 — GEOGRAPHIC DATA QUALITY FLAGS
# ══════════════════════════════════════════════════════════════════════════════

def add_geo_flags(df: pd.DataFrame, label: str) -> pd.DataFrame:
    """Add geographic data quality flag columns to df."""
    df = df.copy()

    lat = pd.to_numeric(df.get("Latitude"),  errors="coerce")
    lon = pd.to_numeric(df.get("Longitude"), errors="coerce")

    # Flag: Latitude or Longitude is null
    df["missing_coords_flag"] = lat.isna() | lon.isna()

    # Flag: Latitude == 0 or Longitude == 0 (null-island placeholder)
    df["zero_coords_flag"] = (lat == 0) | (lon == 0)

    # Flag: Longitude is positive — CA should be between -114 and -124
    df["positive_longitude_flag"] = lon > 0

    # Flag: coordinates are present and non-zero but fall outside California
    # CA approx bounds: lat 32.5–42.0, lon -124.5 to -114.1
    valid_check = ~df["missing_coords_flag"] & ~df["zero_coords_flag"] & ~df["positive_longitude_flag"]
    df["out_of_state_flag"] = valid_check & (
        (lat < 32.5) | (lat > 42.0) |
        (lon < -124.5) | (lon > -114.1)
    )

    total = len(df)
    print(f"\n{label} — Geographic data quality summary:")
    print(f"  missing_coords_flag    : {df['missing_coords_flag'].sum():>8,}  "
          f"({df['missing_coords_flag'].mean()*100:.2f}%)")
    print(f"  zero_coords_flag       : {df['zero_coords_flag'].sum():>8,}  "
          f"({df['zero_coords_flag'].mean()*100:.2f}%)")
    print(f"  positive_longitude_flag: {df['positive_longitude_flag'].sum():>8,}  "
          f"({df['positive_longitude_flag'].mean()*100:.2f}%)")
    print(f"  out_of_state_flag      : {df['out_of_state_flag'].sum():>8,}  "
          f"({df['out_of_state_flag'].mean()*100:.2f}%)")

    any_geo_bad = (
        df["missing_coords_flag"] | df["zero_coords_flag"] |
        df["positive_longitude_flag"] | df["out_of_state_flag"]
    )
    print(f"  any geographic issue   : {any_geo_bad.sum():>8,}  "
          f"({any_geo_bad.mean()*100:.2f}%)")
    print(f"  clean coordinates      : {(~any_geo_bad).sum():>8,}  "
          f"({(~any_geo_bad).mean()*100:.2f}%)")

    return df

print("\n" + "=" * 60)
print("WEEKS 4-5 — Geographic Data Quality Flags ...")

sold     = add_geo_flags(sold,     "SOLD")
listings = add_geo_flags(listings, "LISTINGS")

# ── Negative bedrooms / bathrooms flags ───────────────────────────────────────
print("\n" + "=" * 60)
print("WEEKS 4-5 — Negative Bedrooms / Bathrooms Flags ...")

for df, label in [(sold, "SOLD"), (listings, "LISTINGS")]:
    if "BedroomsTotal" in df.columns:
        bedrooms_neg = pd.to_numeric(df["BedroomsTotal"], errors="coerce") < 0
        df["negative_bedrooms_flag"] = bedrooms_neg
        print(f"  {label} negative_bedrooms_flag    : {bedrooms_neg.sum():,}")
    if "BathroomsTotalInteger" in df.columns:
        bathrooms_neg = pd.to_numeric(df["BathroomsTotalInteger"], errors="coerce") < 0
        df["negative_bathrooms_flag"] = bathrooms_neg
        print(f"  {label} negative_bathrooms_flag   : {bathrooms_neg.sum():,}")

# ══════════════════════════════════════════════════════════════════════════════
# WEEK 6 — ADDITIONAL FEATURE ENGINEERING
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("WEEK 6 — Additional Feature Engineering (SOLD) ...")

# YrMo: combined year-month string for easy Tableau filtering
sold["YrMo"] = sold["CloseDate"].dt.to_period("M").astype(str)

# close_to_original_list_ratio: how close final close price was to original list
sold["close_to_original_list_ratio"] = (
    sold["ClosePrice"] / pd.to_numeric(sold["OriginalListPrice"], errors="coerce").replace(0, float("nan"))
).round(4)

# listing_to_contract_days: how many days from listing to contract
if "PurchaseContractDate" in sold.columns:
    sold["listing_to_contract_days"] = (
        sold["PurchaseContractDate"] - sold["ListingContractDate"]
    ).dt.days
    print(f"  listing_to_contract_days  : {sold['listing_to_contract_days'].notna().sum():,} non-null  "
          f"| median {sold['listing_to_contract_days'].median():.0f} days")
else:
    sold["listing_to_contract_days"] = float("nan")
    print("  WARNING: PurchaseContractDate not found — listing_to_contract_days set to NaN")

# contract_to_close_days: how many days from contract to close
if "PurchaseContractDate" in sold.columns:
    sold["contract_to_close_days"] = (
        sold["CloseDate"] - sold["PurchaseContractDate"]
    ).dt.days
    print(f"  contract_to_close_days    : {sold['contract_to_close_days'].notna().sum():,} non-null  "
          f"| median {sold['contract_to_close_days'].median():.0f} days")
else:
    sold["contract_to_close_days"] = float("nan")
    print("  WARNING: PurchaseContractDate not found — contract_to_close_days set to NaN")

print(f"  close_to_original_list_ratio: {sold['close_to_original_list_ratio'].notna().sum():,} non-null  "
      f"| median {sold['close_to_original_list_ratio'].median():.4f}")
print(f"  YrMo                        : {sold['YrMo'].notna().sum():,} non-null  "
      f"| range {sold['YrMo'].min()} → {sold['YrMo'].max()}")

# ── Sample output table (required by handbook deliverable) ────────────────────
print("\nWeek 6 — Sample output (5 rows, key new columns):")
sample_cols = [
    "CloseDate", "ListingContractDate",
    "YrMo",
    "close_to_original_list_ratio",
    "listing_to_contract_days",
    "contract_to_close_days",
]
sample_cols = [c for c in sample_cols if c in sold.columns]
print(sold[sample_cols].dropna(subset=["listing_to_contract_days"]).head(5).to_string(index=False))

# ══════════════════════════════════════════════════════════════════════════════
# WEEK 6 — SEGMENT SUMMARY TABLES
# ══════════════════════════════════════════════════════════════════════════════

AGG_SPEC = dict(
    sales_count           = ("ClosePrice",                  "count"),
    median_close_price    = ("ClosePrice",                  "median"),
    median_dom            = ("DaysOnMarket",                "median"),
    median_price_per_sqft = ("price_per_sqft",              "median"),
    median_close_to_orig  = ("close_to_original_list_ratio","median"),
    median_list_to_close  = ("list_to_close_ratio",         "median"),
)

print("\n" + "=" * 60)
print("WEEK 6 — Segment Summary: by CountyOrParish ...")

seg_county = (
    sold.groupby("CountyOrParish")
    .agg(**AGG_SPEC)
    .round(2)
    .reset_index()
    .sort_values("sales_count", ascending=False)
)
seg_county.to_csv(OUTPUT_SEG_COUNTY, index=False)
print(f"  {len(seg_county)} counties  →  {OUTPUT_SEG_COUNTY}")

print("\nTop 10 counties by sales count:")
print(seg_county.head(10).to_string(index=False))

# ── Segment by PropertySubType ─────────────────────────────────────────────────
print("\n" + "=" * 60)
print("WEEK 6 — Segment Summary: by PropertySubType ...")

if "PropertySubType" in sold.columns:
    seg_subtype = (
        sold.groupby("PropertySubType")
        .agg(**AGG_SPEC)
        .round(2)
        .reset_index()
        .sort_values("sales_count", ascending=False)
    )
    seg_subtype.to_csv(OUTPUT_SEG_SUBTYPE, index=False)
    print(f"  {len(seg_subtype)} subtypes  →  {OUTPUT_SEG_SUBTYPE}")
    print(seg_subtype.to_string(index=False))
else:
    print("  WARNING: PropertySubType column not found — skipping.")

# ── Segment by ListOfficeName (top 50) ────────────────────────────────────────
print("\n" + "=" * 60)
print("WEEK 6 — Segment Summary: by ListOfficeName (top 50 by volume) ...")

if "ListOfficeName" in sold.columns:
    seg_office = (
        sold.groupby("ListOfficeName")
        .agg(**AGG_SPEC)
        .round(2)
        .reset_index()
        .sort_values("sales_count", ascending=False)
        .head(50)
    )
    seg_office.to_csv(OUTPUT_SEG_OFFICE, index=False)
    print(f"  Top 50 offices  →  {OUTPUT_SEG_OFFICE}")
    print(seg_office.head(10).to_string(index=False))
else:
    print("  WARNING: ListOfficeName column not found — skipping.")

# ══════════════════════════════════════════════════════════════════════════════
# SAVE UPDATED DATASETS
# ══════════════════════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("Saving updated datasets ...")

# Convert date columns back to strings for CSV compatibility
for col in DATE_COLS_SOLD:
    if col in sold.columns and pd.api.types.is_datetime64_any_dtype(sold[col]):
        sold[col] = sold[col].dt.strftime("%Y-%m-%d")

if pd.api.types.is_datetime64_any_dtype(listings.get("ListingContractDate")):
    listings["ListingContractDate"] = listings["ListingContractDate"].dt.strftime("%Y-%m-%d")

sold.to_csv(OUTPUT_SOLD, index=False)
print(f"Saved (sold)    : {OUTPUT_SOLD}  ({len(sold):,} rows, {sold.shape[1]} columns)")

listings.to_csv(OUTPUT_LISTINGS, index=False)
print(f"Saved (listings): {OUTPUT_LISTINGS}  ({len(listings):,} rows, {listings.shape[1]} columns)")

print("\n" + "=" * 60)
print("New columns added to SOLD:")
new_sold_cols = [
    "listing_after_close_flag", "purchase_after_close_flag", "negative_timeline_flag",
    "missing_coords_flag", "zero_coords_flag", "positive_longitude_flag", "out_of_state_flag",
    "negative_bedrooms_flag", "negative_bathrooms_flag",
    "YrMo", "close_to_original_list_ratio",
    "listing_to_contract_days", "contract_to_close_days",
]
for col in new_sold_cols:
    if col in sold.columns:
        print(f"  {col}")

print("\nNew columns added to LISTINGS:")
new_listings_cols = [
    "missing_coords_flag", "zero_coords_flag", "positive_longitude_flag", "out_of_state_flag",
    "negative_bedrooms_flag", "negative_bathrooms_flag",
]
for col in new_listings_cols:
    if col in listings.columns:
        print(f"  {col}")

print("\nNEXT STEPS:")
print("  Re-run 06_outlier_detection.py  (reads sold_with_districts.csv)")
print("  Re-run 07_tableau_prep.py        (reads sold_iqr_clean.csv)")
print("\nDone.")
