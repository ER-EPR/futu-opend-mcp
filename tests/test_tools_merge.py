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


from futu_opend_mcp.tools import options, capital, derivatives


def _patch3(monkeypatch, capture):
    for mod in (options, capital, derivatives):
        monkeypatch.setattr(mod.connection, "get_context", lambda: None)
    def fake_run(fn, *a, **k):
        capture["fn"] = fn.__name__; capture["args"] = a; capture["kwargs"] = k
        return {"data": []}
    for mod in (options, capital, derivatives):
        monkeypatch.setattr(mod.skill_runner, "_run_skill_json", fake_run)


def test_option_underlying_routes_volatility(monkeypatch):
    cap = {}; _patch3(monkeypatch, cap)
    options.get_option_underlying("US.AAPL", view="volatility", begin="2025-01-01", end="2025-06-01")
    assert cap["fn"] == "get_option_underlying_his_volatility"


def test_option_underlying_routes_overview_multi_code(monkeypatch):
    cap = {}; _patch3(monkeypatch, cap)
    options.get_option_underlying(["US.AAPL", "US.TSLA"], view="overview")
    assert cap["fn"] == "get_option_underlying_overview"


from futu_opend_mcp.tools import plates, industrial_chains, ipo


def _patch4(monkeypatch, capture):
    for mod in (plates, industrial_chains, ipo):
        monkeypatch.setattr(mod.connection, "get_context", lambda: None)
    def fake_run(fn, *a, **k):
        capture["fn"] = fn.__name__; capture["args"] = a; capture["kwargs"] = k
        return {"data": []}
    for mod in (plates, industrial_chains, ipo):
        monkeypatch.setattr(mod.skill_runner, "_run_skill_json", fake_run)


def test_industrial_chains_routes_detail(monkeypatch):
    cap = {}; _patch4(monkeypatch, cap)
    industrial_chains.get_industrial_chains(market="HK", view="detail", chain_id=123)
    assert cap["fn"] == "get_industrial_chain_detail"


def test_industrial_plate_routes_stocks(monkeypatch):
    cap = {}; _patch4(monkeypatch, cap)
    industrial_chains.get_industrial_plate(plate_id=123, view="stocks")
    assert cap["fn"] == "get_industrial_plate_stock"


from futu_opend_mcp.tools import institutions, macro, dividends


def _patch5(monkeypatch, capture):
    for mod in (institutions, macro, dividends):
        monkeypatch.setattr(mod.connection, "get_context", lambda: None)
    def fake_run(fn, *a, **k):
        capture["fn"] = fn.__name__; capture["args"] = a; capture["kwargs"] = k
        return {"data": []}
    for mod in (institutions, macro, dividends):
        monkeypatch.setattr(mod.skill_runner, "_run_skill_json", fake_run)


def test_institution_holdings_routes_change(monkeypatch):
    cap = {}; _patch5(monkeypatch, cap)
    institutions.get_institution_holdings(market="US", institution_id=123, view="change")
    assert cap["fn"] == "get_institution_holding_change"


def test_macro_indicator_routes_history(monkeypatch):
    cap = {}; _patch5(monkeypatch, cap)
    macro.get_macro_indicator(view="history", indicator_id=1)
    assert cap["fn"] == "get_macro_indicator_history"


def test_fed_watch_routes_dot_plot(monkeypatch):
    cap = {}; _patch5(monkeypatch, cap)
    macro.get_fed_watch(view="dot_plot")
    assert cap["fn"] == "get_fed_watch_dot_plot"
