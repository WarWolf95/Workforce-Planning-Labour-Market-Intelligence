"""
Processes raw datasets using SQLite and builds analytical views 
for reporting and visualization in Power BI.
"""

from pathlib import Path
import pandas as pd
import sqlite3

from config import SKILLS_VOCABULARY, ROLE_TEMPLATES, CORPORATE_ROLES
from utils import setup_logging, extract_skills_from_jds

# Configure logger
logger = setup_logging("process_data")

# Path definitions
WORKSPACE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = WORKSPACE_DIR / "data" / "raw"
PROCESSED_DIR = WORKSPACE_DIR / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = PROCESSED_DIR / "workforce_intelligence.sqlite"

def load_data_to_sqlite(extracted_skills: list) -> None:
    """
    Initializes SQLite database and loads raw CSV datasets into stage tables,
    then builds analytical views.
    """
    logger.info(f"Connecting to SQLite database at: {DB_PATH}")
    con = sqlite3.connect(str(DB_PATH))
    
    # 1. Load staging tables from raw CSVs
    logger.info("Loading datasets into SQLite staging tables...")
    
    # Internal workforce
    workforce_csv = RAW_DIR / "internal_workforce.csv"
    pd.read_csv(workforce_csv).to_sql("stg_internal_workforce", con, if_exists="replace", index=False)
    
    # ONS salaries
    ashe_csv = RAW_DIR / "ons_ashe_salaries.csv"
    pd.read_csv(ashe_csv).to_sql("stg_ons_ashe", con, if_exists="replace", index=False)
    
    # ONS vacancies
    vacancies_csv = RAW_DIR / "ons_vacancies.csv"
    pd.read_csv(vacancies_csv).to_sql("stg_ons_vacancies", con, if_exists="replace", index=False)
    
    # ONS labor supply
    supply_csv = RAW_DIR / "ons_labor_supply.csv"
    pd.read_csv(supply_csv).to_sql("stg_ons_labor_supply", con, if_exists="replace", index=False)
    
    # Adzuna vacancies
    adzuna_csv = RAW_DIR / "adzuna_vacancies.csv"
    pd.read_csv(adzuna_csv).to_sql("stg_adzuna_vacancies", con, if_exists="replace", index=False)
    
    # Extracted JD skills (load from list of dicts)
    extracted_df = pd.DataFrame(extracted_skills)
    jd_skills_csv = RAW_DIR / "extracted_jd_skills.csv"
    extracted_df.to_csv(jd_skills_csv, index=False)
    extracted_df.to_sql("stg_extracted_skills", con, if_exists="replace", index=False)
    
    # 2. Build Analytical Views for Reporting
    logger.info("Building analytical views for Workforce Intelligence briefing...")
    
    # View 1: Regional Salary Gap Analysis
    con.execute("DROP VIEW IF EXISTS v_salary_gap_analysis;")
    con.execute("""
    CREATE VIEW v_salary_gap_analysis AS
    with internal_summary as (
        select 
            soc_code,
            job_title,
            region,
            count(*) as employee_count,
            round(avg(salary), 0) as avg_internal_salary
        from stg_internal_workforce
        group by 1, 2, 3
    )
    select 
        i.soc_code,
        i.job_title,
        a.category,
        i.region,
        i.employee_count,
        i.avg_internal_salary,
        a.median_salary as ons_median_salary,
        i.avg_internal_salary - a.median_salary as salary_difference,
        round(((i.avg_internal_salary - a.median_salary) / a.median_salary) * 100, 1) as salary_gap_percentage
    from internal_summary i
    join stg_ons_ashe a 
      on cast(i.soc_code as text) = cast(a.soc_code as text) 
     and i.region = a.region;
    """)
    
    # View 2: Succession Risk Scoring
    con.execute("DROP VIEW IF EXISTS v_succession_risk_scoring;")
    con.execute("""
    CREATE VIEW v_succession_risk_scoring AS
    with role_demographics as (
        select 
            soc_code,
            job_title,
            count(*) as total_employees,
            sum(case when age >= 55 then 1 else 0 end) as age_55_plus_count,
            round(sum(case when age >= 55 then 1 else 0 end) * 100.0 / count(*), 1) as pct_retirement_risk_5yr,
            sum(case when succession_readiness = 'No Successor' and age >= 50 then 1 else 0 end) as critical_no_successor_count
        from stg_internal_workforce
        group by 1, 2
    ),
    market_comp as (
        select 
            cast(soc_code as text) as soc_code,
            sum(vacancies_2024) as national_vacancies_2024,
            avg(growth_rate) as market_growth_rate
        from stg_ons_vacancies
        where region = 'United Kingdom'
        group by 1
    )
    select 
        d.soc_code,
        d.job_title,
        d.total_employees,
        d.age_55_plus_count,
        d.pct_retirement_risk_5yr,
        d.critical_no_successor_count,
        m.national_vacancies_2024,
        round(m.market_growth_rate * 100, 1) as vacancy_growth_pct,
        -- Composite Risk Score: (Retirement Risk % * 0.4) + (Lack of Successor % * 0.4) + (Market Vacancies Factor * 0.2)
        round(
            (d.pct_retirement_risk_5yr * 0.4) + 
            ((d.critical_no_successor_count * 100.0 / case when d.total_employees = 0 then 1 else d.total_employees end) * 0.4) + 
            (min(m.national_vacancies_2024 / 150.0, 100.0) * 0.2), 
            1
        ) as composite_risk_score
    from role_demographics d
    left join market_comp m on cast(d.soc_code as text) = cast(m.soc_code as text);
    """)
    
    # Verify contents
    logger.info("Database load verification counts:")
    for table in ["stg_internal_workforce", "stg_ons_ashe", "stg_ons_vacancies", "stg_ons_labor_supply", "stg_adzuna_vacancies", "stg_extracted_skills"]:
        cnt = con.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        logger.info(f"- {table}: {cnt} records")
        
    con.close()
    logger.info("SQLite staging database compilation complete.")

def export_star_schema() -> None:
    """Exports clean dimensional Star Schema CSV files for Power BI and SQLite ingestion."""
    logger.info("Exporting Star Schema CSVs for Power BI...")
    pbi_dir = PROCESSED_DIR / "powerbi"
    pbi_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Load raw dataframes
    df_workforce = pd.read_csv(RAW_DIR / "internal_workforce.csv")
    df_ashe = pd.read_csv(RAW_DIR / "ons_ashe_salaries.csv")
    df_vacancies = pd.read_csv(RAW_DIR / "adzuna_vacancies.csv")
    df_supply = pd.read_csv(RAW_DIR / "ons_labor_supply.csv")
    df_skills = pd.read_csv(RAW_DIR / "extracted_jd_skills.csv")
    
    # 2. Build dim_soc_taxonomy
    soc_records = []
    for soc, template in ROLE_TEMPLATES.items():
        cat = "Tech" if soc.startswith("213") or soc == "3131" else ("Green Energy" if soc.startswith("212") or soc in ["3112", "8124"] else "Healthcare")
        soc_records.append({
            "soc_code": str(soc),
            "soc_title": template["title"],
            "category": cat
        })
    for r in CORPORATE_ROLES:
        soc_records.append({
            "soc_code": str(r["soc"]),
            "soc_title": r["title"],
            "category": "Corporate"
        })
    df_soc = pd.DataFrame(soc_records)
    
    # 3. Build dim_regions
    regions_list = ["London", "South East", "West Midlands", "North West", "Scotland", "Wales", "East of England", "South West", "United Kingdom"]
    regions_records = [{"region": r, "country": "Scotland" if r == "Scotland" else ("Wales" if r == "Wales" else "England")} for r in regions_list]
    df_regions = pd.DataFrame(regions_records)
    
    # 4. Save tables to powerbi directory
    df_soc.to_csv(pbi_dir / "dim_soc_taxonomy.csv", index=False)
    df_ashe.to_csv(pbi_dir / "dim_ashe_salary.csv", index=False)
    df_supply.to_csv(pbi_dir / "dim_labor_supply.csv", index=False)
    df_skills.to_csv(pbi_dir / "dim_extracted_skills.csv", index=False)
    df_workforce.to_csv(pbi_dir / "fact_employees.csv", index=False)
    df_vacancies.to_csv(pbi_dir / "fact_market_vacancies.csv", index=False)
    df_regions.to_csv(pbi_dir / "dim_regions.csv", index=False)
    
    logger.info(f"Power BI Star Schema CSVs exported successfully to: {pbi_dir}")

def load_star_schema_to_sqlite() -> None:
    """Loads compiled Power BI Star Schema CSVs into final SQLite tables (retiring generate_sqlite.py)."""
    logger.info("Loading Star Schema CSVs into final SQLite tables...")
    pbi_dir = PROCESSED_DIR / "powerbi"
    
    tables = {
        "dim_soc_taxonomy": "dim_soc_taxonomy.csv",
        "dim_ashe_salary": "dim_ashe_salary.csv",
        "dim_labor_supply": "dim_labor_supply.csv",
        "dim_extracted_skills": "dim_extracted_skills.csv",
        "dim_regions": "dim_regions.csv",
        "fact_employees": "fact_employees.csv",
        "fact_market_vacancies": "fact_market_vacancies.csv"
    }
    
    conn = sqlite3.connect(str(DB_PATH))
    for table_name, csv_filename in tables.items():
        csv_path = pbi_dir / csv_filename
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            logger.info(f"Loaded {csv_filename} into table '{table_name}'")
    conn.close()
    logger.info("SQLite database final tables compiled successfully.")

def main() -> None:
    logger.info("=========================================")
    logger.info("STARTING DATA PROCESSING & SQLITE LOAD")
    logger.info("=========================================")
    
    jd_json_path = RAW_DIR / "internal_job_descriptions.json"
    extracted_skills = extract_skills_from_jds(jd_json_path, SKILLS_VOCABULARY)
    load_data_to_sqlite(extracted_skills)
    
    # Export Star Schema CSVs for SQLite/Power BI
    export_star_schema()
    
    # Load Star Schema CSVs into SQLite database (retiring generate_sqlite logic)
    load_star_schema_to_sqlite()
    
    logger.info("=========================================")
    logger.info("DATA PROCESSING COMPLETED SUCCESSFULLY")
    logger.info("=========================================")

if __name__ == "__main__":
    main()
