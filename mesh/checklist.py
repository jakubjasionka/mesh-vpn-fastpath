"""Generate a markdown deployment checklist for self-hosted headscale / Tailscale."""

from __future__ import annotations

DEFAULT_HOSTNAME = "headscale.example.net"
DEFAULT_PORT = 443
NEWLINE = chr(10)


def generate_checklist(
    hostname: str = DEFAULT_HOSTNAME,
    port: int = DEFAULT_PORT,
) -> str:
    """Generate a Markdown checklist for keeping a self-hosted mesh on direct paths.

    Uses documented port numbers and protocol behavior only.
    """
    clean_host = hostname.strip()
    if not clean_host:
        raise ValueError("hostname must not be empty.")
    if not (1 <= port <= 65535):
        raise ValueError(f"port must be between 1 and 65535 (got {port}).")

    lines = [
        f"# Self-Hosted Mesh Direct-Path Checklist (`{clean_host}:{port}`)",
        "",
        "## 1. Documented Inbound & Outbound Ports",
        "",
        (
            f"- [ ] **Control Plane & HTTPS (`TCP {port}`)**: Allow inbound `TCP {port}` on "
            f"`{clean_host}` for the headscale control plane API and TLS coordination "
            "(documented default: `TCP 443`)."
        ),
        (
            f"- [ ] **Embedded DERP Relay Fallback (`TCP 443`)**: If running an embedded DERP "
            f"relay on `{clean_host}`, allow inbound `TCP 443` for HTTPS-upgraded relay "
            "fallback traffic."
        ),
        (
            f"- [ ] **STUN Endpoint Discovery (`UDP 3478`)**: Allow inbound `UDP 3478` on "
            f"`{clean_host}` (or the configured DERP/STUN node) so peers can discover their "
            "external NAT mappings via STUN."
        ),
        (
            "- [ ] **WireGuard Direct Peer Traffic (`UDP 41641`)**: Allow inbound and outbound "
            "`UDP 41641` on edge nodes and peers (documented Tailscale WireGuard listen port) "
            "so peers can establish direct UDP tunnels without NAT hole-punching failures."
        ),
        "",
        "## 2. NAT & Firewall Notes",
        "",
        (
            "- [ ] **Endpoint-Independent NAT Mapping**: Prefer endpoint-independent NAT "
            "(Full Cone / Restricted Cone) on edge routers. Symmetric NAT on both sides "
            "prevents UDP hole punching and forces traffic onto DERP relays."
        ),
        (
            "- [ ] **Firewall State & UDP Pinholes**: Ensure the host firewall "
            "(`nftables` / `iptables` / `ufw`) permits inbound UDP on `41641` and outbound "
            "UDP to remote peer endpoints."
        ),
        (
            "- [ ] **Avoid Double NAT**: Place the edge box on a public IP or configure a "
            "static UDP port forward (`UDP 41641`) from the upstream router to the edge node."
        ),
        (
            "- [ ] **Path MTU & ICMP Packet Too Big**: Permit ICMP (IPv4 Fragmentation Needed "
            "and IPv6 Packet Too Big) across the firewall so Path MTU Discovery functions "
            "cleanly on direct WireGuard tunnels."
        ),
        "",
        "## 3. DNS Requirements",
        "",
        (
            f"- [ ] **Control Server Resolution**: Ensure `{clean_host}` resolves via public "
            "DNS (both `A` and `AAAA` records as applicable) on every peer before tunnel "
            "bring-up."
        ),
        (
            "- [ ] **Split DNS / MagicDNS Namespace**: Use a dedicated DNS zone (for example, "
            "`tailnet.example.net`) that does not collide with public domains required to "
            f"reach `{clean_host}`."
        ),
        (
            "- [ ] **Bootstrap DNS Availability**: Configure fallback upstream resolvers "
            "(`UDP 53` / `TCP 53`) on the edge node so control-plane hostname resolution "
            "succeeds even when the mesh interface is restarting."
        ),
        "",
        "## 4. Verify Direct Path",
        "",
        (
            "- [ ] **Inspect Peer Path Status**: Export the current status JSON and verify "
            "that peers report `direct=True` rather than a DERP relay region:"
        ),
        "  ```bash",
        "  tailscale status --json > status.json",
        "  python -m mesh status --file status.json",
        "  ```",
        (
            "- [ ] **Confirm Active Direct Tunnel**: Trigger traffic to the target peer and "
            "confirm via `tailscale status` that the peer transitions from a relay code to a "
            "direct UDP path."
        ),
        "",
    ]
    return NEWLINE.join(lines)
