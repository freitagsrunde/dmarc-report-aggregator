from datetime import datetime, UTC

import aiosqlite

from dmarc_report_aggregator.models import DkimResult, SpfResult, DmarcRecord, DmarcReport, DmarcPolicy


async def _load_record(db: aiosqlite.Connection, row: aiosqlite.Row) -> DmarcRecord:
    dkim_results = []
    async for dkim_row in await db.execute(
            "SELECT * FROM dkim_result WHERE org_name = ? AND report_id = ? AND record_no = ? ORDER BY no",
            (row["org_name"], row["report_id"], row["no"])
    ):
        dkim_results.append(DkimResult(
            domain=dkim_row["domain"],
            selector=dkim_row["selector"],
            result=dkim_row["result"]
        ))

    spf_results = []
    async for spf_row in await db.execute(
            "SELECT * FROM spf_result WHERE org_name = ? AND report_id = ? AND record_no = ? ORDER BY no",
            (row["org_name"], row["report_id"], row["no"])
    ):
        spf_results.append(SpfResult(domain=spf_row["domain"], result=spf_row["result"]))

    return DmarcRecord(
        from_header=row["header_from"],
        source_ip=row["source_ip"],
        count=row["count"],

        disposition=row["disposition"],
        dkim_alignment=row["dkim"],
        spf_alignment=row["spf"],

        dkim_results=dkim_results,
        spf_results=spf_results,
    )


def _parse_dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso).replace(tzinfo=UTC)


async def _load_report(db: aiosqlite.Connection, row: aiosqlite.Row) -> DmarcReport:
    records = []
    async for record_row in await db.execute(
            "SELECT * FROM dmarc_record WHERE org_name = ? AND report_id = ? ORDER BY no",
            (row["org_name"], row["report_id"])
    ):
        records.append(await _load_record(db, record_row))

    return DmarcReport(
        id=row["report_id"],
        org_name=row["org_name"],
        email=row["email"],
        extra_contact_info=row["extra_contact_info"],
        start=_parse_dt(row["begin_timestamp"]),
        end=_parse_dt(row["end_timestamp"]),
        policy=DmarcPolicy(
            domain=row["policy_domain"],
            adkim=row["policy_adkim"],
            aspf=row["policy_aspf"],
            p=row["policy_p"],
            sp=row["policy_sp"],
            pct=row["policy_pct"]
        ),
        records=records
    )
