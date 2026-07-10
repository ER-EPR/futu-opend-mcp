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


from futu_opend_mcp.tools import shareholders, short, profile


def _patch2(monkeypatch, capture):
    for mod in (shareholders, short, profile):
        monkeypatch.setattr(mod.connection, "get_context", lambda: None)
    def fake_run(fn, *a, **k):
        capture["fn"] = fn.__name__; capture["args"] = a; capture["kwargs"] = k
        return {"data": []}
    for mod in (shareholders, short, profile):
        monkeypatch.setattr(mod.skill_runner, "_run_skill_json", fake_run)


def test_insider_data_routes_holder(monkeypatch):
    cap = {}; _patch2(monkeypatch, cap)
    shareholders.get_insider_data("US.AAPL", data_type="holders")
    assert cap["fn"] == "get_insider_holder_list"


def test_insider_data_routes_trade(monkeypatch):
    cap = {}; _patch2(monkeypatch, cap)
    shareholders.get_insider_data("US.AAPL", data_type="trades")
    assert cap["fn"] == "get_insider_trade_list"


def test_short_data_routes_interest(monkeypatch):
    cap = {}; _patch2(monkeypatch, cap)
    short.get_short_data("HK.00700", data_type="interest")
    assert cap["fn"] == "get_short_interest"
