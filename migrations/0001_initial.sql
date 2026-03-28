-- Starter migration for the hackathon MVP.
-- The runnable local path uses SQLAlchemy create_all() for speed.
-- Production follow-up should convert this schema into Alembic-managed revisions.

CREATE TABLE IF NOT EXISTS workspaces (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  context_json JSON NOT NULL,
  normalized_context_json JSON NOT NULL,
  missing_fields_json JSON NOT NULL,
  readiness_to_research BOOLEAN NOT NULL,
  assumption_summary_json JSON NOT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS workflow_runs (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL REFERENCES workspaces(id),
  status TEXT NOT NULL,
  stage_order_json JSON NOT NULL,
  current_stage TEXT NOT NULL,
  correlation_id TEXT NOT NULL,
  budget_json JSON NOT NULL,
  error_text TEXT NULL,
  created_at TIMESTAMP NOT NULL,
  updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NULL REFERENCES workspaces(id),
  event_type TEXT NOT NULL,
  severity TEXT NOT NULL,
  correlation_id TEXT NOT NULL,
  actor_type TEXT NOT NULL,
  actor_id TEXT NULL,
  payload_json JSON NOT NULL,
  created_at TIMESTAMP NOT NULL
);
