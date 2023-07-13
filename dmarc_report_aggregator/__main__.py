import asyncio
import logging
from asyncio import TaskGroup

from dmarc_report_aggregator.settings import Settings

try:
    import aiomonitor
except ImportError:
    aiomonitor = None

from dmarc_report_aggregator.smtp import DmarcSmtpServer
from dmarc_report_aggregator.storage import DmarcReportStorage
from dmarc_report_aggregator.web import DmarcWebApp


async def main(settings: Settings) -> None:
    storage = DmarcReportStorage(settings.db_uri)
    await storage.migrate()
    smtp_server = DmarcSmtpServer(settings.smtp, storage)
    web_app = DmarcWebApp(settings.http, storage)

    async with TaskGroup() as tg:
        tg.create_task(smtp_server.run(), name="SMTP server")
        tg.create_task(web_app.run(), name="HTTP server")


if __name__ == '__main__':
    settings = Settings()

    logging.basicConfig(level=settings.loglevel)
    logging.getLogger("mail.log").setLevel(logging.WARNING)  # aiosmtpd

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    if aiomonitor:
        with aiomonitor.start_monitor(loop):
            loop.run_until_complete(main(settings))
    else:
        loop.run_until_complete(main(settings))
