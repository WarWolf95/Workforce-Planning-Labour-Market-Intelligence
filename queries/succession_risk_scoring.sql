-- ========================================================
-- 2. SUCCESSION & RETIREMENT RISK SCORING QUERY
-- Compatible with Oracle SQL & SQLite
-- ========================================================

SELECT 
    e.soc_code,
    e.job_title,
    t.category,
    COUNT(*) as total_employees,
    SUM(CASE WHEN e.age >= 55 THEN 1 ELSE 0 END) as retirement_risk_count_5yr,
    ROUND(SUM(CASE WHEN e.age >= 55 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as retirement_risk_pct,
    SUM(CASE WHEN e.age >= 50 AND e.succession_readiness = 'No Successor' THEN 1 ELSE 0 END) as critical_no_successor_count,
    ROUND(
        (SUM(CASE WHEN e.age >= 55 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) * 0.5 + 
        (SUM(CASE WHEN e.age >= 50 AND e.succession_readiness = 'No Successor' THEN 1 ELSE 0 END) * 100.0 / COUNT(*)) * 0.5,
        1
    ) as composite_succession_risk_score
FROM fact_employees e
JOIN dim_soc_taxonomy t ON e.soc_code = t.soc_code
GROUP BY e.soc_code, e.job_title, t.category
ORDER BY composite_succession_risk_score DESC;
