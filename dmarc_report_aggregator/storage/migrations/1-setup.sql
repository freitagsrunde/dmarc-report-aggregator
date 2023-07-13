CREATE TABLE dmarc_report
(
    -- report_id is really an integer, but may be too large to fit in sqlite's signed 64-bit integer type.
    report_id          TEXT NOT NULL,
    org_name           TEXT NOT NULL,
    email              TEXT NOT NULL,
    extra_contact_info TEXT,
    begin_timestamp    TEXT NOT NULL,
    end_timestamp      TEXT NOT NULL,

    policy_domain      TEXT NOT NULL,
    policy_adkim       CHARACTER(1),
    policy_aspf        CHARACTER(1),
    policy_p           TEXT NOT NULL,
    policy_sp          TEXT,
    policy_pct         INT,

    PRIMARY KEY (report_id, org_name)
);

CREATE TABLE dmarc_record
(
    report_id   TEXT NOT NULL,
    org_name    TEXT NOT NULL,
    no          INT  NOT NULL,

    header_from TEXT NOT NULL,
    source_ip   TEXT NOT NULL,
    count       INT  NOT NULL CHECK (count > 0),

    disposition TEXT NOT NULL,
    dkim        TEXT NOT NULL,
    spf         TEXT NOT NULL,

    FOREIGN KEY (report_id, org_name) REFERENCES dmarc_report (report_id, org_name),
    PRIMARY KEY (report_id, org_name, no)
);

CREATE TABLE dkim_result
(
    report_id TEXT NOT NULL REFERENCES dmarc_record (report_id),
    org_name  TEXT NOT NULL REFERENCES dmarc_record (org_name),
    record_no INT  NOT NULL REFERENCES dmarc_record (no),
    no        INT  NOT NULL,

    domain    TEXT NOT NULL,
    result    TEXT NOT NULL,
    selector  TEXT NOT NULL,

    FOREIGN KEY (report_id, org_name, record_no) REFERENCES dmarc_record (report_id, org_name, no),
    PRIMARY KEY (report_id, org_name, record_no, no)
);

CREATE TABLE spf_result
(
    report_id TEXT NOT NULL REFERENCES dmarc_record (report_id),
    org_name  TEXT NOT NULL REFERENCES dmarc_record (org_name),
    record_no INT  NOT NULL REFERENCES dmarc_record (no),
    no        INT  NOT NULL,

    domain    TEXT NOT NULL,
    result    TEXT NOT NULL,

    FOREIGN KEY (report_id, org_name, record_no) REFERENCES dmarc_record (report_id, org_name, no),
    PRIMARY KEY (report_id, org_name, record_no, no)
);
