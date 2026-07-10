from __future__ import annotations
from .. import connection, skill_runner
from ._base import mcp, skill_fn


@mcp.tool()
def get_capital_flow(code: str) -> dict:
    """Capital flow time series (main-force in/out) - 资金流向/资金流入流出."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_capital_flow"), code)


@mcp.tool()
def get_capital_distribution(code: str) -> dict:
    """Capital distribution (super/big/mid/small orders) - 资金分布/大单小单/主力资金."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_capital_distribution"), code)


@mcp.tool()
def get_top_brokers(code: str, days_before: int = 0) -> dict:
    """Top-10 buy/sell brokers (HK only) - 十大买卖经纪商/经纪队列排名. days_before: 0=realtime."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_top_ten_buy_sell_brokers"), code, days_before=days_before)
