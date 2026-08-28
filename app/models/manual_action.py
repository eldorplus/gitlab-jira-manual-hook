from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ManualAction:
    project_id: int
    pipeline_id: int
    job_id: int
    project_name: str
    job_name: str
    stage: str
    status: str = "manual"
    jira_issue_key: str | None = None
    state: str = "pending"
    created_at: datetime | None = None
    updated_at: datetime | None = None
