# Measured results (single edge node, one run)

Node: Linux 5.15 vendor kernel, tailscale 1.102.2, headscale control plane (self-hosted).
Peers: 9 known, 1 online at the time of measurement.

## 1. Direct path RTT (peer reached over UDP, no relay)

Command: `tailscale ping --timeout 5s <peer>` x 30, sequential, 0.2 s apart.
Raw output: `direct_ping_30.txt` (peer names and addresses redacted).

| Samples | Path | p50 | p95 | min | max |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 30 | direct (30/30) | 48.0 ms | 51.0 ms | 44.0 ms | 63.0 ms |

## 2. DERP region RTT from this node

Command: `tailscale netcheck --format=json`, raw values converted to ms. See `derp_region_rtt.json`.
This measures the leg to each relay region from this node. It is **not** the RTT of a
peer-to-peer relayed path, which needs an online peer that is currently using a relay.

## Not measured

- **Relayed peer-to-peer RTT.** No online peer was on a relay at measurement time.
- **Throughput (direct or relayed).** Requires an iperf3 server on the remote peer, which this node does not control.

## Kernel prerequisites (checked, not measured)

On this kernel the following options are absent: `CONFIG_WIREGUARD`, `CONFIG_TUN`
(no `/dev/net/tun`), `CONFIG_CRYPTO_CURVE25519`, `CONFIG_CRYPTO_CHACHA20POLY1305`.
Tailscale therefore cannot use kernel WireGuard here. The `CONFIG_PSI` option is also absent.
