# Power BI Dashboard Implementation Guide

This guide details the complete, step-by-step implementation of the **Workforce Planning & Labour Market Intelligence Dashboard** using the processed CSV files located in `data/processed/powerbi/`.

---

## Step 1: Ingest & Model Data (Star Schema)

1.  **Load Files**: Open Power BI Desktop, click **Get Data** -> **Text/CSV**, and select all 7 files from [data/processed/powerbi/](file:///c:/Projects/Workforce%20Planning%20&%20Labour%20Market%20Intelligence/data/processed/powerbi).
2.  **Verify Relationships**: Go to the **Model View** (left sidebar) and create a clean **Star Schema**. Power BI may auto-detect some links, but verify that they match the following settings:
    *   `dim_soc_taxonomy.soc_code` (1) $\rightarrow$ `fact_employees.soc_code` (*) [Single, Active]
    *   `dim_soc_taxonomy.soc_code` (1) $\rightarrow$ `fact_market_vacancies.soc_code` (*) [Single, Active]
    *   `dim_soc_taxonomy.soc_code` (1) $\rightarrow$ `dim_ashe_salary.soc_code` (*) [Single, Active]
    *   `dim_soc_taxonomy.soc_code` (1) $\rightarrow$ `dim_labor_supply.soc_code` (*) [Single, Active]
    *   `dim_regions.region` (1) $\rightarrow$ `fact_employees.region` (*) [Single, Active]
    *   `dim_regions.region` (1) $\rightarrow$ `fact_market_vacancies.region` (*) [Single, Active]
    *   `dim_regions.region` (1) $\rightarrow$ `dim_ashe_salary.region` (*) [Single, Active]
    *   `dim_regions.region` (1) $\rightarrow$ `dim_labor_supply.region` (*) [Single, Active]

---

## Step 2: Write DAX Measures

Create a new table for measures (click **Enter Data**, name it `_Measures`, and load). Create the following DAX measures:

### 1. Internal Salary Metrics
```dax
Avg Salary Internal = AVERAGE(fact_employees[salary])
```
*Format: Currency (£), 0 decimal places.*

### 2. ONS Benchmark Salary Metrics
```dax
Avg Salary ONS Median = AVERAGE(dim_ashe_salary[median_salary])
```
*Format: Currency (£), 0 decimal places.*

### 3. Salary Gap Calculations
```dax
Salary Gap GBP = [Avg Salary Internal] - [Avg Salary ONS Median]
```
*Format: Currency (£), 0 decimal places.*

```dax
Salary Gap Pct = DIVIDE([Salary Gap GBP], [Avg Salary ONS Median], 0)
```
*Format: Percentage (%), 1 decimal place.*

### 4. Demographics & Retirement Risks
```dax
Employee Count = COALESCE(COUNTROWS(fact_employees), 0)
```
*Format: Whole Number.*

```dax
Retirement Risk Count 5Yr = CALCULATE([Employee Count], fact_employees[age] >= 55)
```
*Format: Whole Number.*

```dax
Retirement Risk Pct = DIVIDE([Retirement Risk Count 5Yr], [Employee Count], 0)
```
*Format: Percentage (%), 1 decimal place.*

### 5. Succession Pipeline Gaps
```dax
Critical Staff Age 50 Plus = CALCULATE([Employee Count], fact_employees[age] >= 50)
```

```dax
No Successor Count = CALCULATE([Employee Count], fact_employees[succession_readiness] = "No Successor", fact_employees[age] >= 50)
```

```dax
Succession Gap Pct = DIVIDE([No Successor Count], [Critical Staff Age 50 Plus], 0)
```
*Format: Percentage (%), 1 decimal place.*

### 6. External Vacancy Volumes
```dax
Market Vacancy Count = COUNTROWS(fact_market_vacancies)
```
*Format: Whole Number.*

---

## Step 3: Design Dashboard Pages

Use a cohesive, modern visual theme (Dark Slate background or Sleek White, with a clean serif font like *Georgia* or clean sans-serif like *Segoe UI*).

### Page 1: Workforce Overview & Demographics
*   **KPI Cards**: Total Employees (`[Employee Count]`), Average Internal Salary (`[Avg Salary Internal]`), Overall Retirement Risk (`[Retirement Risk Pct]`).
*   **Donut Chart**: Employees by **Shortage Category** (`dim_soc_taxonomy[category]`).
*   **Stacked Bar Chart**: Employee count by **Age Bracket** (Create a grouping/bin of 10-year intervals: 20-29, 30-39, 40-49, 50-59, 60+).
*   **Table Visual**: Department list showing employee counts, average age, and succession gap percentage.

### Page 2: Salary Benchmark & Market Mapping
*   **Clustered Bar Chart (Regional Audit)**: Region (`dim_regions[region]`) on Y-Axis, `[Market Vacancy Count]` on X-Axis, with bar colors conditionally formatted by `[Salary Gap Pct]` (red = high lag, green = lead). This operates entirely offline and bypasses Power BI Bing Maps API security blocks.
*   **Scatter Plot**: 
    *   X-Axis: `[Avg Salary ONS Median]`
    *   Y-Axis: `[Avg Salary Internal]`
    *   Details: `dim_soc_taxonomy[soc_title]`
    *   *Add a $45^\circ$ reference line ($y=x$)*. Points below the line indicate salary lag.
*   **Clustered Column Chart**: Average internal vs. ONS Median salary by role.
*   **Slicers**: Region (`dim_regions[region]`), Shortage Category (`dim_soc_taxonomy[category]`).

### Page 3: Succession & Operational Risk Matrix
*   **Matrix Visual**: 
    *   Rows: Department $\rightarrow$ Job Title
    *   Columns: (None)
    *   Values: `[Employee Count]`, `[Retirement Risk Pct]`, `[Succession Gap Pct]`
    *   *Conditional Formatting*: Highlight cells in the `[Succession Gap Pct]` and `[Retirement Risk Pct]` columns using red/orange gradients where risk is high.
*   **Bar Chart**: Top 10 roles ordered by `[No Successor Count]`.
*   **Multi-row Card**: Mapped skills taxonomy for the selected role (`dim_extracted_skills[extracted_skills]`) to show what capabilities must be hired.

---

## Step 4: Verification Check

Once visuals are created, verify these figures in your charts to assert correctness:
1.  **Software Developer (London)** visual must show a salary gap of exactly **-26.3%** (£47,907 vs £65,040 ONS).
2.  **Battery Design Engineer** must show a retirement risk of **41.0%** and **11** critical roles without a successor.
