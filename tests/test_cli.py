"""Unit tests for the CLI parser and subcommands in `mesh.cli`."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from mesh.cli import build_parser, main


def test_cli_parser_subcommands() -> None:
    """Verify `status`, `mtu`, and `checklist` subcommands parse expected flags."""
    parser = build_parser()

    args_status = parser.parse_args(["status", "--file", "status.json", "--show-names"])
    assert args_status.subcommand == "status"
    assert args_status.file_path == "status.json"
    assert args_status.show_names is True
    assert args_status.live is False

    args_mtu = parser.parse_args(["mtu", "--outer-mtu", "1500"])
    assert args_mtu.subcommand == "mtu"
    assert args_mtu.outer_mtu == 1500

    args_checklist = parser.parse_args(
        ["checklist", "--hostname", "example.net", "--port", "443"]
    )
    assert args_checklist.subcommand == "checklist"
    assert args_checklist.hostname == "example.net"
    assert args_checklist.port == 443


def test_cli_mtu_requires_outer_mtu() -> None:
    """Verify `mtu` subcommand requires `--outer-mtu` with no default."""
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["mtu"])


def test_cli_main_execution(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Run CLI subcommands end-to-end using a synthetic status file fixture."""
    fixture_file = tmp_path / "status.json"
    fixture_file.write_text(
        json.dumps(
            {
                "Peer": {
                    "k1": {
                        "HostName": "node-a",
                        "Online": True,
                        "CurAddr": "192.0.2.10:41641",
                        "Relay": "",
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    rc_status = main(["status", "--file", str(fixture_file)])
    out_status = capsys.readouterr().out
    assert rc_status == 0
    assert "Direct peers:  1" in out_status
    assert "192.0.2.10" not in out_status

    rc_mtu = main(["mtu", "--outer-mtu", "1500"])
    out_mtu = capsys.readouterr().out
    assert rc_mtu == 0
    assert "1420 bytes" in out_mtu

    rc_checklist = main(["checklist", "--hostname", "example.net", "--port", "443"])
    out_checklist = capsys.readouterr().out
    assert rc_checklist == 0
    assert "example.net:443" in out_checklist
