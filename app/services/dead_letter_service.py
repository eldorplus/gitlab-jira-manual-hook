from __future__ import annotations

import asyncpg
import uuid


class DeadLetterService:
    def __init__(self, database_url: str):
        self.database_url = database_url

    async def requeue(self, dead_letter_id: str) -> None:
        conn = await asyncpg.connect(self.database_url)
        try:
            row = await conn.fetchrow("SELECT id,topic,payload FROM webhook_dead_letters WHERE id=$1", uuid.UUID(dead_letter_id))
            if not row:
                raise ValueError(f"dead letter not found: {dead_letter_id}")
            await conn.execute("INSERT INTO webhook_queue(id,topic,payload,attempts) VALUES($1,$2,$3::jsonb,0) ON CONFLICT (id) DO NOTHING", row["id"], row["topic"], row["payload"])
            await conn.execute("DELETE FROM webhook_dead_letters WHERE id=$1", row["id"])
        finally:
            await conn.close()
