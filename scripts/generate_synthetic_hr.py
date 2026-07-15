"""
Generates a realistic synthetic employee dataset and job descriptions
calibrated to typical UK regional distributions and organizational structures.
"""

import random
from pathlib import Path
import json
import pandas as pd
from typing import List, Dict, Any

from config import FIRST_NAMES, LAST_NAMES, DEPTS, ROLE_TEMPLATES, CORPORATE_ROLES
from utils import setup_logging

# Configure logger
logger = setup_logging("generate_synthetic_hr")

# Define target paths relative to workspace root
WORKSPACE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = WORKSPACE_DIR / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

WORKFORCE_FILE = RAW_DIR / "internal_workforce.csv"
JDS_FILE = RAW_DIR / "internal_job_descriptions.json"

def generate_workforce(count: int = 800) -> None:
    """
    Generates synthetic employee dataset.
    """
    logger.info(f"Generating synthetic employee dataset ({count} records)...")
    random.seed(42)  # Ensure reproducibility of the organization roster
    
    records: List[Dict[str, Any]] = []
    for i in range(count):
        emp_id = f"EMP-{i+1:04d}"
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        
        # Distribute employees across departments:
        # Digital: ~25%, Green Energy: ~35%, Clinical Ops: ~30%, Corporate: ~10%
        dept = random.choices(
            ["Digital Services", "Green Energy Projects", "Clinical Operations", "Corporate Services"],
            weights=[25, 35, 30, 10]
        )[0]
        
        # Assign role
        if dept == "Corporate Services":
            template = random.choice(CORPORATE_ROLES)
            title = template["title"]
            soc = template["soc"]
            base = template["base_salary"]
            skills_pool = template["skills"]
        else:
            soc = random.choice(DEPTS[dept])
            template = ROLE_TEMPLATES[soc]
            title = template["title"]
            base = template["base_salary"]
            skills_pool = template["skills"]
            
        # Age distribution: 
        # - Green Energy Projects & Clinical Operations should have a higher average age (high retirement risk)
        # - Digital Services should have a lower average age (low retirement risk, high turnover risk)
        if dept == "Green Energy Projects" or soc in ["2231", "6141"]:
            age = int(random.gauss(49, 9))  # Mean age 49
            age = max(20, min(67, age))
        elif dept == "Digital Services":
            age = int(random.gauss(33, 7))  # Mean age 33
            age = max(21, min(60, age))
        else:
            age = int(random.gauss(40, 10))  # Mean age 40
            age = max(18, min(65, age))
            
        # Tenure logic based on age
        tenure = round(max(0.5, min(age - 18, random.uniform(0.1, 0.4) * (age - 18))), 1)
        
        # Location distribution
        region = random.choices(
            ["London", "South East", "North West", "West Midlands", "Scotland", "Wales", "South West"],
            weights=[20, 25, 15, 15, 12, 5, 8]
        )[0]
        
        # Salary logic
        # - London pay weight
        loc_mult = 1.15 if region == "London" else (1.05 if region == "South East" else 0.98)
        # - Tenure adjustment (longer tenure = slightly higher salary)
        tenure_mult = 1.0 + (tenure * 0.015)
        # - Organizational structural salary lag in Tech (Digital Services)
        # We deliberately make our tech salaries lag ONS market values by ~12% to show salary risk!
        lag_mult = 0.88 if dept == "Digital Services" else 1.02
        
        salary = int(base * loc_mult * tenure_mult * lag_mult * random.uniform(0.96, 1.04))
        
        # Skills gaps logic: 
        # Employees typically possess 2 to 4 of their template skills. Some are missing critical modern skills.
        num_skills = random.randint(2, len(skills_pool))
        emp_skills = random.sample(skills_pool, num_skills)
        # Semicolon delimited
        skills_str = ";".join(emp_skills)
        
        # Performance Score (1-5)
        perf = random.choices([1, 2, 3, 4, 5], weights=[5, 10, 60, 20, 5])[0]
        
        # Succession Planning (mostly relevant for older/senior staff)
        # High retirement risk roles will lack successors to highlight succession gap modeling
        if age >= 58:
            ret_risk = "High"
            # Older employees in Green Energy (Operations) and Nursing are very likely to have NO successor
            if soc in ["8124", "2231", "3112"] or random.random() < 0.70:
                successor = "No Successor"
            else:
                successor = random.choice(["Ready 1-2 Years", "Ready 3+ Years"])
        elif age >= 50:
            ret_risk = "Medium"
            successor = random.choice(["Ready Now", "Ready 1-2 Years", "No Successor"])
        else:
            ret_risk = "Low"
            successor = "Not Applicable"  # Not retiring soon
            
        records.append({
            "employee_id": emp_id,
            "name": name,
            "age": age,
            "department": dept,
            "job_title": title,
            "salary": salary,
            "region": region,
            "soc_code": soc,
            "skills": skills_str,
            "tenure_years": tenure,
            "performance_rating": perf,
            "retirement_risk": ret_risk,
            "succession_readiness": successor
        })
        
    df = pd.DataFrame(records)
    df.to_csv(WORKFORCE_FILE, index=False)
    logger.info(f"Successfully saved {len(records)} workforce records to {WORKFORCE_FILE}.")

def generate_job_descriptions() -> None:
    """
    Generates text-heavy job descriptions in JSON to test 
    keyword/skills extraction script (basic text analysis).
    """
    logger.info("Generating organizational job descriptions...")
    
    jds: List[Dict[str, str]] = []
    # Combined role list from templates and corporate roles
    all_roles: List[tuple] = []
    for soc, template in ROLE_TEMPLATES.items():
        all_roles.append((soc, template["title"], template["skills"]))
    for template in CORPORATE_ROLES:
        all_roles.append((template["soc"], template["title"], template["skills"]))
        
    for soc, title, skills in all_roles:
        # Pick some extra noise terms to make keyword extraction realistic
        noise_terms = ["collaborative environment", "stakeholder communication", "report writing", "office hours", "team player"]
        
        description_text = f"Organizational Specification for the role of {title}. " \
                           f"The core responsibility of the {title} is to deliver high-quality outcomes within our business unit. " \
                           f"Essential skills for this role include extensive experience in {', '.join(skills[:3])}. " \
                           f"Additionally, the candidate should demonstrate ability in {skills[-1] if len(skills)>3 else 'analytical thinking'}. " \
                           f"Excellent verbal and written communication is required. Familiarity with {', '.join(noise_terms[:2])} is desirable."
                           
        jds.append({
            "job_title": title,
            "soc_code": soc,
            "description_text": description_text
        })
        
    with open(JDS_FILE, "w", encoding="utf-8") as f:
        json.dump(jds, f, indent=2)
    logger.info(f"Successfully wrote {len(jds)} job descriptions to {JDS_FILE}.")

def main() -> None:
    logger.info("=========================================")
    logger.info("STARTING WORKFORCE DATA GENERATION")
    logger.info("=========================================")
    generate_workforce(count=800)
    generate_job_descriptions()
    logger.info("=========================================")
    logger.info("WORKFORCE DATA GENERATION COMPLETE")
    logger.info("=========================================")

if __name__ == "__main__":
    main()
