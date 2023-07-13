import time
from dataclasses import dataclass
from typing import Counter

from aiohttp import web
from aiohttp_jinja2 import template

from dmarc_report_aggregator.models import DmarcReport
from dmarc_report_aggregator.storage import DmarcReportStorage


@dataclass
class _ReportSummary:
    dkim_alignments: Counter[str]
    spf_alignments: Counter[str]

    dkim_results: dict[str, int]
    spf_results: dict[str, int]


def _summarize(report: DmarcReport) -> _ReportSummary:
    dkim_results: dict[str, int] = {}
    spf_results: dict[str, int] = {}
    for record in report.records:
        for dkim_result in record.dkim_results:
            dkim_results[dkim_result.result] = dkim_results.get(dkim_result.result, 0) + 1
        for spf_result in record.spf_results:
            spf_results[spf_result.result] = spf_results.get(spf_result.result, 0) + 1

    dkim_alignments = Counter[str](record.dkim_alignment for record in report.records)
    spf_alignments = Counter[str](record.spf_alignment for record in report.records)

    return _ReportSummary(
        dkim_alignments=dkim_alignments,
        spf_alignments=spf_alignments,
        dkim_results=dkim_results,
        spf_results=spf_results,
    )


@template("index.html.j2")
async def index_handler(request: web.Request) -> dict:
    start_time = time.time()
    storage: DmarcReportStorage = request.app["storage"]
    reports = await storage.get_all()
    summaries = tuple(map(_summarize, reports))

    return {
        "reports": reports,
        "summaries": summaries,
        "db_size": await storage.size_bytes(),
        "request_ms": round((time.time() - start_time) * 1000, 3),
    }
