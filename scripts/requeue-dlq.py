#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import sys

from app.config import get_settings
from app.services.dead_letter_service import DeadLetterService


async def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: scripts/requeue-dlq.py <dead-letter-uuid>")
    await DeadLetterService(get_settings().database_url).requeue(sys.argv[1])
    print(f"requeued {sys.argv[1]}")


if __name__ == "__main__":
    asyncio.run(main())
