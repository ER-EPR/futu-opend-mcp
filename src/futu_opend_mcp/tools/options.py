from __future__ import annotations
from typing import Literal
from .. import connection, skill_runner
from ._base import mcp, skill_fn

_UNDERLYING_ROUTES = {
    "volatility": "get_option_underlying_his_volatility",
    "statistic": "get_option_underlying_his_statistic",
    "overview": "get_option_underlying_overview",
}


@mcp.tool()
def resolve_option_code(underlying: str, expiry: str, strike: float,
                        option_type: Literal["CALL", "PUT"]) -> dict:
    """Resolve an option's Futu code from a description - 解析期权简写代码. underlying e.g.
    US.JPM; expiry YYYY-MM-DD; strike e.g. 267.50; option_type CALL/PUT. Returns a code like
    US.JPM260320C267500. Do NOT hand-build HK option codes (abbreviation differs) - use this.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "resolve_option_code"), underlying, expiry, strike, option_type)


@mcp.tool()
def get_option_chain(underlying: str, start: str | None = None,
                     end: str | None = None) -> dict:
    """Get option chain for an underlying - 期权链. HK/US stocks/ETF/index only.
    start/end YYYY-MM-DD filter by expiry.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_option_chain"), underlying, start=start, end=end)


@mcp.tool()
def get_option_expiration_date(underlying: str) -> dict:
    """List option expiration dates - 期权到期日. HK/US stocks/ETF/index only."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_option_expiration_date"), underlying)


@mcp.tool()
def get_option_quote(legs: list[dict]) -> dict:
    """Get option snapshot/Greeks for one or more legs - 期权快照/期权实时行情/多腿Greeks.
    legs: [{code, action: BUY|SELL, quantity}]. NOT for combo bid/ask - use get_option_strategy_analysis.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_option_quote"), legs)


@mcp.tool()
def get_option_volatility(code: str, query_time_period: int = 2,
                          hv_time_period: int = 30) -> dict:
    """Option volatility analysis (IV/HV) for a single option contract - 期权波动率/隐含波动率/
    IV/HV. Input is an OPTION code (resolve via resolve_option_code first). query_time_period:
    1=week 2=month 3=quarter 4=half 5=year.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_option_volatility"), code, query_time_period=query_time_period, hv_time_period=hv_time_period)


@mcp.tool()
def get_option_strategy_analysis(legs: list[dict]) -> dict:
    """Combo option bid1/ask1 + P&L analysis - 组合摆盘价/损益分析/最大盈亏/盈亏平衡点.
    legs: [{code, action: BUY|SELL, quantity}]. PREFERRED source for combo bid/ask; do NOT
    sum single-leg snapshots.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_option_strategy_analysis"), legs)


@mcp.tool()
def get_option_underlying(
    code: list[str] | str,
    view: Literal["volatility", "statistic", "overview"],
    begin: str | None = None,
    end: str | None = None,
) -> dict:
    """Option-underlying IV/HV data - 标的历史波动率/IV走势/P-C比率/批量标的快照.
    view: volatility (IV+HV time series, single code), statistic (volume/OI/PCR time series,
    single code), overview (latest snapshot, MULTIPLE codes). For overview pass a list; for
    volatility/statistic pass a single code + begin/end (≤364 days).
    """
    fn_name = _UNDERLYING_ROUTES.get(view)
    if fn_name is None:
        return {"_skill_error": True, "error": f"view must be {list(_UNDERLYING_ROUTES)}"}
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", fn_name), code, begin=begin, end=end)
