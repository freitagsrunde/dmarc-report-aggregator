FROM python:3.11.5-alpine

ADD / /dmarc-report-aggregator
RUN pip install /dmarc-report-aggregator && rm -rf /dmarc-report-aggregator

ENTRYPOINT ["python", "-m", "dmarc_report_aggregator"]
EXPOSE 8080 8025
VOLUME /data

ENV DB_URI="file:/data/db.sqlite3"

LABEL org.opencontainers.image.authors="maxh@freitagsrunde.org"
LABEL org.opencontainers.image.source="https://github.com/freitagsrunde/dmarc-report-aggregator"
