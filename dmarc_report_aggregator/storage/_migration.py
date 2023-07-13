import bisect
import logging
from datetime import datetime
from importlib import resources
from importlib.abc import Traversable
from operator import attrgetter

import aiosqlite

_log = logging.getLogger(__name__)


def _collect_migrations() -> list[Traversable]:
    from . import migrations as migrations_pkg
    migrations: list[Traversable] = []
    for traversable in resources.files(migrations_pkg).iterdir():
        if traversable.is_file() and traversable.name.endswith(".sql"):
            bisect.insort(migrations, traversable, key=attrgetter("name"))

    return migrations


async def migrate_db(db: aiosqlite.Connection) -> None:
    migrations = _collect_migrations()

    await db.executescript("""
        CREATE TABLE IF NOT EXISTS migrations (
            name TEXT PRIMARY KEY NOT NULL,
            applied_at TEXT NOT NULL
        );
    """)

    async with db.execute("SELECT * FROM migrations") as cursor:
        applied_migrations = [row[0] for row in await cursor.fetchall()]

    for migration in migrations:
        async with db.cursor() as cursor:
            basename = migration.name.removesuffix(".sql")
            if basename in applied_migrations:
                _log.debug("Migration '%s' is already applied", basename)
                continue

            _log.info("Running migration '%s'", basename)

            sql = "BEGIN EXCLUSIVE;\n"
            sql += migration.read_text()
            await cursor.executescript(sql)

            await cursor.execute("INSERT INTO migrations VALUES (?, ?)",
                                 (basename, datetime.utcnow()))
            await cursor.execute("COMMIT")
