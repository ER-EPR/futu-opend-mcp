from futu_opend_mcp.tools import quote


def _patch_runner(monkeypatch, payload):
    monkeypatch.setattr(quote.skill_runner, "_run_skill_json",
                        lambda fn, *a, **k: payload)


def _patch_get_context(monkeypatch):
    monkeypatch.setattr(quote.connection, "get_context", lambda: object())


def test_get_snapshot_tool(monkeypatch):
    _patch_get_context(monkeypatch)
    _patch_runner(monkeypatch, {"data": [{"code": "US.AAPL", "last_price": 190.0}]})
    result = quote.get_snapshot(["US.AAPL"])
    assert result["data"][0]["last_price"] == 190.0


def test_get_kline_tool(monkeypatch):
    _patch_get_context(monkeypatch)
    _patch_runner(monkeypatch, {"code": "HK.00700", "data": []})
    result = quote.get_kline("HK.00700", ktype="1d", num=10)
    assert result["code"] == "HK.00700"
