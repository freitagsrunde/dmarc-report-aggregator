from typing import Literal, Annotated

from pydantic import BaseModel, BeforeValidator, conbytes
from pydantic_settings import BaseSettings, SettingsConfigDict


def _validate_bool(value: object) -> bool:
    if value is True:
        return True
    if isinstance(value, str):
        if value.lower() in ("true", "1", "yes", "y"):
            return True
        if value.lower() in ("false", "0", "no", "n"):
            return False

    raise ValueError(f"expected boolean, got '{value!r}'")


class SmtpSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8025
    validate_dkim: bool = True


class LdapSettings(BaseModel):
    enabled: Annotated[Literal[True], BeforeValidator(_validate_bool)]

    url: str
    user_dn: str
    user_filter: str = "(objectClass=*)"
    cookie_secret: conbytes(min_length=32, max_length=32) | None = None


class LdapDisabled(BaseModel):
    enabled: Annotated[Literal[False], BeforeValidator(_validate_bool)] = False


class HttpSettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8080

    ldap: LdapSettings | LdapDisabled = LdapDisabled()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_nested_delimiter='__')

    loglevel: str = "INFO"
    db_uri: str

    smtp: SmtpSettings = SmtpSettings()
    http: HttpSettings = HttpSettings()
