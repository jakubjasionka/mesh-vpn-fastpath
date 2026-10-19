"""Unit tests for self-hosted headscale checklist generation in `mesh.checklist`."""

from __future__ import annotations

import pytest

from mesh.checklist import generate_checklist


def test_generate_checklist_defaults() -> None:
    """Verify default checklist uses example.net and includes required sections."""
    markdown = generate_checklist()
    assert "headscale.example.net:443" in markdown
    assert "TCP 443" in markdown
    assert "UDP 3478" in markdown
    assert "UDP 41641" in markdown
    assert "NAT & Firewall Notes" in markdown
    assert "DNS Requirements" in markdown
    assert "tailnet.example.net" in markdown
    assert "Verify Direct Path" in markdown
    assert "tailscale status --json" in markdown


def test_generate_checklist_custom_parameters() -> None:
    """Verify custom RFC 2606 hostname and port are rendered into checklist."""
    markdown = generate_checklist(hostname="control.example.net", port=8443)
    assert "control.example.net:8443" in markdown
    assert "TCP 8443" in markdown


def test_generate_checklist_validation() -> None:
    """Verify empty hostname or out-of-range port raises ValueError."""
    with pytest.raises(ValueError, match="hostname must not be empty"):
        generate_checklist(hostname="   ", port=443)

    with pytest.raises(ValueError, match="port must be between 1 and 65535"):
        generate_checklist(hostname="example.net", port=70000)
