# mesh-vpn-fastpath

Read-only Python standard-library utilities for keeping Tailscale and headscale (WireGuard-based) mesh VPN traffic on **direct UDP paths** instead of **DERP relays** on a small self-hosted edge box.

## Problem Statement: Direct Paths vs. DERP Relays

In a WireGuard-based mesh VPN coordinated by Tailscale or a self-hosted headscale control plane, peers exchange encrypted WireGuard frames using one of two transport paths:

1. **Direct Path (`CurAddr` populated)**: Peers establish an end-to-end UDP session (typically via STUN endpoint discovery and UDP hole punching on port `41641`). WireGuard packets travel directly between peer endpoints over UDP without intermediate payload proxies.
2. **Relayed Path (`Relay` populated, `CurAddr` empty)**: When restrictive NAT (such as bilateral symmetric NAT), firewall rules, or missing UDP pinholes prevent direct UDP reachability, traffic falls back to a **DERP (Designated Encrypted Relay for Packets)** server over `TCP 443` (HTTPS).

Why relayed paths degrade connectivity compared to direct paths:
- **Extra Routing Hop**: Every packet traverses the relay host instead of taking the shortest direct path between peers.
- **TCP-over-TCP Encapsulation**: Carrying encapsulated traffic over a TCP/TLS DERP stream introduces head-of-line blocking and outer TCP congestion control interactions.
- **Edge Box Resource Contention**: On a small self-hosted edge box running an embedded DERP relay or acting as a mesh gateway, user-space TLS relay forwarding consumes extra CPU and socket buffer resources compared to direct kernel/UDP WireGuard transport.

`mesh-vpn-fastpath` provides read-only tooling to audit whether peers are on direct paths, compute exact WireGuard inner MTU budgets, and generate a deployment checklist for self-hosted headscale environments.

## Architecture

```text
                       +-----------------------------------------+
                       |   Self-Hosted Control Plane / STUN      |
                       |        headscale.example.net            |
                       |   Control API & DERP Fallback: TCP 443  |
                       |   STUN Endpoint Discovery:     UDP 3478 |
                       +-------------------+---------------------+
                                           |
                  +------------------------+------------------------+
                  |  Slow Path: Relayed via DERP (TCP 443 / HTTPS)  |
                  v                                                 v
        +-------------------+                             +-------------------+
        |   Peer (node-a)   |                             |   Peer (node-b)   |
        |   Edge / Client   |<===========================>|   Remote Node     |
        +-------------------+    Fast Path: Direct UDP    +-------------------+
                  |              WireGuard (UDP 41641)
                  |
                  |  tailscale status --json (file or stdin)
                  v
        +---------------------------------------------------------------------+
        |                         mesh-vpn-fastpath                           |
        |                                                                     |
        |  +---------------+      +------------------+     +---------------+  |
        |  |  mesh status  |      |     mesh mtu     |     | mesh checklist|  |
        |  | Peer path     |      | Arithmetic inner |     | Ports, NAT,   |  |
        |  | classification|      | MTU budget       |     | DNS & verify  |  |
        |  | & redaction   |      | (IPv4 / IPv6)    |     | steps         |  |
        |  +---------------+      +------------------+     +---------------+  |
        +---------------------------------------------------------------------+
```

## Quick Start

Requires Python `>=3.11` and uses the Python standard library only (zero runtime dependencies).

```bash
# Inspect CLI help
python -m mesh --help

# 1. Classify peers from a saved tailscale status JSON file (hostnames redacted by default)
tailscale status --json > status.json
python -m mesh status --file status.json

# Opt-in to display peer hostnames (IP addresses are never printed)
python -m mesh status --file status.json --show-names

# 2. Compute inner WireGuard MTU budget for a given outer path MTU
python -m mesh mtu --outer-mtu 1500

# 3. Generate a self-hosted headscale direct-path checklist
python -m mesh checklist --hostname headscale.example.net --port 443
```

## Safety Notes

- **Read-Only Operation**: Does not modify system network interfaces, firewall rules, routing tables, or VPN daemon settings.
- **No Configuration Writes**: Reads JSON from a file or `stdin` by default. Does not invoke `tailscale` unless `--live` is explicitly passed to `mesh status`.
- **No Key or Token Handling**: Never reads, stores, or outputs private keys, pre-shared keys, auth tokens, or tailnet identifiers.
- **Privacy & Redaction by Default**:
  - Peer hostnames are replaced with a deterministic short SHA-256 hash (`peer-<8hex>`) unless `--show-names` is explicitly provided.
  - **IP addresses are never printed**: When `CurAddr` is present in `tailscale status --json`, `mesh status` strips the endpoint address and reports only `direct=True`.

## Benchmarks

**Not measured yet.**

To compare direct UDP path vs. DERP relayed path behavior on your own environment, follow this reproducible procedure and publish the raw tool outputs alongside hardware and kernel details:

1. **Confirm Baseline Path State**:
   - Export peer status and verify the target peer is on a direct path (`direct=True`):
     ```bash
     tailscale status --json > status-direct.json
     python -m mesh status --file status-direct.json
     ```
2. **Measure Direct Path RTT and Throughput**:
   - Measure round-trip time (RTT) using `ping` over the mesh interface toward the target peer (`node-b.tailnet.example.net`) and save the raw output:
     ```bash
     ping -c 30 node-b.tailnet.example.net > ping-direct.txt
     ```
   - Measure bulk TCP and UDP throughput using `iperf3` between the two peers and save the raw JSON output:
     ```bash
     # On node-b.tailnet.example.net:
     iperf3 -s -1
     # On node-a.tailnet.example.net:
     iperf3 -c node-b.tailnet.example.net -J > iperf3-direct.json
     ```
3. **Measure Relayed Path RTT and Throughput**:
   - Temporarily block direct UDP (`UDP 41641`) on the test peer firewall so traffic falls back to the DERP relay, then verify `Relayed peers: 1` via `python -m mesh status`:
     ```bash
     tailscale status --json > status-relayed.json
     python -m mesh status --file status-relayed.json
     ```
   - Repeat the identical `ping` and `iperf3` commands, saving `ping-relayed.txt` and `iperf3-relayed.json`.
4. **Publish Raw Output**:
   - Record the unmodified `ping` and `iperf3` outputs together with OS kernel version, WireGuard implementation, and outer link MTU.

## Limitations

- **Arithmetic-Only MTU Calculation**: `mesh mtu` computes inner MTU budgets purely from documented WireGuard protocol encapsulation constants (`60` bytes over IPv4 outer transport, `80` bytes over IPv6 outer transport). An active network `--probe` mode (such as Don't-Fragment ICMP-free packet probing) is not implemented.
- **No Active NAT Traversal**: This tool inspects `tailscale status --json` output and generates operator checklists; it does not send STUN requests or modify router NAT mappings.
- **Schema Scope**: `mesh status` evaluates the `Peer` map fields (`HostName`, `Online`, `CurAddr`, `Relay`) produced by `tailscale status --json`.

## Development

```bash
pip install -e ".[dev]"
ruff check .
mypy mesh
pytest -q
```

## License

MIT License. Copyright (c) 2026 Jakub Jasionka.
