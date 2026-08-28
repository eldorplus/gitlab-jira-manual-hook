from app.services.policy_service import PolicyService
from app.services.webhook_service import ManualJob


def job():
    return ManualJob(42, "demo", "", 1, 2, "deploy_production", "deploy", "manual", "main", "abc", "", "")


def test_missing_policy_is_fail_closed():
    service = PolicyService("does-not-exist.yml")
    assert service.allowed(job()) is False
