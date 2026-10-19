"""Unit tests for `mesh.status` using a synthetic parser fixture.

Note: The JSON payload in this module is strictly a synthetic parser fixture
for unit-testing classification and redaction logic. It is not a claim about
any real network deployment.
"""

from __future__ import annotations

import json

import pytest

from mesh.status import (
     format_status_summary,
    parse_status_json,
    redact_hostname,
)

SYNTHETIC_STATUS_FIXTURE = json.dumps(
    {
        "Peer": {
            "peer-key-1": {
                "HostName": "node-a",
                "Online": True,
                "CurAddr": "192.0.2.10:41641",
                "Relay": "derp-a",
            },
            "peer-key-2": {
                "HostName": "node-b",
                "Online": True,
                "CurAddr": "",
                "Relay": "derp-b",
            },
            "peer-key-3": {
                "HostName": "node-c",
                "Online": False,
                "CurAddr": "",
                "Relay": "derp-a",
            },
        }
    }
)


def test_parse_status_classification_and_redaction() -> None:
    """Synthetic parser fixture test: classify direct, relayed, and offline peers."""
    summary = parse_status_json(SYNTHETIC_STATUS_FIXTURE, show_names=False)

    assert summary.total_peers == 3
    assert summary.direct_count == 1
    assert summary.relayed_count == 1
    assert summary.offline_count == 1
    assert summary.relay_regions == ["derp-b"]

    identifiers = {p.identifier for p in summary.peers}
    assert "node-a" not in identifiers
    assert "node-b" not in identifiers
    assert "node-c" not in identifiers
    assert redact_hostname("node-a") in identifiers

    formatted = format_status_summary(summary)
    assert "192.0.2.10" not in formatted
    assert "Direct peers:  1" in formatted
    assert "Relayed peers: 1" in formatted
    assert "Offline peers: 1" in formatted
    assert "Relay regions: derp-b" in formatted


def test_parse_status_show_names_opt_in() -> None:
    """Synthetic parser fixture test: `--show-names` preserves fake hostnames only."""
    summary = parse_status_json(SYNTHETIC_STATUS_FIXTURE, show_names=True)
    by_name = {p.identifier: p for p in summary.peers}

    assert set(by_name.keys()) == {"node-a", "node-b", "node-c"}
    assert by_name["node-a"].state == "direct"
    assert by_name["node-a"].direct is True
    assert by_name["node-a"].relay == ""

    assert by_name["node-b"].state == "relayed"
    assert by_name["node-b"].direct is False
    assert by_name["node-b"].relay == "derp-b"

    assert by_name["node-c"].state == "offline"
    assert by_name["node-c"].direct is False
    assert by_name["node-c"].online is False

    formatted = format_status_summary(summary)
    assert "192.0.2.10" not in formatted
    assert "node-a: state=direct direct=True" in formatted
    assert "node-b: state=relayed direct=False relay=derp-b" in formatted
    assert "node-c: state=offline direct=False" in formatted


def test_parse_status_invalid_json_raises() -> None:
    """Verify invalid JSON raises ValueError."""
    with pytest.raises(ValueError, match="Invalid JSON input"):
        parse_status_json("{not-valid-json")
