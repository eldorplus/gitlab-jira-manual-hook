from __future__ import annotations

import asyncio
import logging
import os
import socket

from app.config import get_settings
from app.repositories.manual_action_repository import ManualActionRepository
from app.repositories.queue_repository import QueueRepository
from app.services.jira_service import JiraService
from app.services.webhook_service import parse_gitlab_job

logger = logging.getLogger(__name__)


async def process_item(item, settings, queue: QueueRepository) -> None:
    item_id, topic, payload, attempts = str(item["id"]), item["topic"], dict(item["payload"]), item["attempts"]
    try:
        if topic == "jira.manual_job":
            job = parse_gitlab_job(payload)
            if job is None:
                await queue.ack(item_id)
                return
            repo = ManualActionRepository(settings.database_url)
            issue = await JiraService(settings).create_or_update_issue(job)
            await repo.set_created(job, issue)
        else:
            raise ValueError(f"unknown queue topic: {topic}")
        await queue.ack(item_id)
    except Exception as exc:
        dead = await queue.retry_or_dead_letter(item_id, topic, payload, attempts, str(exc), settings.worker_max_attempts, settings.worker_retry_base_seconds * (2 ** attempts))
        logger.exception("queue item failed", extra={"queue_id": item_id, "dead_letter": dead})


async def run() -> None:
    settings = get_settings()
    queue = QueueRepository(settings.database_url)
    await queue.ensure_schema()
    worker_id = f"{socket.gethostname()}:{os.getpid()}"
    logger.info("worker started", extra={"worker_id": worker_id})
    while True:
        items = await queue.claim(worker_id, settings.worker_batch_size)
        if not items:
            await asyncio.sleep(settings.worker_poll_interval)
            continue
        for item in items:
            await process_item(item, settings, queue)


def main() -> None:
    logging.basicConfig(level=get_settings().log_level)
    asyncio.run(run())


if __name__ == "__main__":
    main()
