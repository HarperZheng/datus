# Copyright 2025-present DatusAI, Inc.
# Licensed under the Apache License, Version 2.0.
# See http://www.apache.org/licenses/LICENSE-2.0 for details.

"""Unit tests for the in-process ClickHouse compatibility aspect (dosi engine)."""

import pytest

from datus.tools.semantic_tools.dosi.ch_compat import _rewrite_body, ensure_ch_compat, reroute_entry
from datus.tools.semantic_tools.dosi.config import DosiConfig
from datus.tools.semantic_tools.dosi.engine import EngineHandle


@pytest.mark.parametrize(
    "sql,expected",
    [
        ("SELECT dateTrunc('MONTH', pay_date) FROM t", "SELECT toStartOfMonth(pay_date) FROM t"),
        ("SELECT dateTrunc('month', a.b)", "SELECT toStartOfMonth(a.b)"),
        ("SELECT dateTrunc('week', toDateTime(d))", "SELECT toMonday(toDateTime(d))"),
        ("SELECT dateTrunc('quarter', d)", "SELECT toStartOfQuarter(d)"),
        ("SELECT dateTrunc('year', d)", "SELECT toStartOfYear(d)"),
        ("SELECT dateTrunc('day', d)", "SELECT toDate(d)"),
        # No match: body must pass through byte-identical.
        ("SELECT toDate(d) FROM t", "SELECT toDate(d) FROM t"),
        ("SELECT dateTrunc('month', '2024-01-01')", "SELECT dateTrunc('month', '2024-01-01')"),
    ],
)
def test_rewrite_body(sql: str, expected: str):
    assert _rewrite_body(sql.encode("utf-8")).decode("utf-8") == expected


def test_ensure_ch_compat_proxies_and_is_singleton():
    # Ephemeral localhost listener, one per upstream, reused on repeat calls.
    first = ensure_ch_compat("203.0.113.10", 8123)
    second = ensure_ch_compat("203.0.113.10", 8123)
    assert first == second
    assert first[0] == "127.0.0.1"
    assert isinstance(first[1], int) and first[1] > 0


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1", ""])
def test_local_hosts_pass_through(host: str):
    assert ensure_ch_compat(host, 8123) == (host, 8123)


def test_stale_compat_env_var_is_ignored(monkeypatch: pytest.MonkeyPatch):
    # DATUS_CH_COMPAT used to disable the aspect; a stale value in the
    # environment must not silently turn the proxy off (protection regression).
    monkeypatch.setenv("DATUS_CH_COMPAT", "off")
    first = ensure_ch_compat("203.0.113.11", 8123)
    assert first[0] == "127.0.0.1"
    assert isinstance(first[1], int) and first[1] > 0


def test_runtime_connections_rewrite_clickhouse_host():
    config = DosiConfig(
        datasource="ck",
        db_config={
            "type": "clickhouse",
            "host": "203.0.113.12",
            "port": "8123",
            "username": "u",
            "ch233_compat": True,
        },
    )
    connections = EngineHandle(config)._runtime_connections(config)
    entry = next(iter(connections.values()))
    # The aspect must reroute the engine's HTTP traffic to the in-process proxy.
    assert entry["host"] == "127.0.0.1"
    assert int(entry["port"]) > 0
    assert entry["port"] != "8123"
    # The opt-in switch must be stripped before the engine sees the entry.
    assert "ch233_compat" not in entry


def test_runtime_connections_keeps_clickhouse_without_opt_in():
    config = DosiConfig(
        datasource="ck",
        db_config={"type": "clickhouse", "host": "203.0.113.12", "port": "8123", "username": "u"},
    )
    connections = EngineHandle(config)._runtime_connections(config)
    entry = next(iter(connections.values()))
    assert entry["host"] == "203.0.113.12"
    assert entry["port"] == "8123"


def test_runtime_connections_keeps_non_clickhouse_host():
    config = DosiConfig(
        datasource="pg",
        db_config={"type": "postgresql", "host": "203.0.113.13", "port": "5432"},
    )
    connections = EngineHandle(config)._runtime_connections(config)
    entry = next(iter(connections.values()))
    assert entry["host"] == "203.0.113.13"
    assert entry["port"] == "5432"


def test_reroute_entry_defaults_off_without_switch():
    # Opt-in: absent ch233_compat keeps the native path.
    entry = {"type": "clickhouse", "host": "203.0.113.14", "port": 8123, "username": "u"}
    assert reroute_entry(entry) is entry
    assert entry["host"] == "203.0.113.14"


def test_reroute_entry_routes_enabled_remote_clickhouse():
    entry = {"type": "clickhouse", "host": "203.0.113.14", "port": 8123, "username": "u", "ch233_compat": True}
    rerouted = reroute_entry(entry)
    assert rerouted is not entry
    assert rerouted["host"] == "127.0.0.1"
    assert isinstance(rerouted["port"], int) and rerouted["port"] > 0
    assert "ch233_compat" not in rerouted  # switch never reaches the engine
    assert entry["ch233_compat"] is True  # input entry untouched


@pytest.mark.parametrize("value", ["off", "false", "no", "0", False])
def test_reroute_entry_falsy_switch_keeps_native_path(value):
    entry = {"type": "clickhouse", "host": "203.0.113.15", "port": 8123, "ch233_compat": value}
    rerouted = reroute_entry(entry)
    assert rerouted["host"] == "203.0.113.15"
    assert "ch233_compat" not in rerouted  # stripped even when disabled


@pytest.mark.parametrize("value", ["true", "on", "yes", "1", True])
def test_reroute_entry_truthy_switch_enables_proxy(value):
    entry = {"type": "clickhouse", "host": "203.0.113.16", "port": "8123", "ch233_compat": value}
    rerouted = reroute_entry(entry)
    assert rerouted["host"] == "127.0.0.1"
    assert isinstance(rerouted["port"], str) and int(rerouted["port"]) > 0
    assert "ch233_compat" not in rerouted


def test_reroute_entry_ignores_non_clickhouse():
    entry = {"type": "postgresql", "host": "203.0.113.17", "port": 5432}
    assert reroute_entry(entry) is entry


def test_reroute_entry_strips_switch_from_non_clickhouse():
    entry = {"type": "postgresql", "host": "203.0.113.17", "port": 5432, "ch233_compat": True}
    rerouted = reroute_entry(entry)
    assert rerouted["host"] == "203.0.113.17"
    assert "ch233_compat" not in rerouted


def test_reroute_entry_ignores_uri_backed_clickhouse():
    entry = {
        "type": "clickhouse",
        "uri": "clickhouse://203.0.113.18:8123/db",
        "host": "203.0.113.18",
        "ch233_compat": True,
    }
    rerouted = reroute_entry(entry)
    assert rerouted["host"] == "203.0.113.18"
    assert "ch233_compat" not in rerouted


def test_reroute_entry_local_host_passthrough():
    entry = {"type": "clickhouse", "host": "127.0.0.1", "port": 8123, "ch233_compat": True}
    rerouted = reroute_entry(entry)
    assert rerouted["host"] == "127.0.0.1"
    assert rerouted["port"] == 8123


def test_reroute_entry_db_type_override():
    # db_manager's adapter config dict drops the `type` key — the caller passes it.
    entry = {"host": "203.0.113.19", "port": 8123, "username": "u", "ch233_compat": True}
    rerouted = reroute_entry(entry, db_type="ClickHouse")  # case-insensitive
    assert rerouted["host"] == "127.0.0.1"
    assert isinstance(rerouted["port"], int) and rerouted["port"] > 0
    assert reroute_entry(entry, db_type="postgresql")["host"] == "203.0.113.19"
