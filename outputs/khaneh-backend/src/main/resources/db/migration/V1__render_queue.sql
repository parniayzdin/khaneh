CREATE TABLE render_jobs (
  id VARCHAR(36) PRIMARY KEY,
  asset_id VARCHAR(40) NOT NULL,
  preset VARCHAR(20) NOT NULL,
  device VARCHAR(12) NOT NULL,
  status VARCHAR(16) NOT NULL CHECK (status IN ('QUEUED','RUNNING','SUCCEEDED','FAILED','CANCELLED')),
  progress INTEGER NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
  attempts INTEGER NOT NULL DEFAULT 0,
  worker_id VARCHAR(80),
  lease_token VARCHAR(36),
  lease_until TIMESTAMP WITH TIME ZONE,
  renderer VARCHAR(120),
  created_at TIMESTAMP WITH TIME ZONE NOT NULL,
  started_at TIMESTAMP WITH TIME ZONE,
  finished_at TIMESTAMP WITH TIME ZONE,
  elapsed_ms BIGINT,
  artifacts VARCHAR(2000),
  artifact_attempt VARCHAR(36),
  error VARCHAR(2000)
);
CREATE INDEX render_jobs_queue ON render_jobs(status, created_at);
CREATE TABLE render_workers (
  id VARCHAR(80) PRIMARY KEY,
  last_seen TIMESTAMP WITH TIME ZONE NOT NULL,
  devices VARCHAR(500) NOT NULL
);
