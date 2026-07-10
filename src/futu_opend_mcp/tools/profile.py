from __future__ import annotations
from .. import connection, skill_runner
from ._base import mcp, skill_fn


@mcp.tool()
def get_company_profile(code: str) -> dict:
    """Company profile - 公司概况/公司详情/公司简介/company profile/主营业务."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_company_profile"), code)


@mcp.tool()
def get_company_executives(code: str) -> dict:
    """Company executives & board - 公司高管/管理层/董事会/executives. Returns leader_name
    usable in get_executive_background.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_company_executives"), code)


@mcp.tool()
def get_executive_background(code: str, leader_name: str) -> dict:
    """Background/career history of a named executive - 高管背景/履历/CEO背景. Two-step: first
    get_company_executives to find leader_name, then call this.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_company_executive_background"), code, leader_name)


@mcp.tool()
def get_operational_efficiency(code: str, currency_code: str | None = None,
                               num: int = 10) -> dict:
    """Operational efficiency - 经营效率/员工数/人均营收/人均利润/headcount per-employee metrics.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_company_operational_efficiency"), code, currency_code=currency_code, num=num)
