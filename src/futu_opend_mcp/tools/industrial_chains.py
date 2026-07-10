from __future__ import annotations
from typing import Literal
from .. import connection, skill_runner
from ._base import mcp, skill_fn

_CHAIN_ROUTES = {
    "list": "get_industrial_chain_list",
    "detail": "get_industrial_chain_detail",
    "by_plate": "get_industrial_chain_by_plate",
}
_PLATE_ROUTES = {"info": "get_industrial_plate_info", "stocks": "get_industrial_plate_stock"}


@mcp.tool()
def get_industrial_chains(
    market: str | None = None,
    view: Literal["list", "detail", "by_plate"] = "list",
    chain_id: int | None = None,
    plate_id: int | None = None,
    keyword: str | None = None,
    count: int = 20,
) -> dict:
    """Browse industrial/supply chains - 产业链. view: list (chains in a market, optional
    keyword), detail (one chain's upstream/midstream/downstream - pass chain_id), by_plate
    (chains linked to a plate - pass plate_id). market needed for list.
    """
    fn_name = _CHAIN_ROUTES.get(view)
    if fn_name is None:
        return {"_skill_error": True, "error": f"view must be {list(_CHAIN_ROUTES)}"}
    connection.get_context()
    if view == "list":
        return skill_runner._run_skill_json(skill_fn("quote", fn_name), market, keyword=keyword, count=count)
    if view == "detail":
        return skill_runner._run_skill_json(skill_fn("quote", fn_name), chain_id)
    return skill_runner._run_skill_json(skill_fn("quote", fn_name), plate_id)


@mcp.tool()
def get_industrial_plate(plate_id: int, view: Literal["info", "stocks"] = "info",
                         markets: str | None = None, count: int = 50) -> dict:
    """Industrial-plate info or constituents - 产业板块信息/成分股. view: info (plate detail) or
    stocks (constituents; optional markets filter like HK,US).
    """
    fn_name = _PLATE_ROUTES.get(view)
    if fn_name is None:
        return {"_skill_error": True, "error": f"view must be {list(_PLATE_ROUTES)}"}
    connection.get_context()
    if view == "info":
        return skill_runner._run_skill_json(skill_fn("quote", fn_name), plate_id)
    return skill_runner._run_skill_json(skill_fn("quote", fn_name), plate_id, markets=markets, count=count)
