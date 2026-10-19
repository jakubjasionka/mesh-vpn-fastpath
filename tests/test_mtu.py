"""Unit tests for WireGuard inner MTU arithmetic in `mesh.mtu`."""

from __future__ import annotations

import pytest

from mesh.mtu import (
    IPV4_HEADER_BYTES,
    IPV6_HEADER_BYTES,
    IPV6_MIN_MTU,
    UDP_HEADER_BYTES,
    WG_IPV4_OVERHEAD_BYTES,
    WG_IPV6_OVERHEAD_BYTES,
    WIREGUARD_FRAME_BYTES,
    calculate_mtu_budget,
    format_mtu_budget,
)


def test_overhead_constants_match_wireguard_spec() -> None:
    """Verify per-packet overhead constants match documented WireGuard framing."""
    assert IPV4_HEADER_BYTES == 20
    assert IPV6_HEADER_BYTES == 40
    assert UDP_HEADER_BYTES == 8
    assert WIREGUARD_FRAME_BYTES == 32
    assert WG_IPV4_OVERHEAD_BYTES == 60
    assert WG_IPV6_OVERHEAD_BYTES == 80
    assert IPV6_MIN_MTU == 1280


def test_calculate_mtu_standard_ethernet() -> None:
    """For outer MTU 1500, inner MTUs are 1440 (IPv4) and 1420 (IPv6)."""
    budget = calculate_mtu_budget(1500)
    assert budget.outer_mtu == 1500
    assert budget.inner_ipv4_mtu == 1500 - 60 == 1440
    assert budget.inner_ipv6_mtu == 1500 - 80 == 1420
    assert budget.recommended_mtu == 1420
    assert budget.below_ipv6_minimum is False

    output = format_mtu_budget(budget)
    assert "1440 bytes" in output
    assert "1420 bytes" in output
    assert "WARNING" not in output


def test_calculate_mtu_warns_below_ipv6_minimum() -> None:
    """For outer MTU 1340, IPv6 inner MTU is 1260 (< 1280) and triggers warning."""
    budget = calculate_mtu_budget(1340)
    assert budget.inner_ipv4_mtu == 1340 - 60 == 1280
    assert budget.inner_ipv6_mtu == 1340 - 80 == 1260
    assert budget.recommended_mtu == 1260
    assert budget.below_ipv6_minimum is True

    output = format_mtu_budget(budget)
    assert "WARNING" in output
    assert "1280 bytes" in output


def test_calculate_mtu_rejects_too_small_outer_mtu() -> None:
    """Outer MTU <= 80 bytes raises ValueError."""
    with pytest.raises(ValueError, match="outer_mtu must be greater than 80"):
        calculate_mtu_budget(80)
