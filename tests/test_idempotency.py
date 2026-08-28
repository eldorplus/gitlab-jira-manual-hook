from app.services.idempotency_service import IdempotencyService


def test_key_is_stable():
    assert IdempotencyService.key(42, 1, 2) == "gitlab:42:pipeline:1:job:2"


class Repo:
    async def exists(self, project_id: int, pipeline_id: int, job_id: int) -> bool:
        return (project_id, pipeline_id, job_id) == (42, 1, 2)


async def test_already_processed():
    service = IdempotencyService(Repo())
    assert await service.already_processed(42, 1, 2) is True
    assert await service.already_processed(42, 1, 3) is False
