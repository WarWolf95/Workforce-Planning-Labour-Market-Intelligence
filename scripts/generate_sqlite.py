"""
Compiles local SQLite database from processed Power BI Star Schema CSVs
for local testing and offline query verification.
"""

from pathlib import Path
import sqlite3
import pandas as pd
from typing import Dict

from utils import setup_logging

# Configure logger
logger = setup_logging("generate_sqlite")

# Define paths
WORKSPACE_DIR = Path(__file__).resolve().parents[1]
PROCESSED_DIR = WORKSPACE_DIR / "data" / "processed"
PBI_DIR = PROCESSED_DIR / "powerbi"
DB_PATH = PROCESSED_DIR / "workforce_intelligence.sqlite"

def compile_sqlite_db() -> None:
    logger.info("=========================================")
    logger.info("STARTING LOCAL SQLITE DATABASE COMPILATION")
    logger.info("=========================================")
    
    logger.info(f"Connecting to SQLite database at: {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))
    
    # Tables to load from our clean Star Schema CSV files
    tables: Dict[str, str] = {
        "dim_soc_taxonomy": "dim_soc_taxonomy.csv",
        "dim_ashe_salary": "dim_ashe_salary.csv",
        "dim_labor_supply": "dim_labor_supply.csv",
        "dim_extracted_skills": "dim_extracted_skills.csv",
        "dim_regions": "dim_regions.csv",
        "fact_employees": "fact_employees.csv",
        "fact_market_vacancies": "fact_market_vacancies.csv"
    }
    
    for table_name, csv_filename in tables.items():
        csv_path = PBI_DIR / csv_filename
        if not csv_path.exists():
            logger.warning(f"CSV file not found at {csv_path}. Skipping.")
            continue
            
        logger.info(f"Loading {csv_filename} into table '{table_name}'...")
        # Read CSV using Pandas
        df = pd.read_csv(csv_path)
        
        # Write to SQLite
        df.to_sql(table_name, conn, index=False, if_exists="replace")
        
    conn.close()
    logger.info("=========================================")
    logger.info("LOCAL SQLITE DATABASE COMPILED SUCCESSFULLY")
    logger.info("=========================================")

def main() -> None:
    compile_sqlite_db()

if __name__ == "__main__":
    main()
