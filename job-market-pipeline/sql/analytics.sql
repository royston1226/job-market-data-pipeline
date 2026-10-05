-- 1. Country counts, including unknown location.
SELECT COALESCE(country,'Unknown') AS country, COUNT(*) AS postings
FROM jobs GROUP BY country ORDER BY postings DESC LIMIT 20;
-- 2. Remote share by country (only sufficiently large groups).
SELECT country, COUNT(*) AS postings,
 ROUND(100.0*AVG(is_remote::int),2) AS remote_percent
FROM jobs WHERE country IS NOT NULL GROUP BY country HAVING COUNT(*)>=100
ORDER BY remote_percent DESC;
-- 3. Monthly posting volume, including active and closed postings.
SELECT date_trunc('month',posted_at) AS month,COUNT(*) AS postings
FROM jobs WHERE posted_at IS NOT NULL GROUP BY month ORDER BY month;
-- 4. Employment types.
SELECT employment_type,COUNT(*) FROM jobs GROUP BY employment_type ORDER BY COUNT(*) DESC;
-- 5. Observed duration of closed postings, excluding invalid chronology.
SELECT country,COUNT(*) AS closed_with_dates,AVG(duration_days) AS mean_days,
 percentile_cont(0.5) WITHIN GROUP (ORDER BY duration_days) AS median_days
FROM jobs WHERE status='closed' AND duration_days IS NOT NULL
GROUP BY country HAVING COUNT(*)>=20 ORDER BY closed_with_dates DESC;
-- 6. Company IDs with most postings (names unavailable).
SELECT c.company_id,COUNT(*) AS postings FROM companies c
JOIN jobs j USING(company_id) GROUP BY c.company_id ORDER BY postings DESC LIMIT 20;
-- 7. Titles among jobs marked active. This is source status, not live verification.
SELECT title,COUNT(*) AS postings FROM jobs WHERE status='active'
GROUP BY title ORDER BY postings DESC LIMIT 20;
-- 8. Conflicting remote indicators.
SELECT id,title,country,quality_flags FROM jobs
WHERE 'remote_onsite_conflict'=ANY(quality_flags) LIMIT 20;
