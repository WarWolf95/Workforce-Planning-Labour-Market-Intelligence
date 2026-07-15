# Workforce Planning & Labour Market Intelligence

A production-grade Python data engineering pipeline and analysis database designed to model, audit, and benchmark organizational workforce rosters against macroeconomic UK labor supply, ASHE earnings, and Adzuna job postings data.

This project identifies skills gaps, succession/retirement risks, and internal-to-market salary disparities across key UK shortage sectors (Technology, Green Energy, and Healthcare).

---

## Technical Stack & Architecture

- **Language**: Python 3.10+ (Type annotated, PEP 8 structured, centralized logging)
- **Data Ingestion**: Polars & HTTPX (for performant structured file operations and API calls)
- **Text Mining**: Scikit-Learn TF-IDF vectorization (extracting skills requirements from unstructured job descriptions)
- **Analytical Storage**: DuckDB (for locally staging data and generating complex reporting views)
- **Enterprise DB Integration**: SQLite (for offline reporting) and Oracle DDL/DML compilation (for LiveSQL schema generation)
- **Visualization**: Power BI Star Schema representation

---

## Directory Structure

```text
├── data/
│   ├── raw/                      # Ingested datasets (synthetic HR roster, ONS ASHE, ONS supply, vacancy indexes)
│   └── processed/
│       ├── powerbi/              # Processed Star Schema CSV files for Power BI model ingestion
│       ├── workforce_intelligence.db      # Compiled DuckDB database
│       └── workforce_intelligence.sqlite  # Compiled SQLite database
├── powerbi/                      # Completed Power BI (.pbix) dashboard and PDF report
├── queries/                      # SQL query scripts (market demand, salary gaps, succession risk, skills mismatch)
├── reports/                      # Generated CSV reports, Oracle setup, Power BI guide, and Executive Briefing
├── scripts/                      # Modular Python processing components
│   ├── config.py                 # Centralized configuration mappings and taxonomies
│   ├── utils.py                  # Shared utilities (casing, TF-IDF skill parser, centralized logger)
│   ├── generate_synthetic_hr.py  # Produces synthetic corporate HR lists and JDs (fixed seed for reproducibility)
│   ├── fetch_nomis.py            # Acquires ONS ASHE, vacancy, and labor supply datasets
│   ├── fetch_adzuna.py           # Contacts Adzuna API (or falls back to seeded mock job postings generation)
│   ├── process_data.py           # Loads staged files to DuckDB and compiles analytical views
│   ├── generate_oracle_setup.py  # Generates Oracle LiveSQL setup DDL/DML script and downsamples vacancy data
│   ├── generate_sqlite.py        # Compiles SQLite database tables from processed CSV outputs
│   └── verify_db.py              # Executes diagnostic assertions against analytical views
├── requirements.txt              # Standard package requirements (Polars, DuckDB, Pandas, Scikit-Learn, HTTPX, xlsxwriter)
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

