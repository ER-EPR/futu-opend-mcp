from __future__ import annotations
from typing import Literal
from .. import connection, skill_runner
from ._base import mcp, skill_fn

_SHORT_ROUTES = {"volume": "get_daily_short_volume", "interest": "get_short_interest"}


@mcp.tool()
def get_short_data(code: str, data_type: Literal["volume", "interest"], num: int = 10) -> dict:
    """Short-selling data - 每日卖空/卖空量/卖空比例 (volume) or 空头持仓/short interest/
    days to cover (interest). HK/US.
    """
    fn_name = _SHORT_ROUTES.get(data_type)
    if fn_name is None:
        return {"_skill_error": True, "error": f"data_type must be {list(_SHORT_ROUTES)}"}
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", fn_name), code, num=num)
