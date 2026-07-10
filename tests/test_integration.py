import pytest
from futu_opend_mcp import connection


@pytest.mark.integration
def test_live_snapshot_and_kline():
    if not connection.check_reachable():
        pytest.skip("OpenD not reachable")
    from futu_opend_mcp.tools import quote
    snap = quote.get_snapshot(["HK.00700"])
    assert "_skill_error" not in snap or snap.get("data") or "error" in snap
    kl = quote.get_kline("HK.00700", ktype="1d", num=5)
    assert isinstance(kl, dict)
