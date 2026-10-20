# Copyright 2025-present DatusAI, Inc.
# Licensed under the Apache License, Version 2.0.
# See http://www.apache.org/licenses/LICENSE-2.0 for details.

"""In-process ClickHouse compatibility proxy for dosi-engine on CH <23.5.

dosi-engine's ClickHouse executor injects a ``session_timezone=UTC`` setting
that ClickHouse rejects before 23.5 (Code 115 UNKNOWN_SETTING), and its window
SQL uses the ``dateTrunc('<unit>', col)`` string-unit spelling that old servers
do not parse. This module runs a transparent reverse proxy as a daemon thread
inside the Datus process: lazily started per upstream, ephemeral port, gone
when the process exits — no standalone service to manage.
"""

import re
import threading
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional, Tuple

from datus.utils.loggings import get_logger

logger = get_logger(__name__)

_COMPAT_SWITCH_KEY = "ch233_compat"
_TRUTHY_SWITCH = {"true", "on", "yes", "1"}

_LISTEN_HOST = "127.0.0.1"
_STRIPPED_PARAMS = {"session_timezone"}
_GRAIN_TO_FUNC = {
    "YEAR": "toStartOfYear",
    "QUARTER": "toStartOfQuarter",
    "MONTH": "toStartOfMonth",
    "WEEK": "toMonday",
    "DAY": "toDate",
}
_DATE_TRUNC = re.compile(
    r"dateTrunc\(\s*'(week|day|month|quarter|year)'\s*,\s*([A-Za-z0-9_.()']+)\s*\)",
    re.IGNORECASE,
)
# Response headers that must survive the hop or the client misparses the body.
_PASSTHROUGH_RESPONSE_HEADERS = ("Content-Type", "Content-Encoding")

_lock = threading.Lock()
_proxies: Dict[Tuple[str, int], Tuple[str, int]] = {}  # (upstream_host, upstream_port) -> listen address


def _is_local(host: str) -> bool:
    return host.strip() in ("127.0.0.1", "localhost", "::1", "")


def _rewrite_body(body: bytes) -> bytes:
    """Rewrite dateTrunc string-unit calls into CH<23.5-compatible functions."""
    sql = _DATE_TRUNC.sub(
        lambda m: f"{_GRAIN_TO_FUNC[m.group(1).upper()]}({m.group(2)})",
        body.decode("utf-8", "replace"),
    )
    return sql.encode("utf-8")


def _make_handler(upstream_host: str, upstream_port: int):
    class _Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *args):
            pass

        def _proxy(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            query = [
                (k, v)
                for k, v in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
                if k not in _STRIPPED_PARAMS
            ]
            new_path = urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(query)))
            length = int(self.headers.get("Content-Length", 0) or 0)
            body = self.rfile.read(length) if length else None
            if body:
                body = _rewrite_body(body)
            request = urllib.request.Request(
                f"http://{upstream_host}:{upstream_port}{new_path}", data=body, method=self.command
            )
            for k, v in self.headers.items():
                if k.lower() not in ("host", "content-length"):
                    request.add_header(k, v)
            try:
                resp = urllib.request.urlopen(request, timeout=120)
                data, code = resp.read(), resp.status
                resp_headers = [(k, v) for k, v in resp.headers.items() if k in _PASSTHROUGH_RESPONSE_HEADERS]
            except urllib.error.HTTPError as exc:
                # ClickHouse errors must reach the engine verbatim.
                data, code = exc.read(), exc.code
                resp_headers = [(k, v) for k, v in exc.headers.items() if k in _PASSTHROUGH_RESPONSE_HEADERS]
            except Exception as exc:  # noqa: BLE001 - surfaced to the engine as a 502 body
                data, code = str(exc).encode("utf-8"), 502
                resp_headers = []
            self.send_response(code)
            for k, v in resp_headers:
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_POST(self) -> None:
            self._proxy()

        def do_GET(self) -> None:
            self._proxy()

    return _Handler


def ensure_ch_compat(host: str, port) -> Tuple[str, int]:
    """Aspect entry: return the (host, port) the engine should connect to.

    Non-local ClickHouse hosts are rerouted through the in-process proxy
    (strips session_timezone, rewrites dateTrunc); local addresses pass
    through untouched. Idempotent; one proxy thread per upstream. Opt-in:
    callers gate this via ``reroute_entry`` (the ``ch233_compat`` switch).
    """
    if _is_local(host):
        return host, int(port)
    key = (host.strip(), int(port))
    with _lock:
        entry = _proxies.get(key)
        if entry is None:
            server = ThreadingHTTPServer((_LISTEN_HOST, 0), _make_handler(*key))
            threading.Thread(
                target=server.serve_forever,
                daemon=True,
                name=f"ch-compat-proxy-{key[0]}:{key[1]}",
            ).start()
            entry = (_LISTEN_HOST, server.server_address[1])
            _proxies[key] = entry
            logger.info("CH compat proxy for %s:%s listening on 127.0.0.1:%s", key[0], key[1], entry[1])
        return entry


def reroute_entry(entry: Dict[str, Any], db_type: Optional[str] = None) -> Dict[str, Any]:
    """Single decision point for CH<23.5 compatibility routing.

    Callers hand in their connection vocabulary (an agent.yml datasource entry
    or an adapter config dict) and get back an entry whose host/port points at
    the in-process proxy when the entry opts in via ``ch233_compat: true`` and
    is a remote ClickHouse connection. The switch is opt-in: absent or falsy
    values keep the native path. Every rewrite rule, the strip list, and the
    local-host decision stay in this module — callers only ever swap the
    address, never touch SQL.

    The ``ch233_compat`` key is always stripped from the result: the native
    engine's connections vocabulary and ``ClickHouseConfig`` (pydantic
    ``extra="forbid"``) reject unknown fields.

    ``db_type`` overrides the entry's own ``type`` field, for callers whose
    config dict drops it (db_manager's adapter branch).
    """
    switch = entry.get(_COMPAT_SWITCH_KEY)
    enabled = str(switch).strip().lower() in _TRUTHY_SWITCH if switch is not None else False
    if _COMPAT_SWITCH_KEY in entry:
        # Work on a copy so the caller's dict is never mutated.
        entry = {k: v for k, v in entry.items() if k != _COMPAT_SWITCH_KEY}

    resolved_type = str(db_type if db_type is not None else entry.get("type") or "").strip().lower()
    if resolved_type != "clickhouse":
        return entry
    if not enabled:
        logger.info(
            "CH compat proxy skipped for %s (%s)",
            entry.get("host"),
            f"ch233_compat={switch}" if switch is not None else "ch233_compat not set",
        )
        return entry
    host = entry.get("host")
    if not host or entry.get("uri"):
        return entry
    port = str(entry.get("port") or "8123")
    proxy_host, proxy_port = ensure_ch_compat(str(host), port)
    if (proxy_host, int(proxy_port)) == (str(host), int(port)):
        return entry
    rerouted = dict(entry)
    rerouted["host"] = str(proxy_host)
    # Preserve the caller's port spelling (engine entries are strings, adapter
    # configs are ints) so downstream validation sees the shape it expects.
    rerouted["port"] = int(proxy_port) if isinstance(entry.get("port"), int) else str(proxy_port)
    return rerouted
