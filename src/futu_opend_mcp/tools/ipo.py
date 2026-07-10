from __future__ import annotations
from .. import connection, skill_runner
from ._base import mcp, skill_fn


@mcp.tool()
def get_ipo_list(market: str) -> dict:
    """Get IPO list for a market - IPO/新股列表. market: HK/US/SH/SZ/SG/MY/JP."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_ipo_list"), market)
