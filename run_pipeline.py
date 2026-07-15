"""
End-to-End Orchestrator Pipeline for Workforce Planning & Labour Market Intelligence.
Runs synthetic data generation, data ingestion, database loading, SQLite compilation,
Oracle script compilation, database integrity checks, and refreshes the report CSVs.
"""

import sys
import sqlite3
from pathlib import Path
import pandas as pd

# Add the scripts folder to the system path to load local modules
SCRIPTS_DIR = Path(__file__).resolve().parent / "scripts"
sys.path.append(str(SCRIPTS_DIR))

# Import main functions from our modular pipeline components
import generate_synthetic_hr
import fetch_nomis
import fetch_adzuna
import process_data
import generate_sqlite
import verify_db
import generate_docx_case_study

from utils import setup_logging

logger = setup_logging("run_pipeline")

WORKSPACE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = WORKSPACE_DIR / "reports"
QUERIES_DIR = WORKSPACE_DIR / "queries"
DB_PATH = WORKSPACE_DIR / "data" / "processed" / "workforce_intelligence.sqlite"

def execute_queries_and_export_reports() -> None:
    """
    Executes the analytical SQL queries in queries/ against the compiled SQLite database
    and refreshes the corresponding CSV files in reports/ folder.
    """
    logger.info("Executing analytical queries and exporting reports...")
    
    if not DB_PATH.exists():
        logger.error(f"SQLite database not found at {DB_PATH}. Cannot export reports.")
        return
        
    conn = sqlite3.connect(str(DB_PATH))
    
    queries_map = {
        "market_vacancy_demand.sql": "Market Vacancy Demand.csv",
        "salary_gap_analysis.sql": "Salary Gap Analysis.csv",
        "skills_mismatch_analysis.sql": "Skills Mismatch Analysis.csv",
        "skills_gap_analysis.sql": "Detailed Skills Gap Analysis.csv",
        "succession_risk_scoring.sql": "Succession & Retirement Risk Scoring.csv"
    }
    
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    for sql_file, csv_file in queries_map.items():
        sql_path = QUERIES_DIR / sql_file
        csv_path = REPORTS_DIR / csv_file
        
        if not sql_path.exists():
            logger.warning(f"SQL query file not found at {sql_path}. Skipping.")
            continue
            
        logger.info(f"Running query {sql_file} and saving to {csv_file}...")
        
        with open(sql_path, "r", encoding="utf-8") as f:
            query_sql = f.read()
            
        df = pd.read_sql_query(query_sql, conn)
        df.to_csv(csv_path, index=False)
        logger.info(f"Successfully exported {len(df)} records to {csv_path}.")
        
    conn.close()
    logger.info("Reports export completed successfully.")

def main() -> None:
    logger.info("=========================================")
    logger.info("STARTING WORKFORCE PLANNING PIPELINE RUN")
    logger.info("=========================================")
    
    try:
        # Step 1: Generate internal workforce & job descriptions
        generate_synthetic_hr.main()
        
        # Step 2: Fetch and build ONS NOMIS-aligned tables
        fetch_nomis.main()
        
        # Step 3: Fetch and build Adzuna vacancy listings
        fetch_adzuna.main()
        
        # Step 4: Process staging data into DuckDB, create analytical views, and export Power BI Star Schema CSVs
        process_data.main()
        
        # Step 5: Load Star Schema CSVs into SQLite database
        generate_sqlite.main()
        
        # Step 7: Verify database integrity in DuckDB
        verify_db.main()
        
        # Step 8: Execute SQL queries and refresh CSV outputs under reports/
        execute_queries_and_export_reports()
        
        # Step 9: Rebuild Word Document Case Study
        generate_docx_case_study.main()
        
        logger.info("=========================================")
        logger.info("WORKFORCE PLANNING PIPELINE RUN COMPLETED")
        logger.info("=========================================")
        
    except Exception as e:
        logger.critical(f"Pipeline execution failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
