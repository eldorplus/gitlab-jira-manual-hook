from __future__ import annotations

import asyncpg

from app.services.webhook_service import ManualJob


class ManualActionRepository:
    def __init__(self, database_url: str):
        self.database_url = database_url

    async def record_or_get(self, job: ManualJob) -> tuple[bool, str | None]:
        conn = await asyncpg.connect(self.database_url)
        try:
            row = await conn.fetchrow("""
                INSERT INTO manual_actions (project_id,pipeline_id,job_id,project_name,job_name,stage,state)
                VALUES ($1,$2,$3,$4,$5,$6,'processing')
                ON CONFLICT (project_id,pipeline_id,job_id)
                DO UPDATE SET updated_at=CURRENT_TIMESTAMP
                RETURNING jira_issue_key,(xmax=0) AS inserted
            """, job.project_id, job.pipeline_id, job.job_id, job.project_name, job.job_name, job.stage)
            return bool(row["inserted"]), row["jira_issue_key"]
        finally:
            await conn.close()

    async def get_issue_key(self, job: ManualJob) -> str | None:
        conn = await asyncpg.connect(self.database_url)
        try:
            return await conn.fetchval("SELECT jira_issue_key FROM manual_actions WHERE project_id=$1 AND pipeline_id=$2 AND job_id=$3", job.project_id, job.pipeline_id, job.job_id)
        finally:
            await conn.close()

    async def set_created(self, job: ManualJob, issue_key: str) -> None:
        conn = await asyncpg.connect(self.database_url)
        try:
            await conn.execute("UPDATE manual_actions SET jira_issue_key=$1,state='created',updated_at=CURRENT_TIMESTAMP WHERE project_id=$2 AND pipeline_id=$3 AND job_id=$4", issue_key, job.project_id, job.pipeline_id, job.job_id)
        finally:
            await conn.close()

    async def set_failed(self, job: ManualJob) -> None:
        conn = await asyncpg.connect(self.database_url)
        try:
            await conn.execute("UPDATE manual_actions SET state='failed',updated_at=CURRENT_TIMESTAMP WHERE project_id=$1 AND pipeline_id=$2 AND job_id=$3", job.project_id, job.pipeline_id, job.job_id)
        finally:
            await conn.close()
