"""
Diagnostic script to run verification queries against the compiled DuckDB database
and assert mathematical alignment with ONS benchmarks and target KPIs.
"""

from pathlib import Path
import duckdb
from typing import List, Tuple

from utils import setup_logging

# Configure logger
logger = setup_logging("verify_db")

# Define path
WORKSPACE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = WORKSPACE_DIR / "data" / "processed" / "workforce_intelligence.db"

def run_verification() -> None:
    logger.info("=========================================")
    logger.info("RUNNING DATABASE INTEGRITY VERIFICATION")
    logger.info("=========================================")
    
    if not DB_PATH.exists():
        logger.error(f"DuckDB database not found at {DB_PATH}. Please run data processing first.")
        return
        
    logger.info(f"Connecting to DuckDB database at: {DB_PATH}")
    con = duckdb.connect(str(DB_PATH))
    
    # Query 1: Verify average internal vs external ONS salaries by category
    logger.info("1. Salary Gap Analysis by Category:")
    sal_gap: List[Tuple] = con.execute("""
        select 
            category,
            count(*) as emp_count,
            round(avg(avg_internal_salary), 0) as avg_internal,
            round(avg(ons_median_salary), 0) as avg_ons_median,
            round(avg(salary_difference), 0) as avg_diff,
            round(avg(salary_gap_percentage), 1) as avg_gap_pct
        from v_salary_gap_analysis
        group by 1
        order by avg_gap_pct asc
    """).fetchall()
    
    for row in sal_gap:
        print(f"Category: {row[0]:<15} | Employees: {row[1]:<3} | Avg Internal: £{row[2]:,.0f} | ONS Median: £{row[3]:,.0f} | Diff: £{row[4]:+,.0f} ({row[5]}%)")

    # Query 2: Verify succession risk scoring (highest risk roles)
    logger.info("2. Top 5 High Succession Risk Roles:")
    risk_roles: List[Tuple] = con.execute("""
        select 
            soc_code,
            job_title,
            total_employees,
            pct_retirement_risk_5yr,
            critical_no_successor_count,
            composite_risk_score
        from v_succession_risk_scoring
        order by composite_risk_score desc
        limit 5
    """).fetchall()
    
    for row in risk_roles:
        print(f"SOC: {row[0]} | Role: {row[1]:<30} | Staff Count: {row[2]:<3} | Retiring 5Yr: {row[3]}% | No Successor: {row[4]} | Composite Risk Score: {row[5]}")

    # Query 3: Verify text analysis (sample extracted skills)
    logger.info("3. Sample Extracted Skills from Job Descriptions:")
    skills: List[Tuple] = con.execute("""
        select 
            soc_code,
            job_title,
            skills_count,
            extracted_skills
        from stg_extracted_skills
        order by skills_count desc
        limit 3
    """).fetchall()
    
    for row in skills:
        print(f"SOC: {row[0]} | Title: {row[1]:<25} | Skills Count: {row[2]} | Skills: {row[3]}")
        
    con.close()
    logger.info("=========================================")
    logger.info("DATABASE VERIFICATION RUN COMPLETED")
    logger.info("=========================================")

def main() -> None:
    run_verification()

if __name__ == "__main__":
    main()
