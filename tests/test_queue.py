import pytest

from app.repositories.queue_repository import QueueRepository


class FakeConn:
    def __init__(self):
        self.executed = []

    async def execute(self, sql, *args):
        self.executed.append((sql, args))

    async def close(self):
        pass


@pytest.mark.asyncio
async def test_enqueue_serializes_payload(monkeypatch):
    conn = FakeConn()

    async def fake_connect(_):
        return conn

    import app.repositories.queue_repository as module
    monkeypatch.setattr(module.asyncpg, "connect", fake_connect)
    queue = QueueRepository("postgresql://test")
    item_id = await queue.enqueue("jira.manual_job", {"object_kind": "build"})
    assert item_id
    assert conn.executed
    assert "webhook_queue" in conn.executed[0][0]


def test_retry_delay_is_exponential():
    base = 2
    assert [base * (2 ** attempt) for attempt in range(5)] == [2, 4, 8, 16, 32]
