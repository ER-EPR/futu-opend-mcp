from __future__ import annotations
from typing import Literal
from .. import connection, skill_runner
from ._base import mcp, skill_fn

_HOLDING_ROUTES = {"list": "get_institution_holding_list", "change": "get_institution_holding_change"}


@mcp.tool()
def get_institution_list(market: str, name: str | None = None, count: int = 20) -> dict:
    """List institutions in a market - 机构列表. Optional name fuzzy search (e.g. 桥水/Bridgewater).
    Returns institution_id usable in other institution tools.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_institution_list"), market, name=name, count=count)


@mcp.tool()
def get_institution_profile(market: str, institution_id: int) -> dict:
    """Institution profile - 机构概况/机构详情."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_institution_profile"), market, institution_id)


@mcp.tool()
def get_institution_holdings(market: str, institution_id: int,
                             view: Literal["list", "change"] = "list",
                             change_type: str | None = None, num: int = 20) -> dict:
    """By-institution holdings - 机构持股/持仓变动. view: list (an institution's holdings) or
    change (holding-change detail). change_type for change: NEW/INCREASE/DECREASE/CLEAR. This is
    the BY-INSTITUTION direction (which stocks an institution holds) - distinct from
    get_institutional_holdings (who holds a given stock).
    """
    fn_name = _HOLDING_ROUTES.get(view)
    if fn_name is None:
        return {"_skill_error": True, "error": f"view must be {list(_HOLDING_ROUTES)}"}
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", fn_name), market, institution_id, change_type=change_type, num=num)


@mcp.tool()
def get_institution_distribution(market: str, institution_id: int) -> dict:
    """Institution holding industry distribution - 机构持仓行业分布."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_institution_distribution"), market, institution_id)
