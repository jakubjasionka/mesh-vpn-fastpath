"""Stdlib TCP throughput probe. Run `recv` on one host and `send` on the other.

    python3 tcp_throughput.py recv --port 5299
    python3 tcp_throughput.py send --host <recv-host> --port 5299 --seconds 10
Prints one JSON line with bytes, seconds and Mbit/s measured on the sending side.
"""
import argparse
import json
import socket
import time

CHUNK = 1 << 20

def recv(port: int) -> None:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", port))
    srv.listen(1)
    conn, _ = srv.accept()
    while conn.recv(CHUNK):
        pass
    conn.close()
    srv.close()

def send(host: str, port: int, seconds: float) -> None:
    s = socket.create_connection((host, port), timeout=30)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    buf = b"\0" * CHUNK
    sent = 0
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < seconds:
        s.sendall(buf); sent += len(buf)
    elapsed = time.perf_counter() - t0
    s.close()
    print(json.dumps({"bytes": sent, "seconds": round(elapsed, 2),
                      "mbit_per_s": round(sent * 8 / elapsed / 1e6, 1)}))

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["recv", "send"])
    p.add_argument("--host", default="")
    p.add_argument("--port", type=int, default=5299)
    p.add_argument("--seconds", type=float, default=10.0)
    a = p.parse_args()
    if a.mode == "recv":
        recv(a.port)
    else:
        send(a.host, a.port, a.seconds)
