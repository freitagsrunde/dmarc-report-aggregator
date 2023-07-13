import asyncio
import logging
from asyncio import Server, get_running_loop

from aiosmtpd.smtp import SMTP

from dmarc_report_aggregator.settings import SmtpSettings
from dmarc_report_aggregator.smtp._handler import DmarcSavingHandler
from dmarc_report_aggregator.storage import DmarcReportStorage

_log = logging.getLogger(__name__)


class DmarcSmtpServer:
    def __init__(self, settings: SmtpSettings, storage: DmarcReportStorage):
        self.host = settings.host
        self.port = settings.port
        self._storage = storage

        self._server: Server | None = None
        self._ready = asyncio.Event()

    async def run(self) -> None:
        loop = get_running_loop()
        self._server = await loop.create_server(lambda: SMTP(DmarcSavingHandler(self._storage)),
                                                self.host, self.port)

        try:
            # Update port in case 0 was used to select an unused port.
            self.host, self.port = self._server.sockets[0].getsockname()[:2]
            _log.info("SMTP server started on %s:%s.", self.host, self.port)
            self._ready.set()

            await self._server.wait_closed()
        finally:
            self._server.close()
            await self._server.wait_closed()
            self._server = None

    async def ready(self) -> None:
        await self._ready.wait()
