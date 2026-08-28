from __future__ import annotations

import json
import uuid

import asyncpg


class QueueRepository:
    """Durable PostgreSQL-backed queue with retry and dead-letter support."""

    def __init__(self, database_url: str):
        self.database_url = database_url

    async def ensure_schema(self) -> None:
        conn = await asyncpg.connect(self.database_url)
        try:
            await conn.execute("""
            CREATE TABLE IF NOT EXISTS webhook_queue (
              id UUID PRIMARY KEY, topic TEXT NOT NULL, payload JSONB NOT NULL,
              attempts INTEGER NOT NULL DEFAULT 0, available_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
              locked_at TIMESTAMPTZ, locked_by TEXT, last_error TEXT,
              created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS webhook_queue_ready_idx ON webhook_queue (available_at) WHERE locked_at IS NULL;
            CREATE TABLE IF NOT EXISTS webhook_dead_letters (
              id UUID PRIMARY KEY, topic TEXT NOT NULL, payload JSONB NOT NULL,
              attempts INTEGER NOT NULL, error TEXT, failed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """)
        finally:
            await conn.close()

    async def enqueue(self, topic: str, payload: dict) -> str:
        item_id = uuid.uuid4()
        conn = await asyncpg.connect(self.database_url)
        try:
            await conn.execute("INSERT INTO webhook_queue(id, topic, payload) VALUES($1,$2,$3::jsonb)", item_id, topic, json.dumps(payload))
        finally:
            await conn.close()
        return str(item_id)

    async def claim(self, worker_id: str, batch_size: int) -> list[asyncpg.Record]:
        conn = await asyncpg.connect(self.database_url)
        try:
            return await conn.fetch("""
              WITH candidates AS (
                SELECT id FROM webhook_queue
                WHERE available_at <= CURRENT_TIMESTAMP AND locked_at IS NULL
                ORDER BY created_at LIMIT $1 FOR UPDATE SKIP LOCKED
              )
              UPDATE webhook_queue q SET locked_at=CURRENT_TIMESTAMP, locked_by=$2, updated_at=CURRENT_TIMESTAMP
              FROM candidates c WHERE q.id=c.id
              RETURNING q.id, q.topic, q.payload, q.attempts
            """, batch_size, worker_id)
        finally:
            await conn.close()

    async def ack(self, item_id: str) -> None:
        conn = await asyncpg.connect(self.database_url)
        try:
            await conn.execute("DELETE FROM webhook_queue WHERE id=$1", uuid.UUID(item_id))
        finally:
            await conn.close()

    async def retry_or_dead_letter(self, item_id: str, topic: str, payload: dict, attempts: int, error: str, max_attempts: int, delay_seconds: int) -> bool:
        conn = await asyncpg.connect(self.database_url)
        try:
            if attempts + 1 >= max_attempts:
                await conn.execute("INSERT INTO webhook_dead_letters(id,topic,payload,attempts,error) VALUES($1,$2,$3::jsonb,$4,$5)", uuid.UUID(item_id), topic, json.dumps(payload), attempts + 1, error[:4000])
                await conn.execute("DELETE FROM webhook_queue WHERE id=$1", uuid.UUID(item_id))
                return True
            await conn.execute("UPDATE webhook_queue SET attempts=attempts+1, available_at=CURRENT_TIMESTAMP + ($2 * INTERVAL '1 second'), locked_at=NULL, locked_by=NULL, last_error=$3, updated_at=CURRENT_TIMESTAMP WHERE id=$1", uuid.UUID(item_id), delay_seconds, error[:4000])
            return False
        finally:
            await conn.close()
