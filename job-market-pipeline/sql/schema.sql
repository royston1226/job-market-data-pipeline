CREATE TABLE IF NOT EXISTS companies (
 company_id BIGINT PRIMARY KEY
);
CREATE TABLE IF NOT EXISTS jobs (
 id TEXT PRIMARY KEY,
 job_id TEXT,
 company_id BIGINT NOT NULL REFERENCES companies(company_id),
 title TEXT NOT NULL CHECK (length(title)>0),
 department TEXT,
 employment_type TEXT,
 workplace_type TEXT,
 country TEXT,
 apply_url TEXT,
 status TEXT,
 is_remote BOOLEAN NOT NULL,
 posted_at TIMESTAMPTZ,
 fetched_time TIMESTAMPTZ,
 close_time TIMESTAMPTZ,
 duration_days DOUBLE PRECISION CHECK (duration_days>=0),
 quality_flags TEXT[] NOT NULL
);
CREATE INDEX IF NOT EXISTS jobs_country ON jobs(country);
CREATE INDEX IF NOT EXISTS jobs_posted_at ON jobs(posted_at);
CREATE INDEX IF NOT EXISTS jobs_company ON jobs(company_id);
