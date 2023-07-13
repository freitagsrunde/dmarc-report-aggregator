import asyncio
import email
import logging
from asyncio import to_thread, CancelledError
from contextlib import suppress
from email.message import Message
from importlib import resources
from pathlib import Path
from smtplib import SMTP
from typing import Generator
from unittest import mock
from unittest.mock import AsyncMock

import pytest

from dmarc_report_aggregator.settings import SmtpSettings
from dmarc_report_aggregator.smtp import DmarcSmtpServer
from dmarc_report_aggregator.storage import DmarcReportStorage
from . import real_reports

logging.basicConfig(level=logging.DEBUG)


@pytest.fixture
async def storage(tmp_path: Path) -> DmarcReportStorage:
    storage = DmarcReportStorage(f"file:{tmp_path / 'db.sqlite3'}")
    await storage.migrate()
    return storage


@pytest.fixture
async def server(storage: DmarcReportStorage) -> Generator[DmarcSmtpServer, None, None]:
    server = DmarcSmtpServer(SmtpSettings(host="localhost", port=0), storage)
    task = asyncio.create_task(server.run(), name="SMTP server")
    try:
        await server.ready()
        yield server
    finally:
        task.cancel()
        with suppress(CancelledError):
            await task


def _sync_send_message(host: str, port: int, message: Message) -> None:
    with SMTP(host, port) as smtp:
        smtp.send_message(message)


@pytest.mark.parametrize("filename,expected_org_name", (
        ("aol.eml", "Yahoo"),
        ("fastmail.eml", "Fastmail Pty Ltd"),
        ("google.eml", "google.com"),
        ("mailru.eml", "Mail.Ru"),
        ("outlook.eml", "Outlook.com"),
        ("outlook-enterprise.eml", "Enterprise Outlook"),
        ("yahoo.eml", "Yahoo")
))
async def test_real_reports(
        filename: str, expected_org_name: str,
        storage: DmarcReportStorage, server: DmarcSmtpServer
) -> None:
    with (mock.patch("dkim.verify_async", new=AsyncMock(return_value=True)),
          resources.files(real_reports).joinpath(filename).open("rb") as file):
        message = email.message_from_binary_file(file)
        await to_thread(lambda: _sync_send_message("localhost", server.port, message))

    reports = await storage.get_all()
    assert len(reports) == 1
    assert reports[0].org_name == expected_org_name
