import gzip
import logging
import re
from email.message import Message
from io import BytesIO
from zipfile import ZipFile

import dkim
from aiosmtpd.handlers import AsyncMessage

from dmarc_report_aggregator.models import DmarcReport
from dmarc_report_aggregator.smtp._parser import parse_report
from dmarc_report_aggregator.storage import DmarcReportStorage

_log = logging.getLogger(__name__)
_dkim_log = logging.getLogger(dkim.__name__)


class ReportExtractionError(Exception):
    pass


def _extract_report_from_zip(payload: bytes, report_basename: str, message_id: str, *,
                             max_size: int = 1024 * 1024) -> bytes:
    with ZipFile(BytesIO(payload)) as zip_file:
        expected_name = f"{report_basename}.xml"
        try:
            report_fileinfo = zip_file.getinfo(expected_name)
        except KeyError:
            raise ReportExtractionError(f"{message_id}: Report ZIP doesn't contain a file named '{expected_name}'")

        if report_fileinfo.file_size > 1024 * 1024:  # 1MiB
            raise ReportExtractionError(
                f"{message_id}: Zipped report '%s' is too large uncompressed: {report_fileinfo.file_size} > {max_size}")

        return zip_file.read(report_fileinfo)


def _require_content_type(part: Message, message_id: str, expected_type: str, *more_types: str) -> None:
    if part.get_content_type() not in (expected_type, *more_types):
        raise ReportExtractionError(f"{message_id}: Report content type does not match file extension, "
                                    f"expected one of {(expected_type, *more_types)}.")


_ATTACHMENT_NAME_PATTERN = re.compile(
    r"""(?ax)
    ^(?P<receiver_domain>[a-zA-Z0-9-.]+\.[a-zA-Z]{2,})
    !(?P<policy_domain>[a-zA-Z0-9-.]+\.[a-zA-Z]{2,})
    !(?P<begin>\d+)
    !(?P<end>\d+)
    (?:!(?P<id>\d+))?
    (?P<ext>(?:\.\w+)+)$
    """, re.X
)


def report_from_message(message: Message, message_id: str) -> DmarcReport | None:
    for part in message.walk():
        name = part.get_filename()
        if not name:
            continue

        match = _ATTACHMENT_NAME_PATTERN.match(name)
        if not match:
            continue

        payload = part.get_payload(decode=True)
        assert isinstance(payload, bytes)

        match match["ext"]:
            case ".xml":  # No compression.
                _require_content_type(part, message_id, "application/xml", "text/xml", "text/plain")
            case ".xml.zip" | ".zip":  # ZIP compression.
                _require_content_type(part, message_id, "application/zip")
                payload = _extract_report_from_zip(payload, name.removesuffix(match["ext"]), message_id)
            case ".xml.gz":  # GZIP compression.
                _require_content_type(part, message_id, "application/gzip")
                payload = gzip.decompress(payload)
            case other:
                raise ReportExtractionError(f"'{message_id}': Unrecognized file extension '{other}'")

        return parse_report(payload)

    return None


class DmarcSavingHandler(AsyncMessage):
    def __init__(self, storage: DmarcReportStorage):
        super().__init__()
        self._storage = storage

    async def handle_message(self, message: Message) -> None:
        message_id = message.get("Message-ID")
        if not message_id:
            _log.info("Disregarding message without Message-ID")
            return

        # dkim_result = await dkim.verify_async(message.as_bytes(), logger=_dkim_log)
        dkim_result = True
        if not dkim_result:
            _log.info("'%s': Disregarding message due to failed DKIM verification", message_id)
            return

        report = report_from_message(message, message_id)
        if not report:
            _log.info("'%s': Message contains no DMARC report", message_id)
            return

        await self._storage.store(report)

    async def handle_exception(self, e: Exception) -> str:
        # Default behaviour is to send the exception message to the client. Let's not do that though.
        _log.exception(e)
        return "250 OK"
