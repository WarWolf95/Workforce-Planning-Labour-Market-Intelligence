-- ========================================================
-- 1. SALARY GAP ANALYSIS QUERY
-- Compatible with Oracle SQL & SQLite
-- ========================================================

SELECT 
    e.soc_code,
    e.job_title,
    t.category,
    e.region,
    COUNT(*) as employee_count,
    ROUND(AVG(e.salary), 0) as avg_internal_salary,
    a.median_salary as ONS_median_salary,
    ROUND(AVG(e.salary) - a.median_salary, 0) as salary_difference,
    ROUND(((AVG(e.salary) - a.median_salary) / a.median_salary) * 100, 1) as salary_gap_percentage
FROM fact_employees e
JOIN dim_soc_taxonomy t ON e.soc_code = t.soc_code
JOIN dim_ashe_salary a ON e.soc_code = a.soc_code AND e.region = a.region
GROUP BY e.soc_code, e.job_title, t.category, e.region, a.median_salary
ORDER BY salary_gap_percentage ASC;
