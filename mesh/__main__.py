"""Entry point for `python -m mesh`."""

from __future__ import annotations

import sys

from mesh.cli import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
