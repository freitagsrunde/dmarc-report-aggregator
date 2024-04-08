from typing import Literal, Sequence

from pydantic import BaseModel, AwareDatetime, conint, IPvAnyAddress, PositiveInt, Field


class DkimResult(BaseModel):
    domain: str
    result: Literal[
        "none", "pass", "fail", "policy", "neutral", "temperror", "permerror"
    ]
    selector: str | None


class SpfResult(BaseModel):
    domain: str
    result: Literal[
        "none", "pass", "fail", "softfail", "neutral", "temperror", "permerror"
    ]


class DmarcPolicy(BaseModel):
    domain: str
    adkim: Literal["r", "s"] | None
    aspf: Literal["r", "s"] | None
    p: Literal["none", "quarantine", "reject"]
    sp: Literal["none", "quarantine", "reject"] | None
    pct: conint(ge=0, le=100) | None


class DmarcRecord(BaseModel):
    from_header: str
    source_ip: IPvAnyAddress
    count: PositiveInt

    disposition: Literal["none", "quarantine", "reject"]
    dkim_alignment: Literal["pass", "fail"]
    spf_alignment: Literal["pass", "fail"]

    dkim_results: Sequence[DkimResult]
    spf_results: Sequence[SpfResult]


class DmarcReport(BaseModel):
    id: str
    org_name: str
    email: str
    extra_contact_info: str | None = None
    start: AwareDatetime
    end: AwareDatetime

    policy: DmarcPolicy

    records: Sequence[DmarcRecord] = Field(min_length=1)
