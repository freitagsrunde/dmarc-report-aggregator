import logging
import secrets
from asyncio import to_thread
from typing import NoReturn

import ldap3
from aiohttp import web
from aiohttp.typedefs import Handler
from aiohttp_jinja2 import template, render_template
from aiohttp_session import get_session, session_middleware, new_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage
from ldap3.core.exceptions import LDAPException

from dmarc_report_aggregator.settings import LdapSettings

_log = logging.getLogger(__name__)


def _ldap_auth(settings: LdapSettings, username: str, password: str) -> str | None:
    user_dn = settings.user_dn.format(username=username)
    user_filter = settings.user_filter.format(username=username)

    connection = ldap3.Connection(settings.url, user_dn, password, authentication=ldap3.SIMPLE,
                                  read_only=True, raise_exceptions=True)
    try:
        connection.bind()
    except LDAPException:
        _log.info("Failed LDAP authentication: Bind failed: '%s'", user_dn)
        return None

    connection.search(user_dn, user_filter, search_scope=ldap3.BASE, attributes=ldap3.ALL_ATTRIBUTES)

    if not connection.entries:
        _log.warning("Failed LDAP authentication: Entry not found after bind: '%s'", user_dn)
        return None

    _log.info("Successfully authenticated user '%s' via LDAP", user_dn)
    return user_dn


def setup_auth(app: web.Application, settings: LdapSettings) -> None:
    _log.info("Enabling LDAP authentication.")
    secret = settings.cookie_secret or secrets.token_bytes(32)
    app.middlewares.append(session_middleware(EncryptedCookieStorage(secret, max_age=3600)))

    routes = web.RouteTableDef()

    @routes.get("/logout")
    @routes.post("/logout")
    async def logout(request: web.Request) -> NoReturn:
        session = await get_session(request)
        session.invalidate()
        raise web.HTTPFound("/login")

    @routes.get("/login")
    @template("login.html.j2")
    async def login_get(_: web.Request) -> {}:
        return {}

    @routes.post("/login")
    async def login_post(request: web.Request) -> NoReturn:
        form_data = await request.post()
        username = form_data.get("username", None)
        password = form_data.get("password", None)
        if not username or not password:
            _log.debug("Login without username and/or password.")
            return render_template("login.html.j2", request, {"failure": True}, status=400)
        if not username.isidentifier():
            _log.debug("Login with invalid username.")
            return render_template("login.html.j2", request, {"failure": True}, status=400)

        user_dn = await to_thread(lambda: _ldap_auth(settings, username, password))
        if not user_dn:
            return render_template("login.html.j2", request, {"failure": True}, status=403)

        session = await new_session(request)
        session["user_dn"] = user_dn
        raise web.HTTPFound("/")

    @web.middleware
    async def middleware(request: web.Request, handler: Handler) -> web.StreamResponse:
        if request.path in ("/login", "/logout"):
            return await handler(request)

        session = await get_session(request)
        if "user_dn" in session:
            user_dn = session["user_dn"]
            _log.info("Re-authenticated user dn '%s' from session", user_dn)

            request["user_dn"] = user_dn
            return await handler(request)

        raise web.HTTPFound("/login")

    app.add_routes(routes)
    app.middlewares.append(middleware)
