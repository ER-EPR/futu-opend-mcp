from __future__ import annotations
from .. import connection, skill_runner
from ._base import mcp, skill_fn


@mcp.tool()
def get_dividend_calendar(market: str, date: str, count: int = 50) -> dict:
    """All-market forward dividend/ex-date calendar - 派息日历/除息日历. market: US/HK/...;
    date YYYY-MM-DD. Distinct from per-stock historical get_corporate_actions.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_dividend_calendar"), market, date=date, count=count)
