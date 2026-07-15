-- ========================================================
-- 4. SKILLS MISMATCH ANALYSIS QUERY
-- Compatible with Oracle SQL & SQLite
-- ========================================================

SELECT 
    soc_code,
    job_title,
    COUNT(*) as total_staff,
    SUM(CASE WHEN skills LIKE '%Python%' THEN 1 ELSE 0 END) as has_python,
    SUM(CASE WHEN skills LIKE '%React%' THEN 1 ELSE 0 END) as has_react,
    SUM(CASE WHEN skills LIKE '%SCADA%' THEN 1 ELSE 0 END) as has_scada,
    SUM(CASE WHEN skills LIKE '%NMC Pin%' THEN 1 ELSE 0 END) as has_nmc_pin,
    SUM(CASE WHEN skills LIKE '%AWS%' THEN 1 ELSE 0 END) as has_aws,
    SUM(CASE WHEN skills LIKE '%AutoCAD%' THEN 1 ELSE 0 END) as has_autocad
FROM fact_employees
GROUP BY soc_code, job_title;
