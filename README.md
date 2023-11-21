# DMARC Report Aggregator

Collects and visualizes DMARC reports. Unlike other tools, it does this by running its own SMTP server to collect DMARC
reports and storing them in an SQLite database, as opposed to connecting to your IMAP server.

## Setup

### Running from Source

```shell
python -m dmarc_report_aggregator
```

### Using Docker

```shell
docker run -v ./data:/data ghcr.io/freitagsrunde/dmarc-report-aggregator:latest
```

Where the DMARC report database will be stored in `./data`.

## Configuration

Uses environment variables via [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).

| Environment Variable        | Default Value                                    | Description                                                                                                                                                                                                                    |
|-----------------------------|--------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `LOGLEVEL`                  | `INFO`                                           |                                                                                                                                                                                                                                |
| `DB_URI`                    |                                                  | [SQLite connection URI](https://www.sqlite.org/uri.html). The docker image defaults this to `file:/data/db.sqlite3`.                                                                                                           |
| `SMTP__HOST`                | `0.0.0.0`                                        | Host for SMTP server to accept DMARC reports on.                                                                                                                                                                               |
| `SMTP__PORT`                | `8025`                                           | Port for SMTP server to accept DMARC reports on.                                                                                                                                                                               |
| `SMTP__VALIDATE_DKIM`       | `yes`                                            | If turned off, DKIM signatures on incoming DMARC reports will not be checked.                                                                                                                                                  |
| `HTTP__HOST`                | `0.0.0.0`                                        | Host for web interface.                                                                                                                                                                                                        |
| `HTTP__PORT`                | `8080`                                           | Port for web interface.                                                                                                                                                                                                        |
| `HTTP__LDAP__ENABLED`       | `yes`                                            | Enable authentication, backed by an LDAP server.                                                                                                                                                                               |
| `HTTP__LDAP__URL`           |                                                  | LDAP server URL.                                                                                                                                                                                                               |
| `HTTP__LDAP__USER_DN`       |                                                  | Template for user DNs. `{username}` will be replaced with the entered username.                                                                                                                                                |
| `HTTP__LDAP__FILTER`        | `(objectClass=*)` (meaning no additional filter) | If set, only LDAP entries matching this filter are considered authorized to access the application. Can be used to (for instance) restrict access to specific groups. `{username}` will be replaced with the entered username. |
| `HTTP__LDAP__COOKIE_SECRET` | a securely-random value generated on startup     | Secret used to encrypt session cookies.                                                                                                                                                                                        |

## License

This project is licensed under the terms of the MIT license. See [LICENSE](./LICENSE).
