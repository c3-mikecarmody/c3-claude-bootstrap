"""python -m swat_memory → launch stdio MCP server."""
from __future__ import annotations

from .server import run


def main() -> int:
    run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
