"""
Task 6 — Outlier Detection and Data Quality
Week 7: IDX Exchange MLS Analytics Internship

Uses the Interquartile Range (IQR) method to identify extreme values
in key numeric fields. Adds outlier flag columns rather than deleting
records, then saves two outputs:
  1. Full dataset with outlier flags
  2. Clean filtered dataset with all outliers removed

Fields analyzed: ClosePrice, LivingArea, DaysOnMarket,
                 price_per_sqft, list_to_close_ratio

Reads from:
  data/processed/sold_with_districts.csv

Saves to:
  data/processed/sold_flagged.csv   — all rows, with outlier flag columns
  data/processed/sold_iqr_clean.csv — rows with no outlier flags
"""

import pandas as pd
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
PROCESSED_DIR = Path("data/processed")

INPUT_SOLD         = PROCESSED_DIR / "sold_with_districts.csv"
OUTPUT_FLAGGED     = PROCESSED_DIR / "sold_flagged.csv"
OUTPUT_CLEAN       = PROCESSED_DIR / "sold_iqr_clean.csv"

# ── Load dataset ───────────────────────────────────────────────────────────────
print("=" * 60)
print("Loading sold dataset ...")

sold = pd.read_csv(INPUT_SOLD, low_memory=False)
print(f"Rows loaded: {len(sold):,}")

# ── IQR outlier detection ──────────────────────────────────────────────────────
# Fields to apply IQR filtering to
IQR_FIELDS = [
    "ClosePrice",
    "LivingArea",
    "DaysOnMarket",
    "price_per_sqft",
    "list_to_close_ratio",
]

def add_iqr_flags(df: pd.DataFrame, fields: list[str]) -> pd.DataFrame:
    """
    For each field, compute Q1, Q3, IQR, lower and upper bounds.
    Add a boolean flag column (<field>_outlier_flag) marking rows
    that fall outside the 1.5 * IQR range.
    """
    df = df.copy()
    for field in fields:
        if field not in df.columns:
            print(f"  WARNING: '{field}' not found — skipping.")
            continue

        series = pd.to_numeric(df[field], errors="coerce")

        q1    = series.quantile(0.25)
        q3    = series.quantile(0.75)
        iqr   = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        flag_col = f"{field}_outlier_flag"
        df[flag_col] = (series < lower) | (series > upper)

        flagged_count = df[flag_col].sum()
        print(f"  {field}:")
        print(f"    Q1={q1:,.2f}  Q3={q3:,.2f}  IQR={iqr:,.2f}")
        print(f"    Lower bound={lower:,.2f}  Upper bound={upper:,.2f}")
        print(f"    Outliers flagged: {flagged_count:,} rows ({flagged_count/len(df)*100:.2f}%)")

    return df

print("\n" + "=" * 60)
print("Applying IQR outlier detection ...")
sold_flagged = add_iqr_flags(sold, IQR_FIELDS)

# ── Create a combined any_outlier_flag ────────────────────────────────────────
flag_cols = [f"{f}_outlier_flag" for f in IQR_FIELDS if f in sold.columns]
sold_flagged["any_outlier_flag"] = sold_flagged[flag_cols].any(axis=1)

total_outliers = sold_flagged["any_outlier_flag"].sum()
print(f"\nRows flagged as outlier in ANY field : {total_outliers:,}")
print(f"Rows with no outlier flags            : {(~sold_flagged['any_outlier_flag']).sum():,}")

# ── Before / after comparison ──────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Before vs. After IQR filtering — size and median values:\n")

sold_clean = sold_flagged[~sold_flagged["any_outlier_flag"]].copy()

comparison_fields = ["ClosePrice", "LivingArea", "DaysOnMarket", "price_per_sqft", "list_to_close_ratio"]

print(f"{'Metric':<25} {'Before':>15} {'After':>15} {'Change':>10}")
print("-" * 65)
print(f"{'Row count':<25} {len(sold_flagged):>15,} {len(sold_clean):>15,} {len(sold_clean)-len(sold_flagged):>10,}")

for field in comparison_fields:
    if field not in sold_flagged.columns:
        continue
    before_median = pd.to_numeric(sold_flagged[field], errors="coerce").median()
    after_median  = pd.to_numeric(sold_clean[field],   errors="coerce").median()
    change        = after_median - before_median
    print(f"  median {field:<17} {before_median:>15,.2f} {after_median:>15,.2f} {change:>+10,.2f}")

# ── Save outputs ───────────────────────────────────────────────────────────────
print("\n" + "=" * 60)

sold_flagged.to_csv(OUTPUT_FLAGGED, index=False)
print(f"Saved (full flagged)   : {OUTPUT_FLAGGED}  ({len(sold_flagged):,} rows, {sold_flagged.shape[1]} columns)")

sold_clean.to_csv(OUTPUT_CLEAN, index=False)
print(f"Saved (IQR clean)      : {OUTPUT_CLEAN}  ({len(sold_clean):,} rows, {sold_clean.shape[1]} columns)")

print("\nDone.")
