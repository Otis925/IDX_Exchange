"""
Task 1 / Week 1 — Aggregate Monthly MLS Files
----------------------------------------------
Reads all monthly CRMLS Listing and Sold CSV files from data/raw/,
concatenates them into two combined DataFrames, filters to Residential
properties only, and saves the results to data/processed/.
"""

import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# ROOT_DIR is the top-level project folder (one level above this script)
ROOT_DIR = Path(__file__).resolve().parent.parent

RAW_DIR = ROOT_DIR / "data" / "raw"
PROCESSED_DIR = ROOT_DIR / "data" / "processed"

# Make sure the output folder exists
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Discover monthly files
# ---------------------------------------------------------------------------

# Collect all Listing files (e.g. CRMLSListing202401.csv) and sort by name
# so they end up in chronological order.
listing_files = sorted(RAW_DIR.glob("CRMLSListing*.csv"))

# Collect all Sold files (e.g. CRMLSSold202401.csv) and sort the same way.
sold_files = sorted(RAW_DIR.glob("CRMLSSold*.csv"))

print(f"Listing files found : {len(listing_files)}")
print(f"Sold files found    : {len(sold_files)}")

# ---------------------------------------------------------------------------
# Helper: read files one by one, print row counts, then concatenate
# ---------------------------------------------------------------------------

def read_and_concat(file_list: list[Path], label: str) -> pd.DataFrame:
    """
    Reads each CSV in file_list, prints its row count, concatenates all of
    them, and returns the combined DataFrame.

    Parameters
    ----------
    file_list : list of Path objects pointing to CSV files
    label     : short name used in print statements ("Listings" or "Sold")
    """
    if not file_list:
        print(f"\nNo {label} files found — returning empty DataFrame.")
        return pd.DataFrame()

    print(f"\n--- {label} file row counts ---")
    frames = []
    for f in file_list:
        df = pd.read_csv(f, encoding="ISO-8859-1", low_memory=False)
        print(f"  {f.name}: {len(df):,} rows")
        frames.append(df)

    combined = pd.concat(frames, ignore_index=True)
    print(f"Total {label} rows after concatenation: {len(combined):,}")
    return combined

# ---------------------------------------------------------------------------
# Read and concatenate
# ---------------------------------------------------------------------------

listings_df = read_and_concat(listing_files, "Listings")
sold_df     = read_and_concat(sold_files,    "Sold")

# ---------------------------------------------------------------------------
# Filter to Residential only
# ---------------------------------------------------------------------------

print("\n--- Residential filter ---")

if not listings_df.empty:
    listings_before = len(listings_df)
    listings_df = listings_df[listings_df["PropertyType"] == "Residential"]
    print(f"Listings before filter : {listings_before:,}")
    print(f"Listings after filter  : {len(listings_df):,}")

if not sold_df.empty:
    sold_before = len(sold_df)
    sold_df = sold_df[sold_df["PropertyType"] == "Residential"]
    print(f"Sold before filter     : {sold_before:,}")
    print(f"Sold after filter      : {len(sold_df):,}")

# ---------------------------------------------------------------------------
# Save outputs
# ---------------------------------------------------------------------------

listings_out = PROCESSED_DIR / "combined_listings_residential.csv"
sold_out     = PROCESSED_DIR / "combined_sold_residential.csv"

if not listings_df.empty:
    listings_df.to_csv(listings_out, index=False)
    print(f"\nSaved listings → {listings_out}")

if not sold_df.empty:
    sold_df.to_csv(sold_out, index=False)
    print(f"Saved sold     → {sold_out}")

print("\nDone.")
