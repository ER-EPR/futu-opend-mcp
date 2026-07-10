from futu_opend_mcp.tools import search, financials


def _patch(monkeypatch, payload):
    monkeypatch.setattr(search.connection, "get_context", lambda: None)
    monkeypatch.setattr(financials.connection, "get_context", lambda: None)
    monkeypatch.setattr(search.skill_runner, "_run_skill_json", lambda fn, *a, **k: payload)
    monkeypatch.setattr(financials.skill_runner, "_run_skill_json", lambda fn, *a, **k: payload)


def test_search_news(monkeypatch):
    _patch(monkeypatch, {"data": [{"title": "x"}]})
    assert search.search_news("苹果")["data"][0]["title"] == "x"


def test_financial_statements(monkeypatch):
    _patch(monkeypatch, {"code": "HK.00700", "report_list": []})
    r = financials.get_financial_statements("HK.00700", statement_type=1)
    assert r["code"] == "HK.00700"
