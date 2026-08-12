"""
Task 7 — Tableau Data Preparation
Weeks 8-10: IDX Exchange MLS Analytics Internship

Generates all Tableau-ready aggregated source tables needed for both
market_analysis.twbx and competitive_analysis.twbx.

Reads from:
  data/processed/sold_iqr_clean.csv
  data/processed/listings_with_districts.csv

Saves to data/processed/tableau/:
  --- market_analysis.twbx sources ---
  ta_01_monthly_market_trends.csv       — median price, DOM, ratios, volume by month
  ta_02_monthly_new_listings.csv        — new listing counts by month
  ta_03_market_trends_combined.csv      — sold + listings merged on year_month (for combo charts)

  --- competitive_analysis.twbx sources ---
  ta_04_top100_listing_agents.csv       — top 100 agents by sales volume and units
  ta_05_top100_listing_offices.csv      — top 100 offices by sales volume and units
  ta_06_zipcode_median_price.csv        — median close price by zip code and month
  ta_07_zipcode_homes_sold.csv          — homes sold count by zip code and month
  ta_08_agent_detail.csv                — full agent-level sold records for filterable views
  ta_09_office_detail.csv               — full office-level sold records for filterable views
"""

import pandas as pd
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
PROCESSED_DIR = Path("data/processed")
TABLEAU_DIR   = PROCESSED_DIR / "tableau"
TABLEAU_DIR.mkdir(parents=True, exist_ok=True)

INPUT_SOLD     = PROCESSED_DIR / "sold_iqr_clean.csv"
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

# Ensure year_month is derived fresh from dates (clean string "YYYY-MM")
sold["year_month"]     = sold["CloseDate"].dt.to_period("M").astype(str)
listings["year_month"] = listings["ListingContractDate"].dt.to_period("M").astype(str)

# close_to_original_list_ratio = ClosePrice / OriginalListPrice
# (different from list_to_close_ratio which uses ListPrice)
sold["close_to_original_list_ratio"] = (
    sold["ClosePrice"] / sold["OriginalListPrice"].replace(0, float("nan"))
).round(4)

print(f"Sold loaded     : {len(sold):,} rows")
print(f"Listings loaded : {len(listings):,} rows")

# ══════════════════════════════════════════════════════════════════════════════
# MARKET ANALYSIS SOURCES
# ══════════════════════════════════════════════════════════════════════════════

# ── ta_01: Monthly market trends (sold) ───────────────────────────────────────
print("\n[1] Monthly market trends ...")

monthly_trends = (
    sold.groupby("year_month")
    .agg(
        median_close_price            = ("ClosePrice",                    "median"),
        mean_close_price              = ("ClosePrice",                    "mean"),
        median_list_price             = ("ListPrice",                     "median"),
        median_original_list_price    = ("OriginalListPrice",             "median"),
        median_dom                    = ("DaysOnMarket",                  "median"),
        mean_dom                      = ("DaysOnMarket",                  "mean"),
        median_price_per_sqft         = ("price_per_sqft",               "median"),
        mean_close_to_orig_list_ratio = ("close_to_original_list_ratio", "mean"),
        median_close_to_orig_list_ratio=("close_to_original_list_ratio", "median"),
        avg_rate_30yr_fixed           = ("rate_30yr_fixed",              "mean"),
        closed_sales_count            = ("ClosePrice",                    "count"),
    )
    .round(4)
    .reset_index()
    .sort_values("year_month")
)

monthly_trends.to_csv(TABLEAU_DIR / "ta_01_monthly_market_trends.csv", index=False)
print(f"  Saved: ta_01_monthly_market_trends.csv  ({len(monthly_trends)} months)")

# ── ta_02: Monthly new listings count ─────────────────────────────────────────
print("[2] Monthly new listings ...")

monthly_listings = (
    listings.groupby("year_month")
    .agg(
        new_listings_count = ("ListingKey", "count"),
        median_list_price  = ("ListPrice",  "median"),
    )
    .round(2)
    .reset_index()
    .sort_values("year_month")
)

monthly_listings.to_csv(TABLEAU_DIR / "ta_02_monthly_new_listings.csv", index=False)
print(f"  Saved: ta_02_monthly_new_listings.csv  ({len(monthly_listings)} months)")

# ── ta_03: Combined monthly trends (sold + listings merged) ───────────────────
print("[3] Combined monthly trends ...")

monthly_combined = monthly_trends.merge(
    monthly_listings[["year_month", "new_listings_count"]],
    on="year_month",
    how="outer"
).sort_values("year_month").fillna({"new_listings_count": 0, "closed_sales_count": 0})

# Absorption rate = closed sales / new listings
monthly_combined["absorption_rate"] = (
    monthly_combined["closed_sales_count"] /
    monthly_combined["new_listings_count"].replace(0, float("nan"))
).round(4)

monthly_combined.to_csv(TABLEAU_DIR / "ta_03_market_trends_combined.csv", index=False)
print(f"  Saved: ta_03_market_trends_combined.csv  ({len(monthly_combined)} months)")

# ══════════════════════════════════════════════════════════════════════════════
# COMPETITIVE ANALYSIS SOURCES
# ══════════════════════════════════════════════════════════════════════════════

# ── ta_04: Top 100 listing agents ─────────────────────────────────────────────
print("[4] Top 100 listing agents ...")

top_agents = (
    sold.groupby(["ListAgentFullName", "ListAgentEmail"])
    .agg(
        units_sold            = ("ClosePrice",       "count"),
        total_sales_volume    = ("ClosePrice",       "sum"),
        median_close_price    = ("ClosePrice",       "median"),
        median_dom            = ("DaysOnMarket",     "median"),
        median_price_per_sqft = ("price_per_sqft",  "median"),
        avg_close_to_orig     = ("close_to_original_list_ratio", "mean"),
        office_name           = ("ListOfficeName",   "first"),
        county                = ("CountyOrParish",   lambda x: x.mode().iloc[0] if not x.mode().empty else None),
        city                  = ("City",             lambda x: x.mode().iloc[0] if not x.mode().empty else None),
    )
    .round(2)
    .reset_index()
    .sort_values("total_sales_volume", ascending=False)
    .head(100)
)

top_agents.to_csv(TABLEAU_DIR / "ta_04_top100_listing_agents.csv", index=False)
print(f"  Saved: ta_04_top100_listing_agents.csv  ({len(top_agents)} agents)")

# ── ta_05: Top 100 listing offices ────────────────────────────────────────────
print("[5] Top 100 listing offices ...")

top_offices = (
    sold.groupby("ListOfficeName")
    .agg(
        units_sold            = ("ClosePrice",       "count"),
        total_sales_volume    = ("ClosePrice",       "sum"),
        median_close_price    = ("ClosePrice",       "median"),
        median_dom            = ("DaysOnMarket",     "median"),
        median_price_per_sqft = ("price_per_sqft",  "median"),
        avg_close_to_orig     = ("close_to_original_list_ratio", "mean"),
        unique_agents         = ("ListAgentFullName", "nunique"),
    )
    .round(2)
    .reset_index()
    .sort_values("total_sales_volume", ascending=False)
    .head(100)
)

top_offices.to_csv(TABLEAU_DIR / "ta_05_top100_listing_offices.csv", index=False)
print(f"  Saved: ta_05_top100_listing_offices.csv  ({len(top_offices)} offices)")

# ── ta_06: Zip code median close price by month ───────────────────────────────
print("[6] Zip code median close price by month ...")

zip_price = (
    sold.dropna(subset=["PostalCode"])
    .groupby(["PostalCode", "year_month", "CountyOrParish", "City"])
    .agg(
        median_close_price    = ("ClosePrice",      "median"),
        median_price_per_sqft = ("price_per_sqft", "median"),
        homes_sold            = ("ClosePrice",      "count"),
    )
    .round(2)
    .reset_index()
    .sort_values(["PostalCode", "year_month"])
)

zip_price.to_csv(TABLEAU_DIR / "ta_06_zipcode_median_price.csv", index=False)
print(f"  Saved: ta_06_zipcode_median_price.csv  ({len(zip_price):,} rows)")

# ── ta_07: Zip code homes sold by month ───────────────────────────────────────
print("[7] Zip code homes sold by month ...")

zip_sold = (
    sold.dropna(subset=["PostalCode"])
    .groupby(["PostalCode", "year_month", "CountyOrParish", "City"])
    .agg(
        homes_sold         = ("ClosePrice",  "count"),
        median_close_price = ("ClosePrice",  "median"),
        median_dom         = ("DaysOnMarket","median"),
    )
    .round(2)
    .reset_index()
    .sort_values(["PostalCode", "year_month"])
)

zip_sold.to_csv(TABLEAU_DIR / "ta_07_zipcode_homes_sold.csv", index=False)
print(f"  Saved: ta_07_zipcode_homes_sold.csv  ({len(zip_sold):,} rows)")

# ── ta_08: Agent detail table (for filterable competitive views) ───────────────
print("[8] Agent detail records ...")

agent_cols = [
    "year_month", "CloseDate", "ClosePrice", "ListPrice", "OriginalListPrice",
    "LivingArea", "DaysOnMarket", "price_per_sqft", "close_to_original_list_ratio",
    "ListAgentFullName", "ListAgentEmail", "ListOfficeName",
    "City", "CountyOrParish", "PostalCode", "PropertySubType",
    "BedroomsTotal", "BathroomsTotalInteger", "DistrictName",
]
agent_detail = sold[[c for c in agent_cols if c in sold.columns]].copy()

agent_detail.to_csv(TABLEAU_DIR / "ta_08_agent_detail.csv", index=False)
print(f"  Saved: ta_08_agent_detail.csv  ({len(agent_detail):,} rows)")

# ── ta_09: Office detail table (for filterable competitive views) ──────────────
print("[9] Office detail records ...")

office_cols = [
    "year_month", "CloseDate", "ClosePrice", "ListPrice", "OriginalListPrice",
    "LivingArea", "DaysOnMarket", "price_per_sqft", "close_to_original_list_ratio",
    "ListOfficeName", "ListAgentFullName",
    "City", "CountyOrParish", "PostalCode", "PropertySubType",
    "BedroomsTotal", "BathroomsTotalInteger", "DistrictName",
]
office_detail = sold[[c for c in office_cols if c in sold.columns]].copy()

office_detail.to_csv(TABLEAU_DIR / "ta_09_office_detail.csv", index=False)
print(f"  Saved: ta_09_office_detail.csv  ({len(office_detail):,} rows)")

# ── Summary ────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("All Tableau prep files saved to data/processed/tableau/")
print()
print("Files for market_analysis.twbx:")
print("  ta_01_monthly_market_trends.csv")
print("  ta_02_monthly_new_listings.csv")
print("  ta_03_market_trends_combined.csv")
print()
print("Files for competitive_analysis.twbx:")
print("  ta_04_top100_listing_agents.csv")
print("  ta_05_top100_listing_offices.csv")
print("  ta_06_zipcode_median_price.csv")
print("  ta_07_zipcode_homes_sold.csv")
print("  ta_08_agent_detail.csv")
print("  ta_09_office_detail.csv")

print("\nDone.")
