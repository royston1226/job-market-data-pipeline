# Demo guide
1. Show the actual source columns using pipeline/inspect_data.py.
2. Explain Parquet batching and raw MongoDB storage before transformation.
3. Show reports/latest_run.json with measured counts and stage timings.
4. Run sql/analytics.sql and explain GROUP BY, HAVING and the company join.
5. Search a title, then apply country, active/closed and remote filters.
6. Explain missing fields, flagged chronology and historical-snapshot limitations.
7. Explain rerun upserts and the absence of cross-database atomicity.

Laptop acceptance checks: run the pipeline twice with the same ROW_LIMIT and compare stored counts; test title search, blank search and filters with no results; check SQL and Elasticsearch stored counts agree. These integration checks have not been run in the development environment.
