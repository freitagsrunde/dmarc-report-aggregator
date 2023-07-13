import logging
from contextlib import asynccontextmanager
from typing import Generator

import aiosqlite

from dmarc_report_aggregator.models import DmarcReport
from dmarc_report_aggregator.storage._load import _load_report
from dmarc_report_aggregator.storage._migration import migrate_db
from dmarc_report_aggregator.storage._store import store_report

_log = logging.getLogger(__name__)


class DmarcReportStorage:
    def __init__(self, uri: str) -> None:
        self._uri = uri

    @asynccontextmanager
    async def _connect(self) -> Generator[aiosqlite.Connection, None, None]:
        async with aiosqlite.connect(self._uri, uri=True) as db:
            db.row_factory = aiosqlite.Row
            yield db

    async def migrate(self) -> None:
        async with self._connect() as db:
            await migrate_db(db)

    async def store(self, report: DmarcReport) -> None:
        async with self._connect() as db:
            await store_report(db, report)
            await db.commit()

    async def get_all(self) -> list[DmarcReport]:
        reports = []
        async with self._connect() as db:
            async for row in await db.execute("SELECT * FROM dmarc_report ORDER BY begin_timestamp DESC"):
                reports.append(await _load_report(db, row))

        return reports

    async def get_one(self, org_name: str, report_id: str) -> DmarcReport:
        async with self._connect() as db:
            async with db.execute("SELECT * FROM dmarc_report WHERE org_name = ? AND report_id = ?",
                                  (org_name, report_id)) as cursor:
                cursor: aiosqlite.Cursor
                row = await cursor.fetchone()
                if not row:
                    raise ValueError(f"No report {org_name}/{report_id}")
                return await _load_report(db, row)

    async def size_bytes(self) -> int:
        async with self._connect() as db:
            db: aiosqlite.Connection
            page_count = (await (await db.execute("PRAGMA page_count")).fetchone())[0]
            page_size = (await (await db.execute("PRAGMA page_size")).fetchone())[0]

        return page_count * page_size
