"""Register all tool categories onto the shared FastMCP singleton.

Each category module registers its tools via @mcp.tool on import. We import
them defensively during scaffolding so the package stays importable before all
categories exist; once every module is present the try/excepts are no-ops.
"""
_CATEGORIES = [
    "quote", "search", "financials", "research", "corporate_actions",
    "shareholders", "profile", "capital", "short", "options", "derivatives",
    "plates", "industrial_chains", "institutions", "macro", "dividends",
    "ipo", "diagnostics",
]

_missing: list[str] = []
for _name in _CATEGORIES:
    try:
        __import__(f"{__name__}.{_name}", fromlist=[_name])
    except ModuleNotFoundError:
        _missing.append(_name)


def register_all() -> None:
    """Importing the submodules above already registers tools via @mcp.tool.
    This function exists for explicitness at the call site. Raises if any
    category module is still missing."""
    if _missing:
        raise ImportError(
            f"tool categories not yet implemented: {_missing}. "
            f"Server cannot start until all are present."
        )
