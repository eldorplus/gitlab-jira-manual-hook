CREATE TABLE IF NOT EXISTS manual_actions (
    id BIGSERIAL PRIMARY KEY,
    project_id BIGINT NOT NULL,
    pipeline_id BIGINT NOT NULL,
    job_id BIGINT NOT NULL,
    project_name TEXT NOT NULL,
    job_name TEXT NOT NULL,
    stage TEXT NOT NULL,
    state VARCHAR(32) NOT NULL DEFAULT 'processing',
    jira_issue_key VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (project_id, pipeline_id, job_id)
);
CREATE INDEX IF NOT EXISTS idx_manual_actions_state ON manual_actions(state);
CREATE INDEX IF NOT EXISTS idx_manual_actions_jira ON manual_actions(jira_issue_key);
