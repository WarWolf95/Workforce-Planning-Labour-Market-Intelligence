-- ========================================================
-- 5. DETAILED SKILLS GAP ANALYSIS QUERY (RECURSIVE CTE)
-- Computes dynamic skill overlap percentage and identifies missing skills
-- Compatible with SQLite & DuckDB
-- ========================================================

WITH RECURSIVE split_emp(employee_id, skill, rest) AS (
    SELECT employee_id, '', skills || ';' FROM fact_employees
    UNION ALL
    SELECT employee_id,
           SUBSTR(rest, 1, INSTR(rest, ';') - 1),
           SUBSTR(rest, INSTR(rest, ';') + 1)
    FROM split_emp
    WHERE rest != ''
),
emp_skills AS (
    SELECT DISTINCT employee_id, TRIM(skill) as skill
    FROM split_emp
    WHERE skill != ''
),

split_jd(soc_code, skill, rest) AS (
    SELECT soc_code, '', extracted_skills || ';' FROM dim_extracted_skills
    UNION ALL
    SELECT soc_code,
           SUBSTR(rest, 1, INSTR(rest, ';') - 1),
           SUBSTR(rest, INSTR(rest, ';') + 1)
    FROM split_jd
    WHERE rest != ''
),
jd_skills AS (
    SELECT DISTINCT soc_code, TRIM(skill) as skill
    FROM split_jd
    WHERE skill != ''
),

jd_skill_counts AS (
    SELECT soc_code, COUNT(*) as total_required
    FROM jd_skills
    GROUP BY soc_code
),

role_skills_matrix AS (
    SELECT 
        e.employee_id,
        e.name as employee_name,
        e.job_title,
        e.department,
        e.soc_code,
        j.skill as required_skill,
        CASE WHEN es.skill IS NOT NULL THEN 1 ELSE 0 END as has_skill
    FROM fact_employees e
    JOIN jd_skills j ON e.soc_code = j.soc_code
    LEFT JOIN emp_skills es ON e.employee_id = es.employee_id AND j.skill = es.skill
)

SELECT 
    m.employee_id,
    m.employee_name,
    m.job_title,
    m.department,
    c.total_required as required_skills_count,
    SUM(m.has_skill) as matched_skills_count,
    ROUND(SUM(m.has_skill) * 100.0 / c.total_required, 1) as skills_match_pct,
    COALESCE(GROUP_CONCAT(CASE WHEN m.has_skill = 0 THEN m.required_skill END, '; '), 'None (100% Match)') as missing_skills
FROM role_skills_matrix m
JOIN jd_skill_counts c ON m.soc_code = c.soc_code
GROUP BY m.employee_id, m.employee_name, m.job_title, m.department, c.total_required
ORDER BY skills_match_pct ASC, m.employee_id ASC;
