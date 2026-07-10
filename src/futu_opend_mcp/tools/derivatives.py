from __future__ import annotations
from .. import connection, skill_runner
from ._base import mcp, skill_fn


@mcp.tool()
def get_warrant(stock_owner: str = "") -> dict:
    """Get warrants/cbbc list for an underlying - 窝轮/牛熊证/warrant. stock_owner e.g. HK.00700."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_warrant"), stock_owner)


@mcp.tool()
def get_future_info(codes: list[str]) -> dict:
    """Get futures contract info (size, last trade day, sessions) - 期货合约信息. e.g. SG.CNmain."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_future_info"), codes)


@mcp.tool()
def get_reference_securities(code: str, reference_type: str = "WARRANT") -> dict:
    """Get securities related to a code (spot↔warrant/future/option) - 关联证券/正股关联涡轮期货.
    reference_type: WARRANT / FUTURE / OPTION (per SDK enum).
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_referencestock_list"), code, reference_type)
