from __future__ import annotations
from typing import Literal
from .. import connection, skill_runner
from ._base import mcp, skill_fn

_ROUTES = {
    "dividends": "get_corporate_actions_dividends",
    "buybacks": "get_corporate_actions_buybacks",
    "splits": "get_corporate_actions_stock_splits",
}


@mcp.tool()
def get_corporate_actions(code: str, action_type: Literal["dividends", "buybacks", "splits"]) -> dict:
    """Get corporate actions - 分红/派息/股息, 回购/buyback, or 拆股/合股/stock split.
    action_type selects which. Per-stock historical records; for a forward
    all-market dividend calendar use get_dividend_calendar instead.
    """
    fn_name = _ROUTES.get(action_type)
    if fn_name is None:
        return {"_skill_error": True,
                "error": f"action_type must be one of {list(_ROUTES)}, got {action_type!r}"}
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", fn_name), code)
