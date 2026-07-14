from __future__ import annotations
from .. import connection, skill_runner
from ._base import mcp, skill_fn


@mcp.tool()
def search_quote(keyword: str, max_count: int = 10) -> dict:
    """Search securities/ETFs/plates by keyword - 搜索股票/搜代码/search quote.
    Returns market/code/name/sec_type. Rate-limited 10/30s. If unsure of a
    stock code, call this first.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_search_quote"), keyword, max_count=max_count)


@mcp.tool()
def search_news(keyword: str, max_count: int = 10, news_sub_type: str = "ALL") -> dict:
    """Search news/announcements/ratings by keyword - 搜索资讯/搜新闻/搜公告.
    news_sub_type: ALL/NEWS(notice=公告)/NOTICE/RATING. Returns title/source/
    publish_time/related_securities/url. Rate-limited 10/30s.
    """
    connection.get_context()
    return skill_runner._run_skill_json(
        skill_fn("quote", "get_search_news"), keyword,
        max_count=max_count, news_sub_type=news_sub_type,
    )


@mcp.tool(name="futu_get_stock_info")
def get_stock_info(codes: list[str]) -> dict:
    """Get stock basic+snapshot info (name, lot size, market cap, PE) - 股票信息/
    基本信息. Underlying uses get_market_snapshot; up to 400 codes.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_stock_info"), codes)


@mcp.tool()
def screen_stocks(market: str, config_json: str, page_count: int = 200) -> dict:
    """Screen stocks by multi-factor config (V2) - 条件选股/筛选/screen stocks. market: HK/US/SH/
    SZ/SG/MY/JP. config_json: a JSON string with filters/retrieves/sort (see Futu V2 screen schema).
    Values are RAW (OpenD scales): PRICE 10.0, MARKET_CAP 1e10, change% 5.0 (not 0.05).
    """
    import json as _json
    connection.get_context()
    cfg = _json.loads(config_json)
    return skill_runner._run_skill_json(skill_fn("quote", "get_stock_screen"), market, cfg, page_count=page_count)
