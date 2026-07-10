from __future__ import annotations
from typing import Literal
from .. import connection, skill_runner
from ._base import mcp, skill_fn

_MACRO_ROUTES = {"list": "get_macro_indicator_list", "history": "get_macro_indicator_history"}
_FED_ROUTES = {"target_rate": "get_fed_watch_target_rate", "dot_plot": "get_fed_watch_dot_plot"}


@mcp.tool()
def get_economic_calendar(market: str | None = None, date: str | None = None,
                          max_count: int = 50) -> dict:
    """Economic-event calendar - 经济事件日历. Optional market + date filter."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_economic_calendar"), market, date=date, max_count=max_count)


@mcp.tool()
def get_macro_indicator(view: Literal["list", "history"] = "list",
                        indicator_id: int | None = None,
                        begin: str | None = None, end: str | None = None,
                        search: str | None = None) -> dict:
    """Macro indicators - 宏观指标. view: list (available indicators, optional search) or
    history (time series for an indicator_id, optional begin/end).
    """
    fn_name = _MACRO_ROUTES.get(view)
    if fn_name is None:
        return {"_skill_error": True, "error": f"view must be {list(_MACRO_ROUTES)}"}
    connection.get_context()
    if view == "list":
        return skill_runner._run_skill_json(skill_fn("quote", fn_name), search=search)
    return skill_runner._run_skill_json(skill_fn("quote", fn_name), indicator_id, begin=begin, end=end)


@mcp.tool()
def get_fed_watch(view: Literal["target_rate", "dot_plot"] = "target_rate") -> dict:
    """CME FedWatch tool - FedWatch 目标利率概率 (target_rate) or 点阵图 (dot_plot)."""
    fn_name = _FED_ROUTES.get(view)
    if fn_name is None:
        return {"_skill_error": True, "error": f"view must be {list(_FED_ROUTES)}"}
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", fn_name))
