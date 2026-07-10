"""Shared bits for tool modules: the FastMCP singleton + a thin import helper."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("futu-opend-mcp")

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "_skill" / "futuapi" / "scripts")


def skill_fn(category: str, name: str) -> Any:
    """Return a lazy callable for an official skill function by category+name.

    Official scripts live at _skill/futuapi/scripts/<category>/<name>.py and
    define a function also named <name>. category: 'quote' (all v1 tools are
    quote). name: e.g. 'get_snapshot'.

    Importing an official script triggers ``common.ensure_futu_api()`` at
    import time, which sys.exits if OpenD is unreachable. We therefore defer
    the import until the returned callable is actually invoked - by which point
    connection.get_context() has already patched common into a no-op. Callers
    pass the result straight to skill_runner._run_skill_json(...) without
    triggering the import.
    """
    def _lazy(*args, **kwargs):
        if _SCRIPTS_DIR not in sys.path:
            sys.path.insert(0, _SCRIPTS_DIR)
        mod = importlib.import_module(f"{category}.{name}")
        return getattr(mod, name)(*args, **kwargs)

    _lazy.__name__ = name
    _lazy._skill_target = (category, name)
    return _lazy
