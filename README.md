# Workforce Planning & Labour Market Intelligence

A production-grade Python data engineering pipeline and analysis database designed to model, audit, and benchmark organizational workforce rosters against macroeconomic UK labor supply, ASHE earnings, and Adzuna job postings data.

This project identifies skills gaps, succession/retirement risks, and internal-to-market salary disparities across key UK shortage sectors (Technology, Green Energy, and Healthcare).

---

## Data Provenance & Methodology

**This project uses a 4-tier hybrid data strategy.** Every dataset is explicitly classified below. No actual employee PII is used or generated.

### Tier 1: Fully Synthetic

| Dataset | Source | Notes |
|---|---|---|
| `internal_workforce.csv` | `generate_synthetic_hr.py` (seed=42) | 800 HR roster records containing employee ages, salaries, skills, and succession flags. |
| `internal_job_descriptions.json` | `generate_synthetic_hr.py` | Template-generated role descriptions. |
| `extracted_jd_skills.csv` | TF-IDF scan on synthetic JDs | Predefined taxonomy keyword mapping (not AI text-mining). |

### Tier 2: Calibrated / Statistically Modelled

| Dataset | Calibrated To | Accuracy Caveat |
|---|---|---|
| `ons_ashe_salaries.csv` | ONS ASHE 2024/2025 published medians by SOC + regional multipliers | Point estimates. Not statistically validated against full ASHE microdata. |
| `ons_vacancies.csv` | ONS VACS02 vacancy volumes by SOC and region | Growth trends applied at category level; regional breakdown uses fixed weights. |
| `ons_labor_supply.csv` | ONS Labour Force Survey employment + graduate pipeline data | Approximate retirement risk rates and graduate supply. |

### Tier 3: Real (Live API)

| Dataset | Source | Status |
|---|---|---|
| `nomis_region_wage_index.json` | Nomis API (NM_99_1) | Fetched live at runtime. Falls back to cached values if API is offline. |

### Tier 4: Hybrid (Real API + Mock Fallback)

| Dataset | Source | Status |
|---|---|---|
| `adzuna_vacancies.csv` | Adzuna API (via `ADZUNA_APP_ID` / `ADZUNA_APP_KEY`) | Fetched live if API credentials are provided. Falls back to 3,000 seeded synthetic postings. |

### Benchmark KPI Targets
Key metrics (e.g., **-26.3%** London Software Developer salary gap, **41.0%** Battery Design Engineer retirement risk) are targeted in verification scripts (`verify_db.py`, `tests/test_data_quality.py`) to enable deterministic validation across DuckDB, SQLite, and PowerBI.

---

## Technical Stack & Architecture

- **Language**: Python 3.10+ (Type annotated, PEP 8 structured, centralized logging)
- **Data Ingestion, ETL & Storage**: Pandas (for utility data handling) and SQLite (serving as the staging repository, analytical query engine, and Power BI relational database)
- **Taxonomy Mapping**: Scikit-Learn TF-IDF vectorization (relevance scoring of skills requirements in job descriptions)
- **Visualization**: Power BI Star Schema representation
- **Database Migration Utilities**: Oracle DDL/DML setup generator (available for C-Suite LiveSQL review)

---

## Directory Structure

```text
├── data/
│   ├── raw/                      # Ingested datasets (synthetic HR roster, ONS ASHE, ONS supply, vacancy indexes)
│   └── processed/
│       ├── powerbi/              # Processed Star Schema CSV files for Power BI model ingestion
│       └── workforce_intelligence.sqlite  # Compiled SQLite database (staging + analytical views + final Star Schema)
├── powerbi/                      # Completed Power BI (.pbix) dashboard and PDF report
├── queries/                      # SQL query scripts (market demand, salary gaps, skills mismatch, detailed skills gap, succession risk)
├── reports/                      # Generated CSV reports, Oracle setup, Power BI guide, and Executive Briefing
├── scripts/                      # Modular Python processing components
│   ├── config.py                 # Centralized configuration mappings and taxonomies
│   ├── utils.py                  # Shared utilities (casing, TF-IDF taxonomy keyword matcher, logging)
│   ├── generate_synthetic_hr.py  # Produces synthetic corporate HR lists and JDs (fixed seed for reproducibility)
│   ├── fetch_nomis.py            # Acquires ONS ASHE, vacancy, and labor supply datasets
│   ├── fetch_adzuna.py           # Contacts Adzuna API (or falls back to seeded mock job postings generation)
│   ├── process_data.py           # Ingests raw data to SQLite, builds staging views, and exports Star Schema CSVs
│   ├── generate_oracle_setup.py  # Standalone utility to compile Oracle LiveSQL setup DDL/DML scripts
│   └── verify_db.py              # Executes diagnostic assertions against SQLite analytical views
├── requirements.txt              # Standard package requirements (Pandas, Scikit-Learn, HTTPX, xlsxwriter)
├── run_pipeline.py               # Main pipeline orchestrator script
└── workforce_intelligence.sqbpro # SQLite database project file
```

---

## Getting Started

### 1. Installation

Create a virtual environment and install the required dependencies:

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install packages
pip install -r requirements.txt
```

### 2. Execute Data Pipeline

Run the orchestrator script to generate synthetic files, retrieve ONS indices, extract skill metrics, compile databases, and export report datasets:

```powershell
python run_pipeline.py
```

Running the pipeline refreshes:
1. Staged database records inside DuckDB and SQLite.
2. The downsampled Oracle SQL insert queries (`reports/oracle_schema_setup.sql`).
3. Power BI modeling CSV files (`data/processed/powerbi/`).
4. Analytical CSV summaries under `reports/`.

### 3. Running SQL Queries

Analytical SQL files are stored in [queries/](queries/). You can execute them directly on the SQLite database or upload the [reports/oracle_schema_setup.sql](reports/oracle_schema_setup.sql) script to **Oracle Live SQL** to verify data alignment.

---

## KPI & Verification Checks

To confirm data pipeline compilation integrity, verify the following metrics in your analytics dashboard:
1. **Software Developer (London)**: Visualizes a salary lag of exactly **-26.3%** (£47,907 avg internal salary vs £65,040 ONS median salary).
2. **Battery Design Engineer**: Reflects a 5-year retirement risk of exactly **41.0%** and **11** critical roles currently operating without a designated successor.

