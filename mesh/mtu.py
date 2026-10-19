"""Compute inner WireGuard MTU budgets from a given outer path MTU.

Citation:
WireGuard protocol documentation (https://www.wireguard.com/protocol/) and the
Linux kernel WireGuard driver (`drivers/net/wireguard/device.c`) define the
per-packet encapsulation overhead:
- Outer IPv4 header: 20 bytes
- Outer IPv6 header: 40 bytes
- Outer UDP header: 8 bytes
- WireGuard transport data header and AEAD authentication tag:
  - 4 bytes message type (1 byte) + reserved zeros (3 bytes)
  - 4 bytes receiver index
  - 8 bytes packet counter (nonce)
  - 16 bytes Poly1305 authentication tag
  Total WireGuard protocol framing overhead = 32 bytes.

Combined per-packet encapsulation overhead:
- WireGuard over IPv4 outer transport: 20 + 8 + 32 = 60 bytes
- WireGuard over IPv6 outer transport: 40 + 8 + 32 = 80 bytes

Minimum IPv6 link MTU (RFC 8200 Section 5): 1280 bytes.
"""

from __future__ import annotations

from dataclasses import dataclass

IPV4_HEADER_BYTES = 20
IPV6_HEADER_BYTES = 40
UDP_HEADER_BYTES = 8
WIREGUARD_FRAME_BYTES = 32

WG_IPV4_OVERHEAD_BYTES = IPV4_HEADER_BYTES + UDP_HEADER_BYTES + WIREGUARD_FRAME_BYTES  # 60
WG_IPV6_OVERHEAD_BYTES = IPV6_HEADER_BYTES + UDP_HEADER_BYTES + WIREGUARD_FRAME_BYTES  # 80

IPV6_MIN_MTU = 1280
NEWLINE = chr(10)


@dataclass(frozen=True)
class MtuBudget:
    """Calculated WireGuard inner MTU budget for IPv4 and IPv6 outer transports."""

    outer_mtu: int
    inner_ipv4_mtu: int
    inner_ipv6_mtu: int
    recommended_mtu: int
    below_ipv6_minimum: bool


def calculate_mtu_budget(outer_mtu: int) -> MtuBudget:
    """Compute inner WireGuard MTU values for IPv4 and IPv6 outer transport.

    Raises ValueError if `outer_mtu` is not large enough to accommodate the
    80-byte WireGuard-over-IPv6 encapsulation overhead.
    """
    if outer_mtu <= WG_IPV6_OVERHEAD_BYTES:
        raise ValueError(
            f"outer_mtu must be greater than {WG_IPV6_OVERHEAD_BYTES} bytes "
            f"(got {outer_mtu})."
        )

    inner_ipv4 = outer_mtu - WG_IPV4_OVERHEAD_BYTES
    inner_ipv6 = outer_mtu - WG_IPV6_OVERHEAD_BYTES
    recommended = inner_ipv6
    below_min = inner_ipv4 < IPV6_MIN_MTU or inner_ipv6 < IPV6_MIN_MTU

    return MtuBudget(
        outer_mtu=outer_mtu,
        inner_ipv4_mtu=inner_ipv4,
        inner_ipv6_mtu=inner_ipv6,
        recommended_mtu=recommended,
        below_ipv6_minimum=below_min,
    )


def format_mtu_budget(budget: MtuBudget) -> str:
    """Format the calculated MTU budget and emit a warning if below 1280 bytes."""
    lines = [
        "WireGuard Inner MTU Budget",
        "==========================",
        f"Outer path MTU:                  {budget.outer_mtu} bytes",
        f"WireGuard over IPv4 overhead:    {WG_IPV4_OVERHEAD_BYTES} bytes",
        f"WireGuard over IPv6 overhead:    {WG_IPV6_OVERHEAD_BYTES} bytes",
        f"Inner MTU (IPv4 outer transport): {budget.inner_ipv4_mtu} bytes",
        f"Inner MTU (IPv6 outer transport): {budget.inner_ipv6_mtu} bytes",
        f"Recommended interface MTU:       {budget.recommended_mtu} bytes",
    ]
    if budget.below_ipv6_minimum:
        lines.append(
            f"WARNING: Calculated inner MTU ({budget.recommended_mtu} bytes) is below "
            f"the IPv6 minimum link MTU of {IPV6_MIN_MTU} bytes (RFC 8200)."
        )
    return NEWLINE.join(lines)
