"""Price / quote / market tools.

Template for single-script tools: typed @mcp.tool fn -> ensure context live ->
delegate to the official skill function via _run_skill_json.
"""
from __future__ import annotations

from .. import connection, skill_runner
from ._base import mcp, skill_fn


@mcp.tool()
def get_snapshot(codes: list[str]) -> dict:
    """Get market snapshot (latest price, OHLC, volume, bid/ask) for one or
    more stocks - no subscription needed. Use when the user asks for 报价/价格/
    行情/快照/quote/price/snapshot. Codes like US.AAPL, HK.00700, SH.600519.
    Up to 400 codes per call.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_snapshot"), codes)


@mcp.tool()
def get_kline(
    code: str,
    ktype: str = "1d",
    num: int = 10,
    start: str | None = None,
    end: str | None = None,
    rehab: str = "forward",
) -> dict:
    """Get K-line / candlestick / historical price (K线/蜡烛图/历史走势).
    ktype: 1m,3m,5m,15m,30m,60m,1d,1w,1M,1Q,1Y. rehab: none/forward/backward
    (forward=前复权 default). With start+end (YYYY-MM-DD) pulls historical K-line
    across the range; otherwise the latest `num` bars. US intraday session not
    exposed in v1.
    """
    connection.get_context()
    return skill_runner._run_skill_json(
        skill_fn("quote", "get_kline"), code,
        ktype=ktype, num=num, start=start, end=end, rehab=rehab,
    )


@mcp.tool()
def get_market_state(codes: list[str]) -> dict:
    """Get market state (open/closed/lunch break) for codes - 市场状态/开盘了吗.
    Supports HK/US/SH/SZ/SG/MY/JP prefixes.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_market_state"), codes)
