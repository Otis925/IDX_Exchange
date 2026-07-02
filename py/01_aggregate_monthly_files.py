"""
Task 1 — Aggregate Monthly MLS Files
Week 1: IDX Exchange MLS Analytics Internship

Reads all unfilled monthly CRMLS CSV files from data/raw/,
concatenates them into two combined datasets (listings + sold),
filters to Residential property type, and saves to data/processed/.
"""

import pandas as pd
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
RAW_DIR = Path("data/raw")
PROCESSED_DIR = Path("data/processed")
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_LISTINGS = PROCESSED_DIR / "combined_listings_residential.csv"
OUTPUT_SOLD     = PROCESSED_DIR / "combined_sold_residential.csv"

# ── Helper: collect unfilled files ─────────────────────────────────────────────
def collect_files(prefix: str) -> tuple[list[Path], list[Path]]:
    """Return (selected, skipped_filled) for files matching the given prefix."""
    all_files = sorted(RAW_DIR.glob(f"{prefix}*.csv"))
    selected = [f for f in all_files if "filled" not in f.name.lower()]
    skipped  = [f for f in all_files if "filled" in f.name.lower()]
    return selected, skipped

# ── Helper: load and concatenate CSVs ──────────────────────────────────────────
def load_and_concat(files: list[Path], label: str) -> pd.DataFrame:
    """Read each CSV, print its row count, and return the concatenated DataFrame."""
    frames = []
    for f in files:
        df = pd.read_csv(f, low_memory=False)
        print(f"  {f.name}: {len(df):,} rows")
        frames.append(df)
    combined = pd.concat(frames, ignore_index=True)
    print(f"\n{label} total rows (all months combined): {len(combined):,}")
    return combined

# ── Collect files ──────────────────────────────────────────────────────────────
listing_files, listing_skipped = collect_files("CRMLSListing")
sold_files,    sold_skipped    = collect_files("CRMLSSold")

# ── Report selections ──────────────────────────────────────────────────────────
print("=" * 60)
print(f"Listing files selected : {len(listing_files)}")
print(f"Sold    files selected : {len(sold_files)}")

all_skipped = listing_skipped + sold_skipped
if all_skipped:
    print(f"\nFilled files skipped ({len(all_skipped)}):")
    for f in all_skipped:
        print(f"  SKIPPED: {f.name}")
else:
    print("\nNo filled files found to skip.")

# ── Load and concatenate ───────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("LISTINGS — per-file row counts:")
listings_all = load_and_concat(listing_files, "Listings")

print("\n" + "=" * 60)
print("SOLD — per-file row counts:")
sold_all = load_and_concat(sold_files, "Sold")

# ── Filter to Residential ──────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Filtering to PropertyType == 'Residential' ...")

listings_before = len(listings_all)
listings_res    = listings_all[listings_all["PropertyType"] == "Residential"].copy()
listings_after  = len(listings_res)
print(f"Listings  before filter: {listings_before:,}  →  after: {listings_after:,}")

sold_before = len(sold_all)
sold_res    = sold_all[sold_all["PropertyType"] == "Residential"].copy()
sold_after  = len(sold_res)
print(f"Sold      before filter: {sold_before:,}  →  after: {sold_after:,}")

# ── Save outputs ───────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
listings_res.to_csv(OUTPUT_LISTINGS, index=False)
print(f"Saved listings : {OUTPUT_LISTINGS}  ({listings_after:,} rows)")

sold_res.to_csv(OUTPUT_SOLD, index=False)
print(f"Saved sold     : {OUTPUT_SOLD}  ({sold_after:,} rows)")

print("\nDone.")
