from __future__ import annotations

import pytest


@pytest.fixture
def manual_payload() -> dict:
    return {
        "object_kind": "build",
        "build_status": "manual",
        "build_id": 2,
        "build_name": "deploy_production",
        "build_stage": "deploy",
        "pipeline": {"id": 1, "ref": "main"},
        "project": {"id": 42, "name": "demo"},
    }
