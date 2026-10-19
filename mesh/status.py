"""Parse and classify peer connection paths from `tailscale status --json`."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

PeerState = Literal["direct", "relayed", "offline"]
NEWLINE = chr(10)


@dataclass(frozen=True)
class PeerStatus:
    """Classified connection status for a single mesh peer without IP addresses."""

    identifier: str
    state: PeerState
    direct: bool
    relay: str
    online: bool


@dataclass(frozen=True)
class StatusSummary:
    """Aggregate summary of peer path classifications."""

    total_peers: int
    direct_count: int
    relayed_count: int
    offline_count: int
    relay_regions: list[str]
    peers: list[PeerStatus]


def redact_hostname(hostname: str) -> str:
    """Return a deterministic short hash identifier for a hostname."""
    normalized = hostname.strip() or "unknown"
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:8]
    return f"peer-{digest}"


def classify_peer(
    peer_data: dict[str, Any],
    fallback_key: str = "unknown",
    *,
    show_names: bool = False,
) -> PeerStatus:
    """Classify a single peer entry from `tailscale status --json`.

    Classification rules:
    - offline: `Online` is false (or missing).
    - direct: `Online` is true and `CurAddr` is non-empty.
    - relayed: `Online` is true, `CurAddr` is empty, and `Relay` is non-empty.
    Never retains or outputs IP addresses from `CurAddr` or `TailscaleIPs`.
    """
    raw_name = str(peer_data.get("HostName") or fallback_key).strip() or "unknown"
    identifier = raw_name if show_names else redact_hostname(raw_name)

    online = bool(peer_data.get("Online", False))
    cur_addr = str(peer_data.get("CurAddr") or "").strip()
    relay = str(peer_data.get("Relay") or "").strip()

    if not online:
        state: PeerState = "offline"
        is_direct = False
    elif cur_addr:
        state = "direct"
        is_direct = True
    elif relay:
        state = "relayed"
        is_direct = False
    else:
        state = "offline"
        is_direct = False

    return PeerStatus(
        identifier=identifier,
        state=state,
        direct=is_direct,
        relay=relay if state == "relayed" else "",
        online=online,
    )


def parse_status_json(raw_json: str, *, show_names: bool = False) -> StatusSummary:
    """Parse raw JSON text from `tailscale status --json` and classify all peers."""
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON input: {exc}") from exc

    if not isinstance(payload, dict):
        raise ValueError("Expected top-level JSON object from tailscale status.")

    peer_map = payload.get("Peer") or {}
    if not isinstance(peer_map, dict):
        raise ValueError("Expected 'Peer' field to be a JSON object.")

    peers: list[PeerStatus] = []
    for idx, (_key, peer_obj) in enumerate(peer_map.items(), start=1):
        if isinstance(peer_obj, dict):
            peers.append(
                classify_peer(
                    peer_obj,
                    fallback_key=f"peer-{idx}",
                    show_names=show_names,
                )
            )

    peers.sort(key=lambda p: p.identifier)

    direct_count = sum(1 for p in peers if p.state == "direct")
    relayed_count = sum(1 for p in peers if p.state == "relayed")
    offline_count = sum(1 for p in peers if p.state == "offline")
    relay_regions = sorted({p.relay for p in peers if p.relay})

    return StatusSummary(
        total_peers=len(peers),
        direct_count=direct_count,
        relayed_count=relayed_count,
        offline_count=offline_count,
        relay_regions=relay_regions,
        peers=peers,
    )


def load_status_input(file_path: str | None = None, *, live: bool = False) -> str:
    """Load `tailscale status --json` payload from a file, `--live` command, or stdin."""
    if live and file_path:
        raise ValueError("Cannot specify both --file and --live.")

    if live:
        proc = subprocess.run(
            ["tailscale", "status", "--json"],
            capture_output=True,
            text=True,
            check=True,
        )
        return proc.stdout

    if file_path and file_path != "-":
        return Path(file_path).read_text(encoding="utf-8")

    return sys.stdin.read()


def format_status_summary(summary: StatusSummary) -> str:
    """Format a human-readable summary without exposing any IP addresses."""
    regions_str = ", ".join(summary.relay_regions) if summary.relay_regions else "none"
    lines = [
        "Mesh Peer Path Summary",
        "======================",
        f"Total peers:   {summary.total_peers}",
        f"Direct peers:  {summary.direct_count}",
        f"Relayed peers: {summary.relayed_count}",
        f"Offline peers: {summary.offline_count}",
        f"Relay regions: {regions_str}",
    ]
    if summary.peers:
        lines.append("")
        lines.append("Peers:")
        for peer in summary.peers:
            relay_info = f" relay={peer.relay}" if peer.relay else ""
            lines.append(
                f"  - {peer.identifier}: state={peer.state} direct={peer.direct}{relay_info}"
            )
    return NEWLINE.join(lines)
