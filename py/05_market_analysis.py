"""
Task 5 — Market Analysis & Tableau Export
Week 6: IDX Exchange MLS Analytics Internship

Builds aggregated analysis tables from the clean, enriched datasets
and exports them as Tableau-ready CSVs.

Analysis tables produced:
  1. Monthly median price trends vs. mortgage rate
  2. Monthly days-on-market trends
  3. Monthly inventory (new listings) vs. sales volume
  4. Absorption rate by month (sales / active listings)
  5. Median price by county (all-time)
  6. Median price by Unified School District (all-time)
  7. DOM distribution by county
  8. Price per sq ft trends by month
  9. List-to-close ratio trends by month
 10. Top cities by sales volume

Reads from:
  data/processed/sold_with_districts.csv
  data/processed/listings_with_districts.csv

Saves Tableau-ready CSVs to:
  data/processed/tableau/
"""

import pandas as pd
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
PROCESSED_DIR = Path("data/processed")
TABLEAU_DIR   = PROCESSED_DIR / "tableau"
TABLEAU_DIR.mkdir(parents=True, exist_ok=True)

INPUT_SOLD     = PROCESSED_DIR / "sold_with_districts.csv"
INPUT_LISTINGS = PROCESSED_DIR / "listings_with_districts.csv"

# ── Load datasets ──────────────────────────────────────────────────────────────
print("=" * 60)
print("Loading datasets ...")

sold     = pd.read_csv(INPUT_SOLD,     low_memory=False)
listings = pd.read_csv(INPUT_LISTINGS, low_memory=False)

# Parse dates
sold["CloseDate"]               = pd.to_datetime(sold["CloseDate"],               errors="coerce")
sold["ListingContractDate"]     = pd.to_datetime(sold["ListingContractDate"],      errors="coerce")
listings["ListingContractDate"] = pd.to_datetime(listings["ListingContractDate"],  errors="coerce")

# Ensure year_month is a sortable string (already stored as "YYYY-MM")
sold["year_month"]     = sold["CloseDate"].dt.to_period("M").astype(str)
listings["year_month"] = listings["ListingContractDate"].dt.to_period("M").astype(str)

print(f"Sold     loaded : {len(sold):,} rows")
print(f"Listings loaded : {len(listings):,} rows")

# ── 1. Monthly median price trends vs. mortgage rate ──────────────────────────
print("\n[1] Monthly median price trends vs. mortgage rate ...")

monthly_price = (
    sold.groupby("year_month")
    .agg(
        median_close_price  = ("ClosePrice",       "median"),
        median_list_price   = ("ListPrice",        "median"),
        median_price_per_sqft = ("price_per_sqft", "median"),
        avg_rate_30yr       = ("rate_30yr_fixed",  "mean"),
        sales_count         = ("ClosePrice",       "count"),
    )
    .round(2)
    .reset_index()
    .sort_values("year_month")
)

monthly_price.to_csv(TABLEAU_DIR / "01_monthly_price_vs_rate.csv", index=False)
print(f"  Saved: 01_monthly_price_vs_rate.csv  ({len(monthly_price)} months)")

# ── 2. Monthly days-on-market trends ──────────────────────────────────────────
print("[2] Monthly days-on-market trends ...")

monthly_dom = (
    sold.groupby("year_month")
    .agg(
        median_dom = ("DaysOnMarket", "median"),
        mean_dom   = ("DaysOnMarket", "mean"),
        count      = ("DaysOnMarket", "count"),
    )
    .round(2)
    .reset_index()
    .sort_values("year_month")
)

monthly_dom.to_csv(TABLEAU_DIR / "02_monthly_dom_trends.csv", index=False)
print(f"  Saved: 02_monthly_dom_trends.csv  ({len(monthly_dom)} months)")

# ── 3. Monthly inventory (new listings) vs. sales volume ──────────────────────
print("[3] Monthly inventory vs. sales volume ...")

monthly_listings_count = (
    listings.groupby("year_month")
    .size()
    .reset_index(name="new_listings")
)

monthly_sales_count = (
    sold.groupby("year_month")
    .size()
    .reset_index(name="sales_count")
)

monthly_inventory = (
    monthly_listings_count
    .merge(monthly_sales_count, on="year_month", how="outer")
    .sort_values("year_month")
    .fillna(0)
)
monthly_inventory["new_listings"] = monthly_inventory["new_listings"].astype(int)
monthly_inventory["sales_count"]  = monthly_inventory["sales_count"].astype(int)

monthly_inventory.to_csv(TABLEAU_DIR / "03_monthly_inventory_vs_sales.csv", index=False)
print(f"  Saved: 03_monthly_inventory_vs_sales.csv  ({len(monthly_inventory)} months)")

# ── 4. Absorption rate by month (sales / new listings) ────────────────────────
print("[4] Absorption rate by month ...")

absorption = monthly_inventory.copy()
# Absorption rate = sales / new listings (what % of new inventory sold that month)
absorption["absorption_rate"] = (
    absorption["sales_count"] / absorption["new_listings"].replace(0, float("nan"))
).round(4)

absorption.to_csv(TABLEAU_DIR / "04_monthly_absorption_rate.csv", index=False)
print(f"  Saved: 04_monthly_absorption_rate.csv  ({len(absorption)} months)")

# ── 5. Median price by county ──────────────────────────────────────────────────
print("[5] Median price by county ...")

price_by_county = (
    sold.groupby("CountyOrParish")
    .agg(
        median_close_price    = ("ClosePrice",       "median"),
        median_price_per_sqft = ("price_per_sqft",   "median"),
        median_dom            = ("DaysOnMarket",      "median"),
        sales_count           = ("ClosePrice",        "count"),
    )
    .round(2)
    .reset_index()
    .sort_values("sales_count", ascending=False)
)

price_by_county.to_csv(TABLEAU_DIR / "05_price_by_county.csv", index=False)
print(f"  Saved: 05_price_by_county.csv  ({len(price_by_county)} counties)")

# ── 6. Median price by Unified School District ────────────────────────────────
print("[6] Median price by Unified School District ...")

price_by_district = (
    sold.dropna(subset=["DistrictName"])
    .groupby("DistrictName")
    .agg(
        median_close_price    = ("ClosePrice",       "median"),
        median_price_per_sqft = ("price_per_sqft",   "median"),
        median_dom            = ("DaysOnMarket",      "median"),
        sales_count           = ("ClosePrice",        "count"),
    )
    .round(2)
    .reset_index()
    .sort_values("sales_count", ascending=False)
)

price_by_district.to_csv(TABLEAU_DIR / "06_price_by_school_district.csv", index=False)
print(f"  Saved: 06_price_by_school_district.csv  ({len(price_by_district)} districts)")

# ── 7. DOM distribution by county ─────────────────────────────────────────────
print("[7] DOM distribution by county ...")

dom_by_county = (
    sold.groupby(["CountyOrParish", "dom_bucket"])
    .size()
    .reset_index(name="count")
    .sort_values(["CountyOrParish", "dom_bucket"])
)

dom_by_county.to_csv(TABLEAU_DIR / "07_dom_distribution_by_county.csv", index=False)
print(f"  Saved: 07_dom_distribution_by_county.csv  ({len(dom_by_county)} rows)")

# ── 8. Price per sq ft trends by month ────────────────────────────────────────
print("[8] Price per sq ft trends by month ...")

ppsf_monthly = (
    sold.groupby("year_month")
    .agg(
        median_price_per_sqft = ("price_per_sqft", "median"),
        mean_price_per_sqft   = ("price_per_sqft", "mean"),
        count                 = ("price_per_sqft", "count"),
    )
    .round(2)
    .reset_index()
    .sort_values("year_month")
)

ppsf_monthly.to_csv(TABLEAU_DIR / "08_price_per_sqft_monthly.csv", index=False)
print(f"  Saved: 08_price_per_sqft_monthly.csv  ({len(ppsf_monthly)} months)")

# ── 9. List-to-close ratio trends by month ────────────────────────────────────
print("[9] List-to-close ratio trends by month ...")

ltc_monthly = (
    sold.groupby("year_month")
    .agg(
        mean_list_to_close   = ("list_to_close_ratio", "mean"),
        median_list_to_close = ("list_to_close_ratio", "median"),
        count                = ("list_to_close_ratio", "count"),
    )
    .round(4)
    .reset_index()
    .sort_values("year_month")
)

ltc_monthly.to_csv(TABLEAU_DIR / "09_list_to_close_ratio_monthly.csv", index=False)
print(f"  Saved: 09_list_to_close_ratio_monthly.csv  ({len(ltc_monthly)} months)")

# ── 10. Top cities by sales volume ────────────────────────────────────────────
print("[10] Top cities by sales volume ...")

top_cities = (
    sold.groupby("City")
    .agg(
        sales_count           = ("ClosePrice",       "count"),
        median_close_price    = ("ClosePrice",       "median"),
        median_price_per_sqft = ("price_per_sqft",   "median"),
        median_dom            = ("DaysOnMarket",      "median"),
        avg_list_to_close     = ("list_to_close_ratio", "mean"),
    )
    .round(2)
    .reset_index()
    .sort_values("sales_count", ascending=False)
    .head(100)
)

top_cities.to_csv(TABLEAU_DIR / "10_top_cities_by_sales.csv", index=False)
print(f"  Saved: 10_top_cities_by_sales.csv  (top {len(top_cities)} cities)")

# ── Summary ────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("All Tableau export files saved to data/processed/tableau/")
print()
print("Quick market summary:")
print(f"  Date range (sold)   : {sold['year_month'].min()} to {sold['year_month'].max()}")
print(f"  Overall median close price : ${sold['ClosePrice'].median():,.0f}")
print(f"  Overall median DOM         : {sold['DaysOnMarket'].median():.0f} days")
print(f"  Overall median $/sqft      : ${sold['price_per_sqft'].median():,.0f}")
print(f"  Overall avg rate (30yr)    : {sold['rate_30yr_fixed'].mean():.2f}%")

print("\nDone.")
