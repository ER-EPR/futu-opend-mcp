from __future__ import annotations
from typing import Literal
from .. import connection, skill_runner
from ._base import mcp, skill_fn


@mcp.tool()
def get_financial_statements(
    code: str,
    statement_type: Literal[1, 2, 3, 4] = 1,
    financial_type: int = 10,
    currency_code: str | None = None,
    num: int = 10,
) -> dict:
    """Get financial statements - 财务报表/财报/利润表/资产负债表/现金流量表/
    关键指标. statement_type: 1=Income 2=BalanceSheet 3=CashFlow 4=MainIndex(关键指标).
    financial_type: 7=年报 10=单季报+年报(default) 9=单季组合. currency_code ISO 4217
    (CNY/USD/HKD/...); omit for native currency.
    """
    connection.get_context()
    return skill_runner._run_skill_json(
        skill_fn("quote", "get_financials_statements"), code,
        statement_type=statement_type, financial_type=financial_type,
        currency_code=currency_code, num=num,
    )


@mcp.tool()
def get_revenue_breakdown(code: str, financial_type: int | None = None,
                          currency_code: str | None = None) -> dict:
    """Get revenue composition by product/industry/region/business - 主营构成/
    营收拆分/收入构成/revenue breakdown. financial_type: 7=年报 9=聚合季报.
    """
    connection.get_context()
    return skill_runner._run_skill_json(
        skill_fn("quote", "get_financials_revenue_breakdown"), code,
        financial_type=financial_type, currency_code=currency_code,
    )


@mcp.tool()
def get_earnings_calendar(market: str, date: str | None = None,
                          max_count: int = 50) -> dict:
    """Get earnings-release calendar for a market - 财报日历. market: US/HK/CN/SG/MY/JP.
    """
    connection.get_context()
    return skill_runner._run_skill_json(
        skill_fn("quote", "get_earnings_calendar"), market, date=date, max_count=max_count,
    )


@mcp.tool()
def get_earnings_price_history(code: str) -> dict:
    """Get per-earnings-day price detail + IV crush - 历史财报日数据明细/财报日股价历史/
    IV Crush/财报预期波动率. HK/US stocks only.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_financials_earnings_price_history"), code)
