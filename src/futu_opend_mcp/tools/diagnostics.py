from __future__ import annotations
from .. import connection, skill_runner
from ._base import mcp, skill_fn


@mcp.tool()
def get_quota_status() -> dict:
    """Self-diagnostics: aggregate user info, history-K-line quota, and global state -
    用户行情权限/订阅配额/历史K线额度/市场开闭/登录状态. Call when a data tool returns a
    permission/quota error to diagnose the cause.
    """
    connection.get_context()
    out = {}
    for label, fn_name in (("user_info", "get_user_info"),
                           ("history_kl_quota", "get_history_kl_quota"),
                           ("global_state", "get_global_state")):
        out[label] = skill_runner._run_skill_json(skill_fn("quote", fn_name))
    return out
