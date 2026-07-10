from __future__ import annotations
from .. import connection, skill_runner
from ._base import mcp, skill_fn


@mcp.tool()
def get_plate_list(market: str, plate_type: str = "CONCEPT",
                   keyword: str | None = None, count: int = 50) -> dict:
    """List plates (concept/industry/region) - 板块列表/概念板块/行业板块. market: HK/US/SH/SZ/
    SG/MY/JP. plate_type: ALL/INDUSTRY/REGION/CONCEPT.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_plate_list"), market, plate_type=plate_type, keyword=keyword, count=count)


@mcp.tool()
def get_plate_stocks(plate_code: str, limit: int = 30) -> dict:
    """Get stocks in a plate or index - 板块成分股/指数成分股/恒指成分股. plate_code e.g. hsi
    (alias) or HK.BK1910.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_plate_stock"), plate_code, limit=limit)


@mcp.tool()
def get_owner_plate(codes: list[str]) -> dict:
    """Get plates a stock belongs to - 所属板块/属于哪些板块."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_owner_plate"), codes)
