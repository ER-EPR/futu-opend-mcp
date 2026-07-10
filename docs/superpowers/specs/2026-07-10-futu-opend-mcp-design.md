# futu-opend-mcp — Design

**Date:** 2026-07-10
**Status:** Approved (pre-implementation)
**Repo:** `github.com/ER-EPR/futu-opend-mcp` (public) → PyPI package `futu-opend-mcp`

## 1. Purpose & scope

A Python MCP server that connects to a **real Futu OpenD gateway** (borrowing its logged-in
session — no separate auth) and exposes **read-only investment-research** quote APIs as MCP tools.
No trading, no subscribe. Installable via `uvx futu-opend-mcp`; runs as stdio for Claude
Code/Desktop, and is loadable behind `mcpo` as HTTP for Open WebUI.

Three reference sources:
1. **Official Futu skill pack** (`https://openapi.futunn.com/skills/opend-skills.zip`) — primary.
   `skills/futuapi/SKILL.md` is the master reference; `skills/futuapi/scripts/quote/` are the
   reusable implementations; `skills/futuapi/scripts/common.py` holds shared helpers.
2. **futuapi.com/guide/mcp** — a Rust *rewrite* of OpenD with its own API-key MCP server. Used
   **only as a feature/naming checklist** (`futu_get_snapshot`, `futu_get_kline`,
   `futu_search_news`, …). We do **not** integrate it: it replaces OpenD and uses API-key auth,
   whereas we borrow a real OpenD login via the Python SDK.
3. **Official Futu API docs** — consulted only when the skill pack is unclear.

Scope decision (user-approved): **investment-research focus**, ~40 merged tools. Trade and
subscribe are excluded. Stale/duplicate interfaces are filtered; the most comprehensive
interface per info type is kept; similar functions are merged behind a single LLM-facing tool.

## 2. RSA certificate handling (key design question)

The futu Python SDK accepts the RSA key **only as a file path** via
`SysConfig.set_init_rsa_file(path)` — it cannot take raw key bytes. The key is a **shared
private key** (PKCS#1 1024-bit): the same key OpenD places in `FutuOpenD.xml` and every SDK
client loads. (This mirrors the existing `futu-tracker` pattern, `futu_client.py:105-128`.)

Resolution — **env var + file fallback**:
- Read `FUTU_OPEND_RSA_KEY` (PEM string) **or** `FUTU_OPEND_RSA_KEY_FILE` (path) at startup.
- If the env string form is used, materialize it to a `0600` tempfile and point the SDK at it.
- Enable `SysConfig.enable_proto_encrypt(is_encrypt=True)` and pass `is_encrypt=True` on the
  context.
- `FUTU_OPEND_ENCRYPT` (default `true`) gates the whole cert path. For a local `127.0.0.1`
  OpenD, encryption is not required (the skill's own `common.py` does not encrypt), so a user
  may set `ENCRYPT=false` and skip the cert entirely. On a remote/`0.0.0.0` OpenD it is
  mandatory.

This is the cleanest way to put the cert into an MCP server's environment while keeping it
ephemeral and SDK-compatible.

## 3. Reuse architecture (vendor + inject + wrap, never edit)

### 3.1 Vendor the official skill pack unmodified
Store `skills/futuapi/` under `futu_opend_mcp/_skill/futuapi/`, byte-for-byte. Add
`scripts/sync_skill.sh` that re-downloads the official zip and overwrites the vendored copy, so
updating to an official release is `./scripts/sync_skill.sh && git diff`. Git history tracks
changes; there are never merge conflicts because we never modify these files.

### 3.2 The single injection seam: patch `common.py`
`common.py` is **not** connection-only — it carries ~250 lines of genuinely reusable helpers
(`safe_get`, `safe_float`, `safe_int`, `df_to_records`, `to_jsonable`, enum parsers, error
classifiers `_is_permission_error`/`_is_no_account_error`) that every script imports. Rewriting
it would mean re-implementing every imported name forever and chasing new ones — the opposite of
"easy official updates". So we **do not rewrite it**.

Instead we patch four functions in place, before any script is loaded:
- `common.create_quote_context` → our factory returning a **single, long-lived, RSA-encrypted**
  `OpenQuoteContext` (reads host/port + cert from env, applies proto-encrypt). This is also where
  we close the encryption gap — the official `common.py` does not encrypt, our factory does.
- `common.safe_close` → no-op on the shared context (scripts call it in every `finally`; we must
  not let them close our singleton).
- `common.check_ret` → wrap so an API failure raises a catchable exception instead of
  `sys.exit(1)` (the official version calls `sys.exit`).
- `common.ensure_futu_api` → no-op. We do our own clean, non-`sys.exit` liveness check.

**Caveat handled:** `common.py` calls `ensure_futu_api()` at **import time** (module-level line
207), which `sys.exit`s the process if OpenD is unreachable — fatal for an MCP server. We
therefore **defer importing `common` until the first tool use**, after our own liveness check
passes (at which point the official socket check passes too, merely printing a stderr warning).
Then we apply the patches. No brittle hack.

### 3.3 Invocation mechanism: stdout capture
Each tool imports the official script's function (e.g. `get_snapshot(codes, output_json=True)`),
captures its `print(json.dumps(...))` stdout via `contextlib.redirect_stdout(StringIO())`
(stderr too), catches `SystemExit` (from `check_ret`), and parses the captured JSON into the
tool result.

**Why stdout capture (not hand-rolled SDK calls):** the user wants maximal reuse of official
scripts, and the field-parsing logic comes for free. Because MCP itself runs over stdio, *every*
byte the script prints must be captured — nothing may leak to real stdout or it corrupts the
JSON-RPC protocol. So capture is both the reuse mechanism **and** a correctness requirement.

A generic `_run_skill_json(fn, *args, **kwargs)` helper centralizes: redirect stdout/stderr,
invoke, catch `SystemExit`, parse JSON, classify error via the skill's own error predicates, and
return a clean dict. Where an official function is awkward for capture, a tool may fall back to
calling the SDK directly via `common.py` helpers (the same vendored helpers).

### 3.4 Merging duplicate tools for a simpler LLM entry point
Upper-layer wrappers combine similar official scripts behind one tool with a discriminating
parameter, so the LLM sees fewer, more obvious entry points. Six merges (each keeps the other
tools in its category as separate, standalone tools):
- `get_corporate_actions(code, action_type)` ← `dividends` + `buybacks` + `stock_splits`
- `get_insider_data(code, data_type)` ← `insider_holder_list` + `insider_trade_list`
  (the *other* four shareholder tools stay separate)
- `get_short_data(code, data_type)` ← `daily_short_volume` + `short_interest`
- `get_macro_indicator` ← `macro_indicator_list` + `macro_indicator_history`
- `get_fed_watch` ← `fed_watch_target_rate` + `fed_watch_dot_plot`
- `get_quota_status` ← `user_info` + `history_kl_quota` + `global_state` (a self-diagnostics tool)

## 4. Connection strategy

A **single shared `OpenQuoteContext`** lives for the lifetime of the MCP server process. It is
opened lazily on first tool use (after the deferred `common` import + patches + liveness check)
and closed on shutdown. Rationale: rapid open/close of contexts makes OpenD slow or error out
(per the skill pack and the existing tracker). All tools are read-only, so one quote context
suffices — no trade context.

## 5. Tool catalogue (~40 tools, merged)

All tools read-only; no trade/subscribe. Rules applied: drop stale V1 (`get_stock_filter`,
keep V2 `get_stock_screen`); keep the most comprehensive interface per info type; merge
similar. `get_stock_quote` (needs subscribe) is replaced by the subscription-free
`get_snapshot`.

| Category | Tool | ← Official script(s) | Note |
|---|---|---|---|
| Price/quote | `get_snapshot` `get_kline` `get_market_state` | get_snapshot / get_kline / get_market_state | snapshot = core quote; kline = historical price |
| Search | `search_quote` `search_news` `get_stock_info` | get_search_quote / get_search_news / get_stock_info | news covers news/announcement/rating |
| Screen | `screen_stocks` | get_stock_screen (V2) | V1 get_stock_filter dropped (stale) |
| Financials | `get_financial_statements` `get_revenue_breakdown` `get_earnings_calendar` `get_earnings_price_history` | _statements / _revenue_breakdown / get_earnings_calendar / _earnings_price_history | statement_type param covers 4 statement types |
| Research/valuation | `get_analyst_consensus` `get_morningstar_report` `get_valuation_detail` | _analyst_consensus / _morningstar_report / _valuation_detail | target+rating / fair value+moat / PE-PB-PS percentile |
| Corporate actions | `get_corporate_actions` | **dividends + buybacks + stock_splits** | **3→1 merge**, action_type param |
| Shareholders | `get_shareholder_overview` `get_holding_changes` `get_holder_detail` `get_institutional_holdings` `get_insider_data` | overview / holding_changes / holder_detail / institutional / **insider_holder_list+insider_trade_list** | insider **2→1**, data_type param (US only) |
| Profile | `get_company_profile` `get_company_executives` | get_company_profile / get_company_executives | |
| Capital | `get_capital_flow` `get_capital_distribution` `get_top_brokers` | get_capital_flow / _distribution / get_top_ten_buy_sell_brokers | |
| Short | `get_short_data` | **daily_short_volume + short_interest** | **2→1 merge**, type param |
| Options/derivatives | `resolve_option_code` `get_option_chain` `get_option_expiration_date` `get_option_quote` `get_option_volatility` `get_option_strategy_analysis` | resolve_option_code / get_option_chain / _expiration_date / get_option_quote / get_option_volatility / get_option_strategy_analysis | covers the "derivative price changes" goal |
| Warrant/futures | `get_warrant` `get_future_info` `get_reference_securities` | get_warrant / get_future_info / get_referencestock_list | reference = spot↔warrant/future/option discovery |
| Plates | `get_plate_list` `get_plate_stocks` `get_owner_plate` | get_plate_list / get_plate_stock / get_owner_plate | |
| Macro | `get_economic_calendar` `get_macro_indicator` `get_fed_watch` | get_economic_calendar / **macro_indicator_list+history** / **fed_watch_target_rate+dot_plot** | 2 merges |
| IPO | `get_ipo_list` | get_ipo_list | |
| Diagnostics | `get_quota_status` | **user_info + history_kl_quota + global_state** | **3→1 merge**; helps LLM self-diagnose permission/quota errors |

**Deliberately excluded in v1:** all ranking/heat-list tools (hot_list, top_movers,
period_change, pre/after/overnight rank, short_selling_rank, earnings_beat_rank, dividend_rank,
high_dividend_soe — too overlapping), ARK tools, industrial chains, standalone institution tools
(partly covered by shareholders_institutional), technical indicators (list/calc),
user-security/price-reminder (personal, not research), executive_background,
operational_efficiency, dividend calendar, option strategy basis/spread, underlying IV/HV time
series, and `get_stock_quote` (subscription-based, replaced by `get_snapshot`).

## 6. Migrating SKILL.md guidance into tool descriptions (skill vs tool)

A skill's `SKILL.md` is a one-shot prompt that drives a multi-step plan and may be long/procedural.
An MCP tool description is *scanned for selection* among ~40 siblings and must fit efficiently in a
tool-use context. So we **distill, not copy**:

- **Trigger phrases** ("当用户问'分红'、'派息'时") → the most valuable migration; folded into each
  tool's `description` to improve tool selection. ✅ migrate.
- **Parameter semantics & gotchas** (enum meanings, `5.0 not 0.05`, quarter codes) → input-schema
  field `description`s. ✅ migrate.
- **Market-support constraints** ("期权链仅支持港美正股ETF") → tool description as a constraint. ✅
  migrate.
- **Multi-step workflows** (option-code resolution is a 3-step op) → kept as separate tools with a
  one-line "prerequisite" note rather than a procedure. ⚠️ distill, do not collapse steps into one
  tool.
- **Ticker lookup table** (~100 lines `腾讯→HK.00700`) → ❌ do not migrate (bloats context); rely on
  the model's general knowledge + `search_quote`. Add a one-line hint: "if unsure of the code, call
  search_quote first".
- **Trade safety rules** (`unlock_trade`) → ❌ drop entirely; there are no trade tools.

## 7. Packaging & running

- `pyproject.toml`, package `futu-opend-mcp`, entry point
  `[project.scripts] futu-opend-mcp = "futu_opend_mcp.server:main"`.
- `main()` builds the FastMCP app and runs `mcp.run()` (stdio) — standard for Claude Code/Desktop.
- **mcpo path:** `mcpo --port 8000 -- futu-opend-mcp` spawns our stdio server and exposes OpenAPI
  for Open WebUI. We write no HTTP code — mcpo handles the transport. Env vars pass through.
- Dependencies: `futu-api>=10.5.6508`, `mcp>=1.0`; Python ≥3.10. pandas is pulled in by futu-api.
- **PyPI release:** GitHub Actions on tag → build + publish via PyPI **trusted publishing** (no
  token). Before that, `uvx --from git+https://github.com/ER-EPR/futu-opend-mcp futu-opend-mcp`
  works.
- **License/attribution:** vendored skill scripts keep their `LEGAL_*.md`; we add attribution in the
  README that we wrap the official Futu skill pack.

## 8. Configuration (env vars)

```
FUTU_OPEND_HOST=127.0.0.1
FUTU_OPEND_PORT=11111
FUTU_OPEND_RSA_KEY=<PEM string>      # OR:
FUTU_OPEND_RSA_KEY_FILE=/path/key.pem
FUTU_OPEND_ENCRYPT=true              # false for a local 127.0.0.1 OpenD skips the cert
FUTU_OPEND_LOG_LEVEL=INFO
```

Startup validation: if host/port missing or OpenD unreachable → raise a clean error (no
`sys.exit`); if `ENCRYPT=true` but neither cert var is set → error with the hint to obtain the key
via `docker compose logs opend | grep 'NEW RSA PRIVATE KEY'` (same hint as the tracker). Ship a
`.env.example`.

## 9. Error handling & testing

- **Errors:** every tool goes through `_run_skill_json()`, which captures `SystemExit` + parses the
  captured-stdout JSON. The skill's error classifiers (`_is_permission_error` /
  `_is_no_account_error`) become structured tool errors with actionable hints (e.g. "港股行情权限不足，
  请购买对应行情卡") — reusing the official logic directly.
- **Tests:** unit tests for RSA-tempfile materialization, config/env parsing, the
  `_run_skill_json` capture mechanism (inject a fake script that prints + sys.exits), the merge
  dispatchers (corporate_actions / insider / short / macro / fed_watch routing), and enum/market
  parsing. Integration tests marked `@pytest.mark.integration` do a snapshot+kline smoke test
  against a live OpenD and skip themselves if OpenD is unreachable (skipped by default in CI).

## 10. Repository layout

```
futu-opend-mcp/
├── pyproject.toml
├── README.md
├── LICENSE
├── .env.example
├── .gitignore
├── scripts/
│   └── sync_skill.sh                 # re-vendor official skill pack
├── .github/workflows/
│   ├── ci.yml                        # lint + unit tests
│   └── publish.yml                   # tag → PyPI trusted publish
└── src/futu_opend_mcp/
    ├── __init__.py
    ├── server.py                     # FastMCP app + main() entry
    ├── config.py                     # env parsing, validation, RSA tempfile
    ├── connection.py                 # patched create_quote_context, singleton ctx
    ├── skill_runner.py               # _run_skill_json: stdout capture + error classify
    ├── _skill/futuapi/               # vendored, unmodified
    │   ├── SKILL.md  docs/  scripts/{common.py,quote/*,...}  LEGAL_*.md
    └── tools/                        # ~40 tool definitions (one module per category)
        ├── quote.py  search.py  financials.py  research.py
        ├── corporate_actions.py  shareholders.py  profile.py  capital.py
        ├── short.py  options.py  derivatives.py  plates.py  macro.py  ipo.py
        └── diagnostics.py
```
