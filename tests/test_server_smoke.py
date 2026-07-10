def test_app_has_tools_registered():
    """Importing server must not crash and the FastMCP app must exist."""
    from futu_opend_mcp.tools import _base
    from futu_opend_mcp import server  # noqa
    # FastMCP exposes registered tools; tool count is asserted once categories exist.
    assert _base.mcp is not None


def test_main_is_callable():
    from futu_opend_mcp import server
    assert callable(server.main)


def test_tool_count():
    """All ~50 v1 tools are registered."""
    import asyncio
    from futu_opend_mcp.tools import _base
    from futu_opend_mcp import server  # noqa
    tools = asyncio.run(_base.mcp.list_tools())
    names = {t.name for t in tools}
    # We assert a representative floor; the exact set is the catalogue.
    assert len(names) >= 45, f"only {len(names)} tools registered: {sorted(names)}"
