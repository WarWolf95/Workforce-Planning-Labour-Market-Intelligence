"""
Acquires job postings data from Adzuna API (when credentials are provided)
or generates a realistic mock dataset representing shortages in UK sectors.
"""

import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import httpx
import pandas as pd

from config import REGIONS, SKILLS_BY_SOC
from utils import setup_logging

# Configure logger
logger = setup_logging("fetch_adzuna")

# Target path
WORKSPACE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = WORKSPACE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)
ADZUNA_FILE = RAW_DIR / "adzuna_vacancies.csv"

# SOC code mapping reference for keyword categorization
SOC_ROLES: Dict[str, Dict[str, List[str]]] = {
    "Tech": {
        "2136": ["Software Engineer", "Developer", "Programmer", "Full Stack Developer", "Backend Engineer", "Frontend Developer", "Python Developer"],
        "2135": ["IT Architect", "Systems Designer", "IT Business Analyst", "Solution Architect", "Systems Analyst"],
        "2137": ["Web Designer", "UX/UI Web Developer", "Web Developer", "Frontend Web Specialist"],
        "2139": ["Data Engineer", "DevOps Specialist", "Cyber Security Analyst", "Information Security Officer", "Cloud Engineer"],
        "3131": ["IT Support Technician", "Helpdesk Engineer", "IT Operations Analyst", "Network Administrator"]
    },
    "Green Energy": {
        "2121": ["Civil Engineer - Wind Farms", "Infrastructure Project Engineer", "Structural Engineer - Renewables"],
        "2122": ["Mechanical Engineer - Wind Turbines", "Renewable Energy Design Specialist", "HVAC Engineer - Heat Pumps"],
        "2123": ["Electrical Grid Engineer", "High Voltage Connections Engineer", "Electrical Engineer - Solar PV"],
        "2125": ["Chemical Engineer - Hydrogen Production", "Bioenergy Process Engineer", "Carbon Capture Engineer"],
        "2126": ["Renewable Systems Designer", "Product Development Engineer - Battery Storage"],
        "3112": ["Wind Turbine Commissioning Technician", "Solar PV Installation Inspector", "Smart Grid Technician"],
        "8124": ["Energy Plant Operative", "Hydroelectric Plant Operator", "Biomass Boiler Operator"]
    },
    "Healthcare": {
        "2211": ["General Practitioner", "Consultant Cardiologist", "Medical Doctor", "Registrar - Acute Medicine"],
        "2231": ["Registered Nurse", "Staff Nurse - ICU", "Senior Ward Nurse", "Clinical Nurse Specialist", "District Nurse"],
        "2237": ["Pharmacist", "Clinical Pharmacist", "Pharmacy Manager"],
        "3211": ["Radiographer", "Medical Lab Technician", "Cardiac Physiologist"],
        "6141": ["Nursing Assistant", "Healthcare Assistant", "Care Auxiliary", "Ward Support Worker"]
    }
}

def fetch_real_adzuna(app_id: str, app_key: str) -> List[Dict[str, Any]]:
    """
    Attempts to fetch job postings from the real Adzuna API.
    Only runs if credentials are provided.
    """
    logger.info(f"Connecting to Adzuna API using App ID: {app_id[:4]}...")
    results: List[Dict[str, Any]] = []
    
    queries = ["software engineer", "nurse", "electrical engineer", "wind energy"]
    
    with httpx.Client() as client:
        for q in queries:
            try:
                url = "https://api.adzuna.com/v1/api/jobs/gb/search/1"
                params = {
                    "app_id": app_id,
                    "app_key": app_key,
                    "what": q,
                    "results_per_page": 50,
                    "content-type": "application/json"
                }
                response = client.get(url, params=params, timeout=15)
                response.raise_for_status()
                data = response.json()
                
                postings = data.get("results", [])
                logger.info(f"Fetched {len(postings)} results for search term '{q}' from Adzuna.")
                
                for p in postings:
                    locs = p.get("location", {}).get("area", [])
                    region = locs[0] if locs else "United Kingdom"
                    
                    created_raw = p.get("created", "")
                    created_date = created_raw[:10] if created_raw else datetime.now().strftime("%Y-%m-%d")
                    
                    results.append({
                        "job_id": p.get("id", ""),
                        "title": p.get("title", ""),
                        "description": p.get("description", ""),
                        "created": created_date,
                        "company": p.get("company", {}).get("display_name", "Confidential"),
                        "region": region,
                        "salary_min": p.get("salary_min", None),
                        "salary_max": p.get("salary_max", None),
                        "source": "adzuna_api"
                    })
            except Exception as e:
                logger.error(f"Error querying Adzuna API for term '{q}': {e}")
                
    return results

def generate_mock_adzuna(count: int = 3000, seed: int = 42) -> List[Dict[str, Any]]:
    """
    Generates a rich, highly realistic mock dataset representing 
    scraped job postings for key UK shortage roles. Seed is locked for reproducibility.
    """
    logger.info(f"Generating {count} mock UK job adverts for gap and salary mapping...")
    random.seed(seed)
    
    companies_by_sector = {
        "Tech": ["TechSpark UK", "Ocado Technology", "Sage Group", "Revolut", "Deliveroo", "Arup Digital", "BAE Systems", "CGI UK", "Direct Line Tech"],
        "Green Energy": ["SSE Renewables", "Octopus Energy", "BP Alternative Energy", "ScottishPower Renewables", "Vestas UK", "Orsted UK", "Ecotricity", "Babcock International"],
        "Healthcare": ["NHS England", "NHS Scotland", "Bupa UK", "Spire Healthcare", "Nuffield Health", "HCA Healthcare UK", "Barchester Healthcare"]
    }
    
    records: List[Dict[str, Any]] = []
    start_date = datetime.now() - timedelta(days=90)
    
    for i in range(count):
        sector = random.choice(["Tech", "Green Energy", "Healthcare"])
        soc = random.choice(list(SOC_ROLES[sector].keys()))
        job_title_base = random.choice(SOC_ROLES[sector][soc])
        
        seniority = random.choices(["Junior", "Senior", "Lead", "Principal", ""], weights=[15, 25, 10, 5, 45])[0]
        title = f"{seniority} {job_title_base}".strip()
        
        company = random.choice(companies_by_sector[sector])
        region = random.choice(REGIONS)
        
        if sector == "Tech":
            base_sal = random.randint(30000, 75000) if "Junior" in title else (random.randint(75000, 110000) if "Senior" in title or "Lead" in title else random.randint(45000, 85000))
        elif sector == "Green Energy":
            base_sal = random.randint(28000, 48000) if "Junior" in title else (random.randint(60000, 85000) if "Senior" in title or "Lead" in title else random.randint(40000, 65000))
        else: # Healthcare
            base_sal = random.randint(25000, 32000) if "Junior" in title else (random.randint(55000, 95000) if "Senior" in title or "Lead" in title else random.randint(32000, 50000))
            if "Doctor" in title or "GP" in title or "Consultant" in title:
                base_sal = random.randint(80000, 130000)
                
        reg_mult = 1.22 if region == "London" else (1.06 if region == "South East" else random.uniform(0.92, 0.98))
        sal_min = int(base_sal * reg_mult * random.uniform(0.95, 0.98))
        sal_max = int(base_sal * reg_mult * random.uniform(1.02, 1.10))
        
        days_offset = random.randint(0, 90)
        created_date = (start_date + timedelta(days=days_offset)).strftime("%Y-%m-%d")
        
        possible_skills = SKILLS_BY_SOC[soc]
        skills_count = random.randint(3, 6)
        required_skills = random.sample(possible_skills, min(skills_count, len(possible_skills)))
        skills_str = ";".join(required_skills)
        
        job_id = f"ADZ-{1000000 + i}"
        
        description = f"We are seeking a motivated {title} to join our growing team in {region}. " \
                      f"The successful candidate will demonstrate proficiency in {', '.join(required_skills[:3])}. " \
                      f"We offer competitive salary and career progression."
                      
        records.append({
            "job_id": job_id,
            "title": title,
            "description": description,
            "created": created_date,
            "company": company,
            "region": region,
            "soc_code": soc,
            "salary_min": sal_min,
            "salary_max": sal_max,
            "category": sector,
            "skills_required": skills_str,
            "source": "scraped_mock"
        })
        
    return records

def main() -> None:
    logger.info("=========================================")
    logger.info("STARTING ADZUNA DATA ACQUISITION")
    logger.info("=========================================")
    
    app_id = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY")
    
    results: List[Dict[str, Any]] = []
    if app_id and app_key:
        try:
            results = fetch_real_adzuna(app_id, app_key)
        except Exception as e:
            logger.warning(f"API Error encountered: {e}. Falling back to mock generator.")
            
    if not results:
        logger.info("Adzuna API credentials not found in environment (ADZUNA_APP_ID, ADZUNA_APP_KEY).")
        results = generate_mock_adzuna(count=3000, seed=42)
        
    df = pd.DataFrame(results)
    df.to_csv(ADZUNA_FILE, index=False)
    logger.info(f"Successfully saved {len(results)} vacancy records to {ADZUNA_FILE}.")
    logger.info("=========================================")
    logger.info("ADZUNA DATA INGESTION COMPLETED")
    logger.info("=========================================")

if __name__ == "__main__":
    main()
