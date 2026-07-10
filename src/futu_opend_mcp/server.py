"""FastMCP server entry point. Runs over stdio."""
from __future__ import annotations

import logging

from .tools import _base  # noqa: F401  (registers tools)
from .tools import register_all  # noqa: F401


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    register_all()
    _base.mcp.run()


if __name__ == "__main__":
    main()
