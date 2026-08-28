from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ManualJob:
    project_id: int
    project_name: str
    project_web_url: str
    pipeline_id: int
    job_id: int
    job_name: str
    stage: str
    status: str
    ref: str
    commit_sha: str
    job_url: str
    pipeline_url: str


def parse_gitlab_job(payload: dict[str, Any]) -> ManualJob | None:
    if payload.get("object_kind") != "build" or payload.get("build_status") != "manual":
        return None
    project = payload.get("project") or {}
    commit = payload.get("commit") or {}
    pipeline = payload.get("pipeline") or {}
    if any(payload.get(k) is None for k in ("project_id", "pipeline_id", "build_id")):
        return None
    return ManualJob(
        project_id=int(payload["project_id"]),
        project_name=str(payload.get("project_name") or project.get("name", "unknown")),
        project_web_url=str(project.get("web_url", "")),
        pipeline_id=int(payload["pipeline_id"]),
        job_id=int(payload["build_id"]),
        job_name=str(payload.get("build_name", "unknown")),
        stage=str(payload.get("build_stage", "unknown")),
        status="manual",
        ref=str(payload.get("ref", "")),
        commit_sha=str(commit.get("id", "")),
        job_url=str(payload.get("build_url", "")),
        pipeline_url=str(pipeline.get("url", "")),
    )
