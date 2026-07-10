from __future__ import annotations
from .. import connection, skill_runner
from ._base import mcp, skill_fn


@mcp.tool()
def get_analyst_consensus(code: str) -> dict:
    """Analyst consensus rating + target price - 分析师评级/一致预期/目标价/
    consensus/analyst rating. Stocks + REITs.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_research_analyst_consensus"), code)


@mcp.tool()
def get_morningstar_report(code: str) -> dict:
    """Morningstar research report - 晨星研报/fair value/护城河/moat/bull-bear.
    Stocks + REITs.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_research_morningstar_report"), code)


@mcp.tool()
def get_valuation_detail(code: str, valuation_type: int | None = None,
                         interval_type: int = 3) -> dict:
    """Valuation detail (PE/PB/PS trend, percentile, vs market) - 估值详情/
    市盈率/市净率/市销率/估值分位. valuation_type: 1=PE 2=PB 3=PS. interval_type:
    1=3m 2=6m 3=1y 4=3y 5=since2019 6=5y 7=10y 8=2y 9=20y 10=30y.
    """
    connection.get_context()
    return skill_runner._run_skill_json(
        skill_fn("quote", "get_valuation_detail"), code,
        valuation_type=valuation_type, interval_type=interval_type,
    )
