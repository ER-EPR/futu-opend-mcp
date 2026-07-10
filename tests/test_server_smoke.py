def test_app_has_tools_registered():
    """Importing server must not crash and the FastMCP app must exist."""
    from futu_opend_mcp.tools import _base
    from futu_opend_mcp import server  # noqa
    # FastMCP exposes registered tools; tool count is asserted once categories exist.
    assert _base.mcp is not None


def test_main_is_callable():
    from futu_opend_mcp import server
    assert callable(server.main)
