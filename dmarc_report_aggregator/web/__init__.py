import asyncio
import logging

import aiohttp_jinja2
import jinja2
from aiohttp import web

from dmarc_report_aggregator.settings import HttpSettings
from dmarc_report_aggregator.storage import DmarcReportStorage
from dmarc_report_aggregator.web._auth import setup_auth
from dmarc_report_aggregator.web._index import index_handler
from dmarc_report_aggregator.web._report import report_handler

_log = logging.getLogger(__name__)


class DmarcWebApp:
    def __init__(self, settings: HttpSettings, storage: DmarcReportStorage) -> None:
        self._host = settings.host
        self._port = settings.port
        self._storage = storage

        self._app = web.Application()
        self._app["storage"] = storage

        self._app.add_routes([
            web.get("/", index_handler),
            web.get("/{org_name}/{report_id}", report_handler)
        ])

        jinja_env = aiohttp_jinja2.setup(self._app,
                                         context_processors=(aiohttp_jinja2.request_processor,),
                                         loader=jinja2.PackageLoader(__package__))
        jinja_env.globals["zip"] = zip

        if settings.ldap.enabled:
            setup_auth(self._app, settings.ldap)
        else:
            _log.warning("Authentication is disabled.")

    async def run(self):
        runner = web.AppRunner(self._app)
        await runner.setup()
        try:
            site = web.TCPSite(runner, self._host, self._port)
            await site.start()

            _log.info("HTTP server started on http://%s:%s.", self._host, self._port)

            await site._server.wait_closed()
        finally:
            await runner.cleanup()
