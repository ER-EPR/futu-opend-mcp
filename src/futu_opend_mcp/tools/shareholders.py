from __future__ import annotations
from typing import Literal
from .. import connection, skill_runner
from ._base import mcp, skill_fn


@mcp.tool()
def get_shareholder_overview(code: str, period_id: int = 0) -> dict:
    """Shareholding structure summary - 持股统计/主要股东/股权结构/shareholder overview."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_shareholders_overview"), code, period_id=period_id)


@mcp.tool()
def get_holding_changes(code: str, filter_type: int = 0, num: int = 10) -> dict:
    """Shareholder holding changes (increase/decrease/new/clear) - 持股变动/增持/减持/
    新进/清仓. filter_type: 0=all 1=increase 2=decrease 3=new 4=clear.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_shareholders_holding_changes"), code, filter_type=filter_type, num=num)


@mcp.tool()
def get_holder_detail(code: str, request_type: int = 0, num: int = 10) -> dict:
    """Top-10 / detailed shareholders - 持股明细/十大股东/大股东名单. request_type 0=default 1000=all."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_shareholders_holder_detail"), code, request_type=request_type, num=num)


@mcp.tool()
def get_institutional_holdings(code: str, num: int = 10) -> dict:
    """By-stock institutional holdings history - 机构持股/机构持仓/13F (who holds THIS stock).
    For by-institution (which stocks an institution holds) use get_institution_holdings.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_shareholders_institutional"), code, num=num)


_INSIDER_ROUTES = {"holders": "get_insider_holder_list", "trades": "get_insider_trade_list"}


@mcp.tool()
def get_insider_data(code: str, data_type: Literal["holders", "trades"],
                     holder_id: int = 0, num: int = 10) -> dict:
    """US insider holdings/trades - 内部人持股/内部人交易/高管交易/Form 4. US stocks only.
    data_type: holders (insider holder list) or trades (insider trade list).
    """
    fn_name = _INSIDER_ROUTES.get(data_type)
    if fn_name is None:
        return {"_skill_error": True, "error": f"data_type must be {list(_INSIDER_ROUTES)}"}
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", fn_name), code, holder_id=holder_id, num=num)
