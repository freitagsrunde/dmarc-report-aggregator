from io import BytesIO
from xml.etree.ElementTree import ElementTree, Element

from defusedxml.ElementTree import parse as etree_parse

from dmarc_report_aggregator.models import (
    DmarcReport,
    DmarcRecord,
    DmarcPolicy,
    DkimResult,
    SpfResult,
)


class XmlDmarcReportError(ValueError):
    pass


def _find_required(etree: ElementTree | Element, path: str) -> Element:
    result = etree.find(path)
    if result is None:
        raise XmlDmarcReportError(f"Missing required element '{path}'")
    return result


def _findtext_required(element: ElementTree | Element, path: str) -> str:
    result = element.findtext(path)
    if not result:
        raise XmlDmarcReportError(f"Missing required element '{path}'")
    return result


def _parse_dkim_result(element: Element) -> DkimResult:
    return DkimResult.model_validate(
        {
            "domain": _findtext_required(element, "domain"),
            "result": _findtext_required(element, "result"),
            "selector": element.findtext("selector"),
        }
    )


def _parse_spf_result(element: Element) -> SpfResult:
    return SpfResult.model_validate(
        {
            "domain": _findtext_required(element, "domain"),
            "result": _findtext_required(element, "result"),
        }
    )


def _parse_record(element: Element) -> DmarcRecord:
    return DmarcRecord.model_validate(
        {
            "from_header": _findtext_required(element, "identifiers/header_from"),
            "source_ip": _findtext_required(element, "row/source_ip"),
            "count": _findtext_required(element, "row/count"),
            "disposition": _findtext_required(
                element, "row/policy_evaluated/disposition"
            ),
            "dkim_alignment": _findtext_required(element, "row/policy_evaluated/dkim"),
            "spf_alignment": _findtext_required(element, "row/policy_evaluated/spf"),
            "dkim_results": [
                _parse_dkim_result(e) for e in element.iterfind("auth_results/dkim")
            ],
            "spf_results": [
                _parse_spf_result(e) for e in element.iterfind("auth_results/spf")
            ],
        }
    )


def _parse_policy(element: Element) -> DmarcPolicy:
    return DmarcPolicy.model_validate(
        {
            "domain": _findtext_required(element, "domain"),
            "adkim": element.findtext("adkim"),
            "aspf": element.findtext("aspf"),
            "p": _findtext_required(element, "p"),
            "sp": element.findtext("sp"),
            "pct": element.findtext("pct"),
        }
    )


def parse_report(source: bytes) -> DmarcReport:
    etree: ElementTree = etree_parse(BytesIO(source))

    return DmarcReport.model_validate(
        {
            "id": _findtext_required(etree, "report_metadata/report_id"),
            "org_name": _findtext_required(etree, "report_metadata/org_name"),
            "email": _findtext_required(etree, "report_metadata/email"),
            "extra_contact_info": etree.findtext("report_metadata/extra_contact_info"),
            "start": _findtext_required(etree, "report_metadata/date_range/begin"),
            "end": _findtext_required(etree, "report_metadata/date_range/end"),
            "policy": _parse_policy(_find_required(etree, "policy_published")),
            "records": [_parse_record(e) for e in etree.iterfind("record")],
        }
    )
