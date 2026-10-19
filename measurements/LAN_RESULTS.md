# Measured results: edge node <-> workstation on the same LAN (one run)

Path check before measuring: traffic to the workstation's LAN address leaves through the
physical interface, **not** through the tailscale interface, and no subnet routes are
advertised through the tailnet. So these numbers describe the plain LAN path, not a tailnet path.

## RTT (ICMP, 20 samples, LAN)

| Direction | min | avg | max |
| :--- | :--- | :--- | :--- |
| edge node -> workstation | 0.184 ms | 0.296 ms | 0.410 ms |

## TCP throughput (`tcp_throughput.py`, 10 s, 1 MiB writes, single stream)

| Direction | Throughput |
| :--- | :--- |
| workstation -> edge node | 939.9 Mbit/s |
| edge node -> workstation | 940.9 Mbit/s |

The result sits at the usual goodput ceiling of a 1 Gbit/s Ethernet link, so the link
itself is the limit here, not the tailscale datapath.

## Not measured

- **Tailnet path to the workstation.** The workstation's node key has expired in the
  headscale control plane (`peer's node key has expired`). It must log in again before
  tailnet throughput or RTT can be measured.
- **Relayed (DERP) peer-to-peer path.** Requires a second online peer that is actually relaying.
