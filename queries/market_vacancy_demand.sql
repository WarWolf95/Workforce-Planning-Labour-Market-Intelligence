-- ========================================================
-- 3. MARKET VACANCY DEMAND QUERY
-- Compatible with Oracle SQL & SQLite
-- ========================================================

SELECT 
    v.soc_code,
    t.soc_title,
    t.category,
    v.region,
    COUNT(*) as active_postings_count,
    ROUND(AVG(v.salary_min), 0) as avg_market_min_salary,
    ROUND(AVG(v.salary_max), 0) as avg_market_max_salary
FROM fact_market_vacancies v
JOIN dim_soc_taxonomy t ON v.soc_code = t.soc_code
WHERE v.region != 'United Kingdom'
GROUP BY v.soc_code, t.soc_title, t.category, v.region
ORDER BY active_postings_count DESC;
