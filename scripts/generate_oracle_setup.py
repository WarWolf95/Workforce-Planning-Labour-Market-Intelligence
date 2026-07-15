"""
Generates the Oracle LiveSQL DDL/DML setup scripts and exports the Star Schema
CSVs for Power BI modeling.
"""

from pathlib import Path
import pandas as pd
from typing import Dict, Any, List

from config import ROLE_TEMPLATES, CORPORATE_ROLES, SKILLS_VOCABULARY
from utils import setup_logging, extract_skills_from_jds

# Configure logger
logger = setup_logging("generate_oracle_setup")

# Path definitions
WORKSPACE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = WORKSPACE_DIR / "data" / "raw"
PBI_DIR = WORKSPACE_DIR / "data" / "processed" / "powerbi"
PBI_DIR.mkdir(parents=True, exist_ok=True)

REPORTS_DIR = WORKSPACE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_SQL_FILE = REPORTS_DIR / "oracle_schema_setup.sql"

def sql_escape(val: Any) -> str:
    """Escapes string quotes and handles nulls for SQL inserts."""
    if pd.isna(val) or val is None:
        return "NULL"
    # Convert numbers to string directly
    if isinstance(val, (int, float)):
        return str(val)
    # Convert string and escape single quotes for Oracle SQL
    s = str(val).replace("'", "''")
    return f"'{s}'"

def sql_date(val: Any) -> str:
    """Formats dates for Oracle TO_DATE function."""
    if pd.isna(val) or val is None:
        return "NULL"
    s = str(val)[:10]  # Take YYYY-MM-DD
    return f"TO_DATE('{s}', 'YYYY-MM-DD')"

def compile_oracle_script(
    df_workforce: pd.DataFrame,
    df_ashe: pd.DataFrame,
    df_vacancies: pd.DataFrame,
    df_supply: pd.DataFrame,
    df_skills: pd.DataFrame
) -> None:
    """
    Compiles schemas, constraints, DDL and DML insert queries into reports/oracle_schema_setup.sql.
    Also downsamples vacancies to 600 records to align with LiveSQL limits.
    """
    logger.info(f"Compiling Oracle schema script to {OUTPUT_SQL_FILE}...")
    
    # Downsample vacancies (keep ONS macro trends, but downsample raw postings to 600)
    df_adzuna = df_vacancies[df_vacancies["source"] == "scraped_mock"]
    df_adzuna_sample = df_adzuna.sample(n=600, random_state=42)
    df_adzuna_sample = df_adzuna_sample.reset_index(drop=True)
    
    # Standard SOC taxonomy table from TARGET_SOCS (de-duplicated)
    soc_records = []
    for soc, template in ROLE_TEMPLATES.items():
        cat = "Tech" if soc.startswith("213") or soc == "3131" else ("Green Energy" if soc.startswith("212") or soc in ["3112", "8124"] else "Healthcare")
        soc_records.append({
            "soc_code": soc,
            "soc_title": template["title"],
            "category": cat
        })
    for r in CORPORATE_ROLES:
        soc_records.append({
            "soc_code": r["soc"],
            "soc_title": r["title"],
            "category": "Corporate"
        })
    df_soc = pd.DataFrame(soc_records)
    
    with open(OUTPUT_SQL_FILE, "w", encoding="utf-8") as f:
        # Header comments
        f.write("-- ========================================================\n")
        f.write("-- ORACLE LIVESQL SCHEMA SETUP FOR WORKFORCE INTELLIGENCE\n")
        f.write(f"-- Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("-- Instructions: Copy-paste the entire script or upload it in \n")
        f.write("--               the 'My Scripts' section of Oracle Live SQL.\n")
        f.write("-- ========================================================\n\n")
        
        # 1. DROP TABLES (for clean re-runs)
        f.write("-- 1. Cleanup existing tables\n")
        for table in ["fact_employees", "fact_market_vacancies", "dim_ashe_salary", "dim_labor_supply", "dim_extracted_skills", "dim_soc_taxonomy"]:
            f.write(f"BEGIN EXECUTE IMMEDIATE 'DROP TABLE {table} CASCADE CONSTRAINTS'; EXCEPTION WHEN OTHERS THEN NULL; END;\n/\n")
        f.write("\n")
        
        # 2. CREATE TABLES (DDL)
        f.write("-- 2. DDL - Create tables with Oracle-compliant datatypes\n\n")
        
        # SOC Taxonomy
        f.write("CREATE TABLE dim_soc_taxonomy (\n")
        f.write("    soc_code VARCHAR2(10) PRIMARY KEY,\n")
        f.write("    soc_title VARCHAR2(150) NOT NULL,\n")
        f.write("    category VARCHAR2(50) NOT NULL\n")
        f.write(");\n\n")
        
        # ASHE salaries
        f.write("CREATE TABLE dim_ashe_salary (\n")
        f.write("    soc_code VARCHAR2(10) NOT NULL,\n")
        f.write("    soc_title VARCHAR2(150),\n")
        f.write("    category VARCHAR2(50),\n")
        f.write("    region VARCHAR2(50) NOT NULL,\n")
        f.write("    median_salary NUMBER(10),\n")
        f.write("    mean_salary NUMBER(10),\n")
        f.write("    hourly_median NUMBER(6,2),\n")
        f.write("    CONSTRAINT pk_dim_ashe PRIMARY KEY (soc_code, region)\n")
        f.write(");\n\n")
        
        # Labor supply
        f.write("CREATE TABLE dim_labor_supply (\n")
        f.write("    soc_code VARCHAR2(10) NOT NULL,\n")
        f.write("    soc_title VARCHAR2(150),\n")
        f.write("    category VARCHAR2(50),\n")
        f.write("    region VARCHAR2(50) NOT NULL,\n")
        f.write("    employed_count NUMBER(10),\n")
        f.write("    unemployed_count NUMBER(10),\n")
        f.write("    retirement_risk_rate NUMBER(5,3),\n")
        f.write("    annual_grad_supply NUMBER(10),\n")
        f.write("    CONSTRAINT pk_dim_supply PRIMARY KEY (soc_code, region)\n")
        f.write(");\n\n")
        
        # Extracted Skills
        f.write("CREATE TABLE dim_extracted_skills (\n")
        f.write("    job_title VARCHAR2(100) NOT NULL,\n")
        f.write("    soc_code VARCHAR2(10) PRIMARY KEY,\n")
        f.write("    extracted_skills VARCHAR2(500),\n")
        f.write("    skills_count NUMBER(5)\n")
        f.write(");\n\n")
        
        # Employees Fact
        f.write("CREATE TABLE fact_employees (\n")
        f.write("    employee_id VARCHAR2(10) PRIMARY KEY,\n")
        f.write("    name VARCHAR2(100) NOT NULL,\n")
        f.write("    age NUMBER(3) NOT NULL,\n")
        f.write("    department VARCHAR2(50) NOT NULL,\n")
        f.write("    job_title VARCHAR2(100) NOT NULL,\n")
        f.write("    salary NUMBER(10) NOT NULL,\n")
        f.write("    region VARCHAR2(50) NOT NULL,\n")
        f.write("    soc_code VARCHAR2(10) NOT NULL,\n")
        f.write("    skills VARCHAR2(500),\n")
        f.write("    tenure_years NUMBER(4,1) NOT NULL,\n")
        f.write("    performance_rating NUMBER(1),\n")
        f.write("    retirement_risk VARCHAR2(10),\n")
        f.write("    succession_readiness VARCHAR2(50),\n")
        f.write("    CONSTRAINT fk_employees_soc FOREIGN KEY (soc_code) REFERENCES dim_soc_taxonomy(soc_code)\n")
        f.write(");\n\n")
        
        # Vacancies Fact
        f.write("CREATE TABLE fact_market_vacancies (\n")
        f.write("    job_id VARCHAR2(20) PRIMARY KEY,\n")
        f.write("    title VARCHAR2(150) NOT NULL,\n")
        f.write("    description VARCHAR2(500),\n")
        f.write("    created_date DATE,\n")
        f.write("    company VARCHAR2(100),\n")
        f.write("    region VARCHAR2(50) NOT NULL,\n")
        f.write("    soc_code VARCHAR2(10) NOT NULL,\n")
        f.write("    salary_min NUMBER(10),\n")
        f.write("    salary_max NUMBER(10),\n")
        f.write("    category VARCHAR2(50) NOT NULL,\n")
        f.write("    skills_required VARCHAR2(500),\n")
        f.write("    source VARCHAR2(20) NOT NULL,\n")
        f.write("    CONSTRAINT fk_vacancies_soc FOREIGN KEY (soc_code) REFERENCES dim_soc_taxonomy(soc_code)\n")
        f.write(");\n\n")
        
        # 3. POPULATE TABLES (DML)
        f.write("-- 3. DML - Populate tables\n\n")
        
        logger.info("Writing dim_soc_taxonomy DML...")
        f.write("-- Populating dim_soc_taxonomy\n")
        for idx, row in df_soc.iterrows():
            f.write(f"INSERT INTO dim_soc_taxonomy (soc_code, soc_title, category) VALUES (" \
                    f"{sql_escape(row['soc_code'])}, {sql_escape(row['soc_title'])}, {sql_escape(row['category'])});\n")
        f.write("COMMIT;\n\n")
        
        logger.info("Writing dim_ashe_salary DML...")
        f.write("-- Populating dim_ashe_salary\n")
        for idx, row in df_ashe.iterrows():
            f.write(f"INSERT INTO dim_ashe_salary (soc_code, soc_title, category, region, median_salary, mean_salary, hourly_median) VALUES (" \
                    f"{sql_escape(row['soc_code'])}, {sql_escape(row['soc_title'])}, {sql_escape(row['category'])}, {sql_escape(row['region'])}, " \
                    f"{sql_escape(row['median_salary'])}, {sql_escape(row['mean_salary'])}, {sql_escape(row['hourly_median'])});\n")
        f.write("COMMIT;\n\n")
        
        logger.info("Writing dim_labor_supply DML...")
        f.write("-- Populating dim_labor_supply\n")
        for idx, row in df_supply.iterrows():
            f.write(f"INSERT INTO dim_labor_supply (soc_code, soc_title, category, region, employed_count, unemployed_count, retirement_risk_rate, annual_grad_supply) VALUES (" \
                    f"{sql_escape(row['soc_code'])}, {sql_escape(row['soc_title'])}, {sql_escape(row['category'])}, {sql_escape(row['region'])}, " \
                    f"{sql_escape(row['employed_count'])}, {sql_escape(row['unemployed_count'])}, {sql_escape(row['retirement_risk_rate'])}, {sql_escape(row['annual_grad_supply'])});\n")
        f.write("COMMIT;\n\n")
        
        logger.info("Writing dim_extracted_skills DML...")
        f.write("-- Populating dim_extracted_skills\n")
        for idx, row in df_skills.iterrows():
            f.write(f"INSERT INTO dim_extracted_skills (job_title, soc_code, extracted_skills, skills_count) VALUES (" \
                    f"{sql_escape(row['job_title'])}, {sql_escape(row['soc_code'])}, {sql_escape(row['extracted_skills'])}, {sql_escape(row['skills_count'])});\n")
        f.write("COMMIT;\n\n")
        
        logger.info("Writing fact_employees DML...")
        f.write("-- Populating fact_employees\n")
        for idx, row in df_workforce.iterrows():
            f.write(f"INSERT INTO fact_employees (employee_id, name, age, department, job_title, salary, region, soc_code, skills, tenure_years, performance_rating, retirement_risk, succession_readiness) VALUES (" \
                    f"{sql_escape(row['employee_id'])}, {sql_escape(row['name'])}, {sql_escape(row['age'])}, {sql_escape(row['department'])}, " \
                    f"{sql_escape(row['job_title'])}, {sql_escape(row['salary'])}, {sql_escape(row['region'])}, {sql_escape(row['soc_code'])}, " \
                    f"{sql_escape(row['skills'])}, {sql_escape(row['tenure_years'])}, {sql_escape(row['performance_rating'])}, " \
                    f"{sql_escape(row['retirement_risk'])}, {sql_escape(row['succession_readiness'])});\n")
        f.write("COMMIT;\n\n")
        
        logger.info("Writing fact_market_vacancies DML...")
        f.write("-- Populating fact_market_vacancies (Sample of 600 records for LiveSQL compatibility)\n")
        for idx, row in df_adzuna_sample.iterrows():
            desc = str(row['description'])[:450] if not pd.isna(row['description']) else ""
            f.write(f"INSERT INTO fact_market_vacancies (job_id, title, description, created_date, company, region, soc_code, salary_min, salary_max, category, skills_required, source) VALUES (" \
                    f"{sql_escape(row['job_id'])}, {sql_escape(row['title'])}, {sql_escape(desc)}, {sql_date(row['created'])}, " \
                    f"{sql_escape(row['company'])}, {sql_escape(row['region'])}, {sql_escape(row['soc_code'])}, " \
                    f"{sql_escape(row['salary_min'])}, {sql_escape(row['salary_max'])}, {sql_escape(row['category'])}, " \
                    f"{sql_escape(row['skills_required'])}, {sql_escape(row['source'])});\n")
        f.write("COMMIT;\n\n")
        
    logger.info(f"Oracle LiveSQL script compiled: {OUTPUT_SQL_FILE}")
    
    # 4. EXPORT STAR SCHEMA FOR POWER BI (Full datasets, not downsampled)
    logger.info("Exporting Star Schema CSVs for Power BI...")
    
    # Save the processed tables into processed/powerbi folder
    df_soc.to_csv(PBI_DIR / "dim_soc_taxonomy.csv", index=False)
    df_ashe.to_csv(PBI_DIR / "dim_ashe_salary.csv", index=False)
    df_supply.to_csv(PBI_DIR / "dim_labor_supply.csv", index=False)
    df_skills.to_csv(PBI_DIR / "dim_extracted_skills.csv", index=False)
    df_workforce.to_csv(PBI_DIR / "fact_employees.csv", index=False)
    df_vacancies.to_csv(PBI_DIR / "fact_market_vacancies.csv", index=False)
    
    # Create simple dim_regions table
    regions_list = ["London", "South East", "West Midlands", "North West", "Scotland", "Wales", "East of England", "South West", "United Kingdom"]
    regions_records = [{"region": r, "country": "Scotland" if r == "Scotland" else ("Wales" if r == "Wales" else "England")} for r in regions_list]
    df_regions = pd.DataFrame(regions_records)
    df_regions.to_csv(PBI_DIR / "dim_regions.csv", index=False)
    
    logger.info(f"Power BI Star Schema CSVs exported successfully to: {PBI_DIR}")

def main() -> None:
    logger.info("=========================================")
    logger.info("STARTING ORACLE SCHEMA COMPILATION")
    logger.info("=========================================")
    
    logger.info("Loading raw CSV files using Pandas...")
    df_workforce = pd.read_csv(RAW_DIR / "internal_workforce.csv")
    df_ashe = pd.read_csv(RAW_DIR / "ons_ashe_salaries.csv")
    df_vacancies = pd.read_csv(RAW_DIR / "adzuna_vacancies.csv")
    df_supply = pd.read_csv(RAW_DIR / "ons_labor_supply.csv")
    
    # Perform JD text analysis using shared helper
    jd_json_path = RAW_DIR / "internal_job_descriptions.json"
    skills_list = extract_skills_from_jds(jd_json_path, SKILLS_VOCABULARY)
    df_skills = pd.DataFrame(skills_list)
    
    # Compile SQL file and Power BI files
    compile_oracle_script(df_workforce, df_ashe, df_vacancies, df_supply, df_skills)
    
    logger.info("=========================================")
    logger.info("ORACLE SCHEMA COMPILATION COMPLETE")
    logger.info("=========================================")

if __name__ == "__main__":
    main()
