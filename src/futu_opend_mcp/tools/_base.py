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
    """Import and return an official skill function by module+name.

    category: 'quote' (all v1 tools are quote). name: e.g. 'get_snapshot'.
    """
    if _SCRIPTS_DIR not in sys.path:
        sys.path.insert(0, _SCRIPTS_DIR)
    mod = importlib.import_module(name)
    return getattr(mod, name)
