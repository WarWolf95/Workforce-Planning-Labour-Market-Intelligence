"""
Shared utility functions and logging configurations for Workforce Planning.
"""

import logging
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Union
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

def setup_logging(logger_name: str = "workforce_planning") -> logging.Logger:
    logger = logging.getLogger(logger_name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger

logger = setup_logging("utils")

def clean_skill_casing(skill: str) -> str:
    acronyms = {
        "uml": "UML", "html": "HTML", "css": "CSS", "ui": "UI", "ux": "UX", "aws": "AWS",
        "plc": "PLC", "matlab": "MATLAB", "aspen": "ASPEN", "fea": "FEA",
        "hvac": "HVAC", "hv": "HV", "cad": "CAD", "scada": "SCADA", "mri": "MRI",
        "cpr": "CPR", "nmc": "NMC", "git": "Git", "jira": "Jira", "figma": "Figma",
        "sql": "SQL", "it": "IT", "itil": "ITIL", "cdm": "CDM", "apis": "APIs",
        "togaf": "TOGAF", "ci": "CI", "cd": "CD", "node.js": "Node.js",
        "wordpress": "WordPress", "autocad": "AutoCAD", "solidworks": "SolidWorks"
    }
    words = skill.split(" ")
    capitalized_words = []
    for w in words:
        if "-" in w:
            parts = w.split("-")
            capitalized_parts = [acronyms.get(p.lower(), p.capitalize()) for p in parts]
            capitalized_words.append("-".join(capitalized_parts))
        elif "/" in w:
            parts = w.split("/")
            capitalized_parts = [acronyms.get(p.lower(), p.capitalize()) for p in parts]
            capitalized_words.append("/".join(capitalized_parts))
        else:
            capitalized_words.append(acronyms.get(w.lower(), w.capitalize()))
    return " ".join(capitalized_words)

def extract_skills_from_jds(
    jd_path: Path,
    skills_vocabulary: List[str]
) -> List[Dict[str, Any]]:
    """
    Scans job descriptions for matching skills in a predefined taxonomy.
    Uses TF-IDF term-frequency weighting to score and rank keywords, falling back
    to exact regex matching if scikit-learn vectorization is unavailable.
    """
    logger.info("Matching taxonomy keywords against organizational job descriptions...")
    
    if not jd_path.exists():
        logger.error(f"Job description file not found at {jd_path}")
        return []
        
    with open(jd_path, "r", encoding="utf-8") as f:
        jds = json.load(f)
        
    documents = [jd["description_text"] for jd in jds]
    
    # Configure vectorizer using our custom skills vocabulary
    vectorizer = TfidfVectorizer(vocabulary=skills_vocabulary, ngram_range=(1, 3), lowercase=True)
    
    try:
        tfidf_matrix = vectorizer.fit_transform(documents)
        feature_names = vectorizer.get_feature_names_out()
        
        extracted_skills_list = []
        for idx, jd in enumerate(jds):
            # Get tf-idf scores for this document
            doc_vector = tfidf_matrix[idx].toarray()[0]
            # Match skills that have non-zero score
            matched_skills = []
            for col_idx, score in enumerate(doc_vector):
                if score > 0:
                    matched_skills.append((feature_names[col_idx], round(float(score), 4)))
            
            # Sort skills by score descending
            matched_skills.sort(key=lambda x: x[1], reverse=True)
            skills_str = ";".join([clean_skill_casing(s[0]) for s in matched_skills])
            
            extracted_skills_list.append({
                "job_title": jd["job_title"],
                "soc_code": jd["soc_code"],
                "extracted_skills": skills_str,
                "skills_count": len(matched_skills)
            })
            
        logger.info(f"Successfully mapped taxonomy keywords for {len(extracted_skills_list)} job descriptions.")
        return extracted_skills_list
    except Exception as e:
        logger.warning(f"TF-IDF weighting failed: {e}. Falling back to direct regex keyword scanner.")
        # Fallback to regex word matching
        extracted_skills_list = []
        for jd in jds:
            text = jd["description_text"].lower()
            matched = []
            for skill in skills_vocabulary:
                if re.search(r'\b' + re.escape(skill) + r'\b', text):
                    matched.append(skill)
            extracted_skills_list.append({
                "job_title": jd["job_title"],
                "soc_code": jd["soc_code"],
                "extracted_skills": ";".join([clean_skill_casing(skill) for skill in matched]),
                "skills_count": len(matched)
            })
        return extracted_skills_list
