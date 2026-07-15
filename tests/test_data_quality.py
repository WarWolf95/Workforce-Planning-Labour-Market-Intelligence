"""
Data quality and KPI verification tests for Workforce Planning pipeline outputs.
Runs against the generated CSV files in data/processed/powerbi/.
"""
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PBI_DIR = PROJECT_ROOT / "data" / "processed" / "powerbi"


def test_fact_employees_row_count():
    df = pd.read_csv(PBI_DIR / "fact_employees.csv")
    assert 700 <= len(df) <= 900, f"Expected ~800 employees, got {len(df)}"


def test_fact_employees_no_null_employee_id():
    df = pd.read_csv(PBI_DIR / "fact_employees.csv")
    assert df["employee_id"].notna().all(), "Null employee_id found"


def test_fact_employees_age_range():
    df = pd.read_csv(PBI_DIR / "fact_employees.csv")
    assert df["age"].between(18, 67).all(), f"Age range violation: {df['age'].min()}-{df['age'].max()}"


def test_fact_employees_positive_salary():
    df = pd.read_csv(PBI_DIR / "fact_employees.csv")
    assert (df["salary"] > 0).all(), f"Non-positive salaries found: min={df['salary'].min()}"


def test_fact_employees_departments_present():
    df = pd.read_csv(PBI_DIR / "fact_employees.csv")
    expected = {"Digital Services", "Green Energy Projects", "Clinical Operations", "Corporate Services"}
    actual = set(df["department"].unique())
    missing = expected - actual
    assert not missing, f"Missing departments: {missing}"


def test_fact_employees_valid_retirement_risk():
    df = pd.read_csv(PBI_DIR / "fact_employees.csv")
    valid = {"Low", "Medium", "High"}
    actual = set(df["retirement_risk"].unique())
    assert actual.issubset(valid), f"Invalid retirement_risk values: {actual - valid}"


def test_fact_employees_valid_succession_readiness():
    df = pd.read_csv(PBI_DIR / "fact_employees.csv")
    valid = {"Not Applicable", "No Successor", "Ready Now", "Ready 1-2 Years", "Ready 3+ Years"}
    actual = set(df["succession_readiness"].unique())
    assert actual.issubset(valid), f"Invalid succession_readiness values: {actual - valid}"


def test_dim_soc_taxonomy_codes_are_unique():
    df = pd.read_csv(PBI_DIR / "dim_soc_taxonomy.csv")
    assert df["soc_code"].is_unique, "Duplicate soc_code in dim_soc_taxonomy"


def test_dim_soc_taxonomy_categories():
    df = pd.read_csv(PBI_DIR / "dim_soc_taxonomy.csv")
    valid = {"Tech", "Green Energy", "Healthcare", "Corporate"}
    actual = set(df["category"].unique())
    assert actual.issubset(valid), f"Invalid categories: {actual - valid}"


def test_dim_ashe_salary_no_null_medians():
    df = pd.read_csv(PBI_DIR / "dim_ashe_salary.csv")
    assert df["median_salary"].notna().all(), "Null median_salary found"
    assert (df["median_salary"] > 0).all(), "Non-positive median_salary"


def test_dim_ashe_salary_positive_hourly():
    df = pd.read_csv(PBI_DIR / "dim_ashe_salary.csv")
    assert (df["hourly_median"] > 0).all(), f"Non-positive hourly_median: min={df['hourly_median'].min()}"


def test_dim_regions_has_uk():
    df = pd.read_csv(PBI_DIR / "dim_regions.csv")
    assert "United Kingdom" in df["region"].values, "Missing United Kingdom region"
    assert len(df) >= 9, f"Expected 9+ regions, got {len(df)}"


def test_fact_market_vacancies_has_records():
    df = pd.read_csv(PBI_DIR / "fact_market_vacancies.csv")
    assert len(df) > 0, "Empty fact_market_vacancies"
    assert df["salary_min"].notna().any(), "All salary_min are null"
    assert df["salary_max"].notna().any(), "All salary_max are null"


def test_fact_market_vacancies_valid_soc_codes():
    vacancies = pd.read_csv(PBI_DIR / "fact_market_vacancies.csv")
    soc = pd.read_csv(PBI_DIR / "dim_soc_taxonomy.csv")
    valid_codes = set(soc["soc_code"].astype(str))
    actual_codes = set(vacancies["soc_code"].astype(str).unique())
    orphans = actual_codes - valid_codes
    assert not orphans, f"Vacancies reference non-existent soc_codes: {orphans}"


def test_fact_market_vacancies_valid_regions():
    vacancies = pd.read_csv(PBI_DIR / "fact_market_vacancies.csv")
    regions = pd.read_csv(PBI_DIR / "dim_regions.csv")
    valid_regions = set(regions["region"])
    actual_regions = set(vacancies["region"].unique())
    orphans = actual_regions - valid_regions
    assert not orphans, f"Vacancies reference non-existent regions: {orphans}"


def test_dim_labor_supply_no_null_employed():
    df = pd.read_csv(PBI_DIR / "dim_labor_supply.csv")
    assert df["employed_count"].notna().all(), "Null employed_count"
    assert (df["employed_count"] > 0).all(), "Non-positive employed_count"


def test_key_kpi_software_developer_london_gap():
    """Verify the Software Developer London salary gap is approximately -26.3%."""
    employees = pd.read_csv(PBI_DIR / "fact_employees.csv")
    ashe = pd.read_csv(PBI_DIR / "dim_ashe_salary.csv")

    sw_devs = employees[(employees["job_title"] == "Software Developer") & (employees["region"] == "London")]
    assert len(sw_devs) > 0, "No Software Developers in London found"

    avg_internal = sw_devs["salary"].mean()
    london_median = ashe[(ashe["soc_code"] == 2136) & (ashe["region"] == "London")]["median_salary"].iloc[0]
    gap_pct = ((avg_internal - london_median) / london_median) * 100

    assert abs(gap_pct - (-26.3)) < 2.0, (
        f"Software Developer (London) gap: expected ~-26.3%, got {gap_pct:.1f}% "
        f"(internal=£{avg_internal:,.0f}, ONS=£{london_median:,.0f})"
    )


def test_key_kpi_battery_engineer_succession_gap():
    """Verify Battery Design Engineer has a meaningful succession gap."""
    df = pd.read_csv(PBI_DIR / "fact_employees.csv")
    battery = df[df["job_title"] == "Battery Design Engineer"]
    assert len(battery) > 0, "No Battery Design Engineers found"

    no_successor_count = len(battery[(battery["age"] >= 50) & (battery["succession_readiness"] == "No Successor")])
    assert no_successor_count >= 5, f"Expected >=5 no-successor, got {no_successor_count}"


def test_cross_reference_employee_soc_codes():
    """Every employee soc_code must exist in dim_soc_taxonomy."""
    employees = pd.read_csv(PBI_DIR / "fact_employees.csv")
    soc = pd.read_csv(PBI_DIR / "dim_soc_taxonomy.csv")
    valid_codes = set(soc["soc_code"].astype(str))
    actual_codes = set(employees["soc_code"].astype(str).unique())
    orphans = actual_codes - valid_codes
    assert not orphans, f"Employees reference non-existent soc_codes: {orphans}"
