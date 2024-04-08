from typing import NamedTuple

import aiosqlite

from dmarc_report_aggregator.models import (
    DkimResult,
    SpfResult,
    DmarcRecord,
    DmarcReport,
)


class _RecordPk(NamedTuple):
    report_id: str
    org_name: str
    no: int


class _ResultPk(NamedTuple):
    report_id: str
    org_name: str
    record_no: int
    no: int


async def _store_dkim_result(
    db: aiosqlite.Connection, result: DkimResult, pk: _ResultPk
) -> None:
    await db.execute(
        """
        INSERT INTO dkim_result (report_id, org_name, record_no, no, domain, result, selector)
        VALUES (?, ?, ?, ?, ?, ?, ?) 
        """,
        (*pk, result.domain, result.result, result.selector),
    )


async def _store_spf_result(
    db: aiosqlite.Connection, result: SpfResult, pk: _ResultPk
) -> None:
    await db.execute(
        """
        INSERT INTO spf_result (report_id, org_name, record_no, no, domain, result)
        VALUES (?, ?, ?, ?, ?, ?) 
        """,
        (*pk, result.domain, result.result),
    )


async def _store_record(
    db: aiosqlite.Connection, record: DmarcRecord, pk: _RecordPk
) -> None:
    await db.execute(
        """
        INSERT INTO dmarc_record (report_id, org_name, no, header_from, source_ip, count, disposition, dkim, spf)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            *pk,
            record.from_header,
            str(record.source_ip),
            record.count,
            record.disposition,
            record.dkim_alignment,
            record.spf_alignment,
        ),
    )

    for i, result in enumerate(record.dkim_results):
        await _store_dkim_result(db, result, _ResultPk(*pk, i))

    for i, result in enumerate(record.spf_results):
        await _store_spf_result(db, result, _ResultPk(*pk, i))


async def store_report(db: aiosqlite.Connection, report: DmarcReport) -> None:
    await db.execute(
        """
        INSERT INTO dmarc_report 
        (report_id, org_name, email, extra_contact_info, begin_timestamp, end_timestamp, 
         policy_domain, policy_adkim, policy_aspf, policy_p, policy_sp, policy_pct)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            report.id,
            report.org_name,
            report.email,
            report.extra_contact_info,
            report.start,
            report.end,
            report.policy.domain,
            report.policy.adkim,
            report.policy.aspf,
            report.policy.p,
            report.policy.sp,
            report.policy.pct,
        ),
    )

    for i, record in enumerate(report.records):
        await _store_record(db, record, _RecordPk(report.id, report.org_name, i))
