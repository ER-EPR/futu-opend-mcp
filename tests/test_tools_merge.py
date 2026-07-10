from futu_opend_mcp.tools import corporate_actions, research


def _patch(monkeypatch, capture):
    monkeypatch.setattr(corporate_actions.connection, "get_context", lambda: None)
    monkeypatch.setattr(research.connection, "get_context", lambda: None)

    def fake_run(fn, *a, **k):
        capture["fn"] = fn.__name__
        capture["args"] = a
        capture["kwargs"] = k
        return {"data": []}
    monkeypatch.setattr(corporate_actions.skill_runner, "_run_skill_json", fake_run)
    monkeypatch.setattr(research.skill_runner, "_run_skill_json", fake_run)


def test_corporate_actions_routes_dividends(monkeypatch):
    cap = {}
    _patch(monkeypatch, cap)
    corporate_actions.get_corporate_actions("HK.00700", action_type="dividends")
    assert cap["fn"] == "get_corporate_actions_dividends"


def test_corporate_actions_routes_buybacks(monkeypatch):
    cap = {}
    _patch(monkeypatch, cap)
    corporate_actions.get_corporate_actions("HK.00700", action_type="buybacks")
    assert cap["fn"] == "get_corporate_actions_buybacks"


def test_corporate_actions_routes_splits(monkeypatch):
    cap = {}
    _patch(monkeypatch, cap)
    corporate_actions.get_corporate_actions("HK.00700", action_type="splits")
    assert cap["fn"] == "get_corporate_actions_stock_splits"


def test_corporate_actions_bad_action_errors(monkeypatch):
    cap = {}
    _patch(monkeypatch, cap)
    r = corporate_actions.get_corporate_actions("HK.00700", action_type="nope")
    assert r["_skill_error"] is True
