import time

from aiohttp import web
from aiohttp_jinja2 import template

from dmarc_report_aggregator.storage import DmarcReportStorage


@template("report.html.j2")
async def report_handler(request: web.Request) -> dict:
    start_time = time.time()
    storage: DmarcReportStorage = request.app["storage"]
    report = await storage.get_one(request.match_info["org_name"], request.match_info["report_id"])

    return {
        "report": report,
        "db_size": await storage.size_bytes(),
        "request_ms": round((time.time() - start_time) * 1000, 3),
    }
