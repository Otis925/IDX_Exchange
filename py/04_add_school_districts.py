"""
Task 4 — Add Unified School District to Properties
IDX Exchange MLS Analytics Internship

Spatially joins each property's latitude/longitude to California
Unified School District boundaries (2025-26) from data.ca.gov.
Adds a DistrictName column to both the sold and listings clean datasets.

Reads from:
  data/processed/sold_clean.csv
  data/processed/listings_clean.csv
  data/geo/ca_school_districts_2526.geojson

Saves to:
  data/processed/sold_with_districts.csv
  data/processed/listings_with_districts.csv
"""

import pandas as pd
import geopandas as gpd
from pathlib import Path
from shapely.geometry import Point

# ── Paths ──────────────────────────────────────────────────────────────────────
PROCESSED_DIR = Path("data/processed")
GEO_DIR       = Path("data/geo")

INPUT_SOLD      = PROCESSED_DIR / "sold_clean.csv"
INPUT_LISTINGS  = PROCESSED_DIR / "listings_clean.csv"
GEOJSON_PATH    = GEO_DIR / "ca_school_districts_2526.geojson"

OUTPUT_SOLD     = PROCESSED_DIR / "sold_with_districts.csv"
OUTPUT_LISTINGS = PROCESSED_DIR / "listings_with_districts.csv"

# ── Load school district boundaries ───────────────────────────────────────────
print("=" * 60)
print("Loading California school district boundaries ...")

districts = gpd.read_file(GEOJSON_PATH)
print(f"  Total districts loaded : {len(districts):,}")
print(f"  CRS                    : {districts.crs}")

# Filter to Unified school districts only
unified = districts[districts["DistrictType"] == "Unified"].copy()
unified = unified.reset_index(drop=True)
print(f"  Unified districts only : {len(unified):,}")

# Keep only the columns we need for the join
unified = unified[["DistrictName", "CountyName", "geometry"]]

# Ensure the CRS is WGS84 (standard lat/lon) so it matches our property coords
unified = unified.to_crs(epsg=4326)

# ── Helper: spatial join ───────────────────────────────────────────────────────
def add_school_district(df: pd.DataFrame, lat_col: str, lon_col: str, label: str) -> pd.DataFrame:
    """
    Convert lat/lon to Points, spatial-join to unified district polygons,
    and return the dataframe with DistrictName added.
    """
    print(f"\n{label} — building geometry from {lat_col} / {lon_col} ...")

    # Drop rows where lat/lon is missing so we can build valid Points
    has_coords = df[lat_col].notna() & df[lon_col].notna()
    df_with    = df[has_coords].copy()
    df_without = df[~has_coords].copy()
    print(f"  Rows with valid coords    : {len(df_with):,}")
    print(f"  Rows missing coords       : {len(df_without):,}")

    # Build a GeoDataFrame from lat/lon
    geometry = [Point(lon, lat) for lon, lat in zip(df_with[lon_col], df_with[lat_col])]
    gdf = gpd.GeoDataFrame(df_with, geometry=geometry, crs="EPSG:4326")

    # Spatial join — each property point gets matched to the district polygon it falls in
    joined = gpd.sjoin(gdf, unified, how="left", predicate="within")

    # sjoin adds index_right and may duplicate columns — keep only what we need
    joined = joined.drop(columns=["geometry", "index_right", "CountyName"], errors="ignore")

    # Convert back to a plain DataFrame
    joined = pd.DataFrame(joined)

    # Re-attach rows that had no coordinates (they get NaN for DistrictName)
    df_without["DistrictName"] = None
    result = pd.concat([joined, df_without], ignore_index=True)

    matched     = result["DistrictName"].notna().sum()
    unmatched   = result["DistrictName"].isna().sum()
    print(f"  Matched to a district     : {matched:,}")
    print(f"  No district match (NaN)   : {unmatched:,}")

    return result

# ── Process sold dataset ───────────────────────────────────────────────────────
print("\n" + "=" * 60)
sold = pd.read_csv(INPUT_SOLD, low_memory=False)
print(f"Sold loaded: {len(sold):,} rows")

sold_enriched = add_school_district(sold, lat_col="Latitude", lon_col="Longitude", label="SOLD")

# ── Process listings dataset ───────────────────────────────────────────────────
print("\n" + "=" * 60)
listings = pd.read_csv(INPUT_LISTINGS, low_memory=False)
print(f"Listings loaded: {len(listings):,} rows")

listings_enriched = add_school_district(listings, lat_col="Latitude", lon_col="Longitude", label="LISTINGS")

# ── Spot check ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SOLD — Top 10 Unified School Districts by listing count:")
print(sold_enriched["DistrictName"].value_counts().head(10).to_string())

print("\nLISTINGS — Top 10 Unified School Districts by listing count:")
print(listings_enriched["DistrictName"].value_counts().head(10).to_string())

# ── Save enriched datasets ─────────────────────────────────────────────────────
print("\n" + "=" * 60)
sold_enriched.to_csv(OUTPUT_SOLD, index=False)
print(f"Saved: {OUTPUT_SOLD}  ({len(sold_enriched):,} rows, {sold_enriched.shape[1]} columns)")

listings_enriched.to_csv(OUTPUT_LISTINGS, index=False)
print(f"Saved: {OUTPUT_LISTINGS}  ({len(listings_enriched):,} rows, {listings_enriched.shape[1]} columns)")

print("\nDone.")
