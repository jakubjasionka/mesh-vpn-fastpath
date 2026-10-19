"""Command-line interface for mesh-vpn-fastpath."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from mesh.checklist import DEFAULT_HOSTNAME, DEFAULT_PORT, generate_checklist
from mesh.mtu import calculate_mtu_budget, format_mtu_budget
from mesh.status import format_status_summary, load_status_input, parse_status_json


def build_parser() -> argparse.ArgumentParser:
    """Create the top-level argument parser and subcommands."""
    parser = argparse.ArgumentParser(
        prog="mesh",
        description=(
            "Read-only diagnostics and checklist tools for keeping WireGuard-based "
            "mesh VPN (Tailscale / headscale) traffic on direct paths."
        ),
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # status subcommand
    status_parser = subparsers.add_parser(
        "status",
        help="Parse `tailscale status --json` and classify peer paths.",
    )
    status_parser.add_argument(
        "--file",
        "-f",
        dest="file_path",
        default=None,
        help="Path to `tailscale status --json` output file (defaults to stdin).",
    )
    status_parser.add_argument(
        "--live",
        action="store_true",
        help="Invoke `tailscale status --json` directly instead of reading a file/stdin.",
    )
    status_parser.add_argument(
        "--show-names",
        action="store_true",
        help="Show peer hostnames instead of redacted short hashes.",
    )

    # mtu subcommand
    mtu_parser = subparsers.add_parser(
        "mtu",
        help="Calculate inner WireGuard MTU budget from an outer path MTU.",
    )
    mtu_parser.add_argument(
        "--outer-mtu",
        type=int,
        required=True,
        help="Outer transport path MTU in bytes (required, no default).",
    )

    # checklist subcommand
    checklist_parser = subparsers.add_parser(
        "checklist",
        help="Generate a Markdown direct-path checklist for a self-hosted deployment.",
    )
    checklist_parser.add_argument(
        "--hostname",
        "--server-hostname",
        dest="hostname",
        default=DEFAULT_HOSTNAME,
        help=f"Control plane hostname (default: {DEFAULT_HOSTNAME}).",
    )
    checklist_parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Control plane HTTPS port (default: {DEFAULT_PORT}).",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return an exit status code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.subcommand == "status":
            raw_json = load_status_input(file_path=args.file_path, live=args.live)
            summary = parse_status_json(raw_json, show_names=args.show_names)
            print(format_status_summary(summary))
            return 0

        if args.subcommand == "mtu":
            budget = calculate_mtu_budget(args.outer_mtu)
            print(format_mtu_budget(budget))
            return 0

        if args.subcommand == "checklist":
            output = generate_checklist(hostname=args.hostname, port=args.port)
            print(output, end="")
            return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0
