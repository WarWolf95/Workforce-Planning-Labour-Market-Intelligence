"""
Centralized Configuration for Workforce Planning & Labour Market Intelligence.
Defines standard UK regions, SOC code mapping taxonomies, skills vocabularies,
and mock data parameters.
"""

from typing import Dict, List

# Standard UK Regions for analysis
REGIONS: List[str] = [
    "London",
    "South East",
    "West Midlands",
    "North West",
    "Scotland",
    "Wales",
    "East of England",
    "South West",
]

# Names generator helper
FIRST_NAMES: List[str] = [
    "Oliver", "Amelia", "George", "Isla", "Harry", "Ava", "Noah", "Emily", "Jack", "Sophia", 
    "Leo", "Grace", "Oscar", "Mia", "Arthur", "Lily", "Muhammad", "Freya", "Henry", "Ivy",
    "Thomas", "Florence", "David", "Sarah", "James", "Helen", "Robert", "Rachel", "William", "Clara"
]
LAST_NAMES: List[str] = [
    "Smith", "Jones", "Taylor", "Brown", "Williams", "Wilson", "Johnson", "Davies", "Robinson", 
    "Wright", "Thompson", "Evans", "Walker", "White", "Roberts", "Green", "Hall", "Wood", "Harris", "Martin"
]

# All regions including national aggregate
ALL_REGIONS: List[str] = ["United Kingdom"] + REGIONS

# Standard Occupational Classification (SOC 2020) target taxonomy
TARGET_SOCS: Dict[str, Dict[str, str]] = {
    # Tech
    "2135": {"title": "IT business analysts, architects and systems designers", "category": "Tech"},
    "2136": {"title": "Programmers and software development professionals", "category": "Tech"},
    "2137": {"title": "Web design and development professionals", "category": "Tech"},
    "2139": {"title": "Information technology professionals n.e.c.", "category": "Tech"},
    "3131": {"title": "IT operations technicians", "category": "Tech"},
    # Green Energy
    "2121": {"title": "Civil engineers", "category": "Green Energy"},
    "2122": {"title": "Mechanical engineers", "category": "Green Energy"},
    "2123": {"title": "Electrical engineers", "category": "Green Energy"},
    "2125": {"title": "Chemical engineers", "category": "Green Energy"},
    "2126": {"title": "Design and development engineers", "category": "Green Energy"},
    "3112": {"title": "Electrical and electronics technicians", "category": "Green Energy"},
    "8124": {"title": "Energy plant operatives", "category": "Green Energy"},
    # Healthcare
    "2211": {"title": "Medical practitioners", "category": "Healthcare"},
    "2231": {"title": "Nurses", "category": "Healthcare"},
    "2237": {"title": "Pharmacists", "category": "Healthcare"},
    "3211": {"title": "Medical technicians", "category": "Healthcare"},
    "6141": {"title": "Nursing auxiliaries and assistants", "category": "Healthcare"}
}

# Role Mapping for Synthetic HR Generation and DDL creation
ROLE_TEMPLATES: Dict[str, Dict[str, any]] = {
    "2135": {"title": "IT Business Analyst", "base_salary": 53000, "skills": ["Business Analysis", "UML", "Agile", "Jira", "Requirements Gathering"]},
    "2136": {"title": "Software Developer", "base_salary": 45000, "skills": ["Python", "SQL", "Git", "JavaScript"]},
    "2137": {"title": "Web Designer", "base_salary": 34000, "skills": ["HTML", "CSS", "UI/UX", "WordPress"]},
    "2139": {"title": "Data Engineer", "base_salary": 43000, "skills": ["SQL", "Python", "Data Pipelines", "AWS"]},
    "3131": {"title": "IT Support Analyst", "base_salary": 31000, "skills": ["Troubleshooting", "Networking", "Office 365", "Active Directory"]},
    "2121": {"title": "Civil Engineer", "base_salary": 44000, "skills": ["AutoCAD", "Structural Analysis", "Project Management"]},
    "2122": {"title": "Mechanical Engineer", "base_salary": 42000, "skills": ["CAD", "Thermodynamics", "Mechanical Design"]},
    "2123": {"title": "Electrical Grid Engineer", "base_salary": 45000, "skills": ["Power Systems", "Grid Connections", "HV Electrical"]},
    "2125": {"title": "Chemical Engineer", "base_salary": 50000, "skills": ["Chemical Process", "ASPEN", "Mass Balance"]},
    "2126": {"title": "Battery Design Engineer", "base_salary": 42000, "skills": ["Product Design", "SolidWorks", "Prototyping"]},
    "3112": {"title": "Turbine Maintenance Technician", "base_salary": 31000, "skills": ["Electrical Testing", "Maintenance", "Instrumentation"]},
    "8124": {"title": "Energy Plant Operator", "base_salary": 32000, "skills": ["Plant Operations", "SCADA", "Health & Safety"]},
    "2211": {"title": "Clinical Practitioner", "base_salary": 82000, "skills": ["Clinical Diagnostics", "Patient Care", "Prescribing"]},
    "2231": {"title": "Staff Nurse", "base_salary": 35500, "skills": ["Patient Assessment", "Medication Administration", "NMC Pin", "CPR"]},
    "2237": {"title": "Pharmacist", "base_salary": 41000, "skills": ["Medicines Management", "Clinical Pharmacy", "Patient Counselling"]},
    "3211": {"title": "Medical Imaging Technician", "base_salary": 30000, "skills": ["Medical Imaging", "MRI", "X-Ray"]},
    "6141": {"title": "Healthcare Assistant", "base_salary": 22000, "skills": ["Personal Care", "Patient Mobility", "Vital Signs"]}
}

# Corporate roles mapping (non-shortage)
CORPORATE_ROLES: List[Dict[str, any]] = [
    {"title": "HR Advisor", "soc": "3562", "base_salary": 32000, "skills": ["Employee Relations", "Recruitment", "Employment Law"]},
    {"title": "Finance Analyst", "soc": "2424", "base_salary": 42000, "skills": ["Financial Modelling", "Excel", "Budgeting"]},
    {"title": "Operations Administrator", "soc": "4159", "base_salary": 24000, "skills": ["Administration", "Scheduling", "Customer Service"]}
]

# Skills vocabulary by SOC code (for Adzuna mock data generation)
SKILLS_BY_SOC: Dict[str, List[str]] = {
    "2136": ["Python", "JavaScript", "React", "Docker", "SQL", "Git", "Java", "Node.js", "APIs"],
    "2135": ["Business Analysis", "UML", "Agile", "Requirements Gathering", "TOGAF", "System Architecture", "Jira"],
    "2137": ["HTML", "CSS", "UI/UX", "Figma", "Responsive Design", "WordPress", "Web Content"],
    "2139": ["AWS", "Terraform", "Kubernetes", "CI/CD", "Linux", "Cyber Security", "Data Pipelines", "Spark"],
    "3131": ["Active Directory", "Windows Server", "ITIL", "Troubleshooting", "Networking", "Office 365"],
    "2121": ["AutoCAD", "Structural Analysis", "Project Management", "CDM Regulations", "Civil Engineering"],
    "2122": ["CAD", "Thermodynamics", "Mechanical Design", "FEA", "Turbine Technology", "HVAC"],
    "2123": ["Power Systems", "Grid Connections", "HV Electrical", "PLC Programming", "MATLAB"],
    "2125": ["Chemical Process", "ASPEN", "Mass Balance", "Hydrogen Safety", "Fluid Dynamics"],
    "2126": ["Product Design", "SolidWorks", "Prototyping", "Battery Chemistry", "Renewable Design"],
    "3112": ["Electrical Testing", "Maintenance", "Safety Regulations", "Instrumentation", "Wiring"],
    "8124": ["Plant Operations", "SCADA", "Health & Safety", "Boiler Control", "Equipment Maintenance"],
    "2211": ["Clinical Diagnostics", "Patient Care", "Prescribing", "Medical Research", "Internal Medicine"],
    "2231": ["Patient Assessment", "Wound Care", "Medication Administration", "NMC Pin", "Record Keeping", "CPR"],
    "2237": ["Medicines Management", "Prescription Auditing", "Clinical Pharmacy", "Patient Counselling"],
    "3211": ["Medical Imaging", "MRI", "X-Ray", "Laboratory Testing", "Pathology"],
    "6141": ["Personal Care", "Patient Mobility", "Vital Signs", "Infection Control", "Compassionate Care"]
}

# Global Skills Vocabulary for keyword extraction calibration
SKILLS_VOCABULARY: List[str] = [
    # Tech skills
    "python", "javascript", "react", "docker", "sql", "git", "java", "node.js", "apis",
    "business analysis", "uml", "agile", "jira", "requirements gathering", "togaf", 
    "system architecture", "html", "css", "ui/ux", "figma", "responsive design", 
    "wordpress", "web content", "aws", "terraform", "kubernetes", "ci/cd", "linux", 
    "cyber security", "data pipelines", "spark", "active directory", "windows server", 
    "itil", "troubleshooting", "networking", "office 365",
    # Engineering/Green energy
    "autocad", "structural analysis", "project management", "cdm regulations", 
    "civil engineering", "cad", "thermodynamics", "mechanical design", "fea", 
    "turbine technology", "hvac", "power systems", "grid connections", "hv electrical", 
    "plc programming", "matlab", "chemical process", "aspen", "mass balance", 
    "hydrogen safety", "fluid dynamics", "product design", "solidworks", "prototyping", 
    "battery chemistry", "renewable design", "electrical testing", "maintenance", 
    "safety regulations", "instrumentation", "wiring", "plant operations", "scada", 
    "health & safety", "boiler control", "equipment maintenance",
    # Healthcare
    "clinical diagnostics", "patient care", "prescribing", "medical research", 
    "internal medicine", "patient assessment", "wound care", "medication administration", 
    "nmc pin", "record keeping", "cpr", "medicines management", "prescription auditing", 
    "clinical pharmacy", "patient counselling", "medical imaging", "mri", "x-ray", 
    "laboratory testing", "pathology", "personal care", "patient mobility", "vital signs", 
    "infection control", "compassionate care",
    # Corporate Support
    "employee relations", "recruitment", "employment law", "financial modelling", 
    "excel", "budgeting", "administration", "scheduling", "customer service"
]

# Organization Departments and BUs
DEPTS: Dict[str, List[str]] = {
    "Digital Services": ["2135", "2136", "2137", "2139", "3131"],
    "Green Energy Projects": ["2121", "2122", "2123", "2125", "2126", "3112", "8124"],
    "Clinical Operations": ["2211", "2231", "2237", "3211", "6141"],
    "Corporate Services": [] # Non-shortage support roles (finance, HR, admin)
}
