# IDX Exchange MLS Analytics Dashboard Project

## Overview

This repository contains the Python data pipeline and Tableau dashboard work for the IDX Exchange MLS Analytics summer project. The goal of the project is to transform monthly CRMLS listing and sold transaction files into cleaned, analysis-ready datasets, then use those datasets to build housing market dashboards and a short market intelligence report.

The project follows a full analytics workflow:

1. Collect monthly MLS listing and sold CSV files.
2. Combine monthly files into unified listing and sold datasets.
3. Filter the data to residential properties.
4. Clean and validate transaction, date, price, and geographic fields.
5. Add external mortgage rate data from FRED.
6. Engineer housing market metrics.
7. Detect and flag outliers.
8. Build Tableau dashboards for market analysis and competitive intelligence.
9. Summarize findings in a final market intelligence report and presentation.

---

## Project Goals

The main goal is to create reliable housing market intelligence from raw MLS transaction data.

Key business questions include:

- How are median close prices changing over time?
- How long are homes staying on the market?
- Are homes selling above or below their original list prices?
- Which cities, counties, or zip codes are most active?
- Which agents and offices lead in sales volume and transaction count?
- How do market conditions vary by property subtype?
- How do mortgage rates relate to market trends over time?

---

## Tech Stack

- **Python**
- **Pandas**
- **Tableau Public / Tableau Desktop Public Edition**
- **FRED mortgage rate data**
- **CRMLS Listing and Sold CSV files**
- **CoreLogic Trestle / IDX Exchange data pipeline**

---

## Repository Structure

```text
.
├── README.md
├── data/
│   ├── raw/
│   │   ├── CRMLSListingYYYYMM.csv
│   │   └── CRMLSSoldYYYYMM.csv
│   ├── processed/
│   │   ├── combined_listings.csv
│   │   ├── combined_sold.csv
│   │   ├── listings_with_rates.csv
│   │   ├── sold_with_rates.csv
│   │   ├── cleaned_listings.csv
│   │   ├── cleaned_sold.csv
│   │   ├── flagged_sold.csv
│   │   └── filtered_sold.csv
│   └── external/
│       └── mortgage_rates_monthly.csv
├── scripts/
│   ├── 00_extract_data.py
│   ├── 01_aggregate_monthly_files.py
│   ├── 02_validate_and_profile_data.py
│   ├── 03_merge_mortgage_rates.py
│   ├── 04_clean_data.py
│   ├── 05_feature_engineering.py
│   └── 06_outlier_detection.py
├── tableau/
│   ├── market_analysis.twbx
│   └── competitive_analysis.twbx
├── reports/
│   ├── market_intelligence_report.pdf
│   └── presentation_slides.pdf
└── requirements.txt
```

> Note: The exact file names may differ depending on how the project is organized locally.

---

## Data Inputs

The project uses two main monthly MLS dataset types:

```text
CRMLSListingYYYYMM.csv
CRMLSSoldYYYYMM.csv
```

Each file represents a monthly extract of CRMLS listing or sold transaction records. The target date range is from **January 2024 through the most recently completed calendar month**.

Because the MLS data is confidential, raw CSV files should not be committed to a public repository.

Recommended `.gitignore` entries:

```text
data/raw/
data/processed/
*.csv
*.xlsx
*.twbx
.env
```

If Tableau workbooks need to be shared, confirm whether they contain embedded confidential data before uploading them.

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone <repository-url>
cd <repository-name>
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` has not been created yet, install the main packages manually:

```bash
pip install pandas requests numpy matplotlib
```

---

## Workflow

### Step 1: Aggregate Monthly Files

Combine all monthly listing files and all monthly sold files into two unified datasets.

Script:

```bash
python scripts/01_aggregate_monthly_files.py
```

Expected outputs:

```text
data/processed/combined_listings.csv
data/processed/combined_sold.csv
```

This step should also filter both datasets to:

```python
PropertyType == "Residential"
```

---

### Step 2: Validate and Profile the Data

Inspect the structure of each dataset.

Checks include:

- Number of rows and columns
- Column names
- Data types
- Unique property types
- Null counts
- Columns with more than 90% missing values
- Summary statistics for key fields

Script:

```bash
python scripts/02_validate_and_profile_data.py
```

Important fields to inspect:

```text
ClosePrice
ListPrice
OriginalListPrice
LivingArea
LotSizeAcres
BedroomsTotal
BathroomsTotalInteger
DaysOnMarket
YearBuilt
```

---

### Step 3: Merge Mortgage Rate Data

Fetch the national 30-year fixed mortgage rate from FRED, convert the weekly series into monthly averages, and merge it into both the listing and sold datasets.

Script:

```bash
python scripts/03_merge_mortgage_rates.py
```

Expected outputs:

```text
data/processed/listings_with_rates.csv
data/processed/sold_with_rates.csv
```

The merge should use a `year_month` key.

For sold records, the key should be based on:

```text
CloseDate
```

For listing records, the key should be based on:

```text
ListingContractDate
```

---

### Step 4: Clean the Data

Clean and standardize the datasets for analysis.

Tasks include:

- Convert date columns to datetime format.
- Remove unnecessary or redundant columns.
- Handle missing values.
- Ensure numeric fields are correctly typed.
- Remove or flag invalid values.
- Validate transaction timelines.
- Validate geographic coordinates.

Script:

```bash
python scripts/04_clean_data.py
```

Date fields to convert:

```text
CloseDate
PurchaseContractDate
ListingContractDate
ContractStatusChangeDate
```

Invalid records to flag include:

```text
ClosePrice <= 0
LivingArea <= 0
DaysOnMarket < 0
Negative bedroom or bathroom counts
Missing latitude or longitude
Latitude = 0 or Longitude = 0
Longitude > 0 for California properties
Out-of-state or implausible coordinates
```

Suggested date consistency flags:

```text
listing_after_close_flag
purchase_after_close_flag
negative_timeline_flag
```

---

### Step 5: Engineer Market Metrics

Create new columns that power the Tableau dashboards.

Script:

```bash
python scripts/05_feature_engineering.py
```

Key engineered metrics:

| Metric | Formula | Purpose |
|---|---|---|
| Price Ratio | `ClosePrice / OriginalListPrice` | Measures negotiation strength |
| Price Per Sq Ft | `ClosePrice / LivingArea` | Normalizes price across home sizes |
| Days on Market | `DaysOnMarket` | Measures time to sell |
| Year | Derived from `CloseDate` | Enables yearly analysis |
| Month | Derived from `CloseDate` | Enables monthly analysis |
| YrMo | Derived from `CloseDate` | Enables time-series dashboarding |
| Listing to Contract Days | `PurchaseContractDate - ListingContractDate` | Measures time from listing to accepted offer |
| Contract to Close Days | `CloseDate - PurchaseContractDate` | Measures escrow / closing period |

Optional enhancement:

- Add school district information using property latitude and longitude.

---

### Step 6: Detect and Flag Outliers

Identify extreme values that could distort market analysis.

Script:

```bash
python scripts/06_outlier_detection.py
```

Recommended fields for outlier checks:

```text
ClosePrice
LivingArea
DaysOnMarket
PricePerSqFt
CloseToOriginalListRatio
```

Use a flag-first approach. Do not permanently delete raw records. Save both:

```text
data/processed/flagged_sold.csv
data/processed/filtered_sold.csv
```

The filtered dataset should be used for cleaner analysis, while the flagged dataset preserves the full record set.

---

## Tableau Dashboards

The final project includes two Tableau workbooks.

### 1. Market Analysis Workbook

File:

```text
tableau/market_analysis.twbx
```

Required dashboards:

- Monthly median close price
- Average days on market
- Average close-to-original-list price ratio
- New listings
- Closed sales
- One custom market analysis dashboard

Dashboards should be filterable by:

- City
- County
- Zip code
- Property subtype

---

### 2. Competitive Analysis Workbook

File:

```text
tableau/competitive_analysis.twbx
```

Required dashboards:

- Top 100 listing agents by sales volume and units
- Top 100 listing offices by sales volume and units
- Zip code heat map of median close prices
- Zip code heat map of homes sold
- One custom competitive analysis dashboard

Dashboards should be filterable by:

- Month
- City
- County
- Zip code
- Property subtype

---

## Final Deliverables

The final project package should include:

1. Cleaned and processed CSV datasets
2. Well-commented Python scripts
3. `market_analysis.twbx`
4. `competitive_analysis.twbx`
5. Published Tableau Public dashboards
6. A 1-page market intelligence report
7. A 5-minute presentation

---

## Market Intelligence Report Structure

The final 1-page report should focus on one county, city, or zip code.

Recommended structure:

### Market Overview

Summarize median home price trends and days on market.

### Pricing Trends

Discuss price per square foot and close-to-original-list price ratio.

### Market Activity

Compare new listings, closed sales, and transaction volume.

### Competitive Landscape

Identify the top agents and brokerages by sales volume and units.

### Key Takeaways

List 3–5 data-driven insights discovered during the analysis.

---

## Confidentiality Notice

This project uses MLS transaction records that are confidential and intended only for IDX Exchange internship work. Do not publicly share raw MLS data, processed datasets, credentials, or Tableau workbooks containing embedded confidential records unless approved.

---

## Author

Otis Tsai  
IDX Exchange Data Analyst Intern
