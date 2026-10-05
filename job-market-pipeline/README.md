# Job Market Data Pipeline

A reproducible local pipeline for the supplied OpenJobData metadata snapshot.
Parquet -> MongoDB raw documents -> Python cleaning -> PostgreSQL analytics and Elasticsearch title/department search -> Streamlit.

## Run on Windows

1. Install and start Docker Desktop with Linux containers. Allow approximately 6 GB of Docker memory and sufficient disk for images/data.
2. Extract this ZIP into a **new folder**. The included `data/part-0.parquet` is your original dataset.
3. Open PowerShell in the extracted `job-market-pipeline` folder (where `docker-compose.yml` lives).
4. Run:

```powershell
docker compose up --build -d
docker compose logs -f pipeline
```

When the pipeline prints a completed report, press Ctrl+C to stop following logs. Open http://localhost:8501 . The app starts only after the pipeline succeeds. First run processes 25,000 source rows so startup is manageable.

To process the full dataset:

```powershell
$env:ROW_LIMIT="0"
docker compose run --rm pipeline
docker compose up -d app
```

The source files are processed in sorted filename order; this is a prefix, not a random sample. Add other compatible Parquet files to `data/` if needed.

## Inspect, test, and query

Local inspection needs Python and PyArrow:

```powershell
python -m pip install pyarrow
python pipeline/inspect_data.py
python -m unittest discover -s tests -v
```

Run example SQL analytics:

```powershell
Get-Content sql/analytics.sql -Raw | docker compose exec -T postgres psql -U jobs -d jobs
```

Inspect service state or failures:

```powershell
docker compose ps -a
docker compose logs --tail 100 pipeline elasticsearch postgres app
```

`reports/latest_run.json` contains measured pipeline counts/timing after a successful run. `reports/local_validation.json` records the separate local transformation scan performed during development. No database timing is invented.

Stop services while keeping stored data:

```powershell
docker compose down
```

## What each component does

| Component | Responsibility |
|---|---|
| Parquet | Original source, read in batches of 1,000 |
| MongoDB | Raw records plus source filename and ingestion run identifier |
| Python | Read raw documents back, validate/normalize, flag data quality issues |
| PostgreSQL | Typed job facts, company-ID relationship, SQL analysis |
| Elasticsearch | Ranked title/department retrieval plus exact filters |
| Streamlit | Search and SQL-based analytics |
| Docker Compose | Service health checks and startup order |

## Dataset and design

The supplied file has 400,000 rows and 14 columns. It contains identifiers, job titles, departments, employment/workplace categories, country, remote flag, posting/fetch/close timestamps, application URL and status. It has **no description, salary, city, company name or skill list**. No such fields or derived skill claims are invented.

`companies(company_id)` preserves source company identities without inventing names. `jobs.id` is the source identifier and primary key; `jobs.company_id` references companies. `job_id` is retained but is not assumed globally unique. This is deliberately a small relational design grounded in the available fields.

Transformations collapse text whitespace, convert blank strings to NULL, normalize full/part-time categories, normalize status/workplace case, preserve UTC dates, validate required identifiers/title/company/remote fields, validate application URLs, and flag inconsistent dates or remote indicators. Unknown categories remain as source values. Country names are trimmed but not guessed or mapped to ISO codes.

Posting duration is computed only for records marked closed with valid posting/closing dates. It is observed source duration, not time to hire. An unknown department stays NULL. Missing dates stay NULL. Invalid required fields are excluded from the clean stores but retained in raw MongoDB. Data-quality flags are queryable in SQL and search.

## Reruns and consistency

Mongo replacement upserts, SQL upserts, and Elasticsearch document IDs make reruns of the same dataset avoid duplicate stored jobs. Duplicate source IDs within one run use the **first record**, counted in the report. This is deterministic but is not a latest-version merge policy.

SQL commits each batch before Elasticsearch indexing. There is no cross-database transaction. If a service fails, the process exits unsuccessfully; rerun the same source/limit to repair partially completed batches. A completed report is written only after success. An old successful report can remain after a failed rerun; check the current logs and exit status.

Stores accumulate/upsert records; reducing the row limit does not delete previously loaded records. Source removals are not propagated. Fresh-snapshot reconciliation, scheduled ingestion, retries beyond Elasticsearch bulk retry, rejected-record dashboards and richer source integration are future work. Use a fresh Compose project name with `docker compose -p jobsfresh up --build -d` for isolated empty volumes (stop the old app first to free port 8501).

## Search and analytics

Search uses Elasticsearch `multi_match` over title (boost 3) and department, with automatic typo tolerance, plus country/status/remote filters. Results show up to 50 records. SQL demonstrates WHERE, GROUP BY, HAVING, ORDER BY, joins, aggregates and median duration in `sql/analytics.sql`.

The dashboard summarizes **the stored snapshot**, which may include closed jobs, historical data and geographic/source bias. Source status is not verified live. First-25k analytics are not representative of the full file. Original posting links may no longer work. Remote share describes the source boolean; conflicts are preserved and flagged.

## Validation and practical limits

Six transformation unit tests passed. Python source compiled and Compose YAML parsed. The full supplied Parquet file was scanned through the transformation functions; actual results are in `reports/local_validation.json`.

Docker is unavailable in the development environment, so container builds, database writes, Elasticsearch retrieval and the Streamlit browser flow **have not been integration-tested here**. Run the startup commands on your laptop and check the logs before a demo. Pinned dependency/image versions make setup reproducible; updating them requires compatibility testing.

This local demo uses a fixed PostgreSQL password and unauthenticated internal Mongo/Elasticsearch services. Only Streamlit is published, bound to localhost. It is intended for local use.
