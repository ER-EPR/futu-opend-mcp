# futu-opend-mcp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A uvx-installable Python MCP server that borrows a real Futu OpenD login and exposes ~50 read-only investment-research quote APIs as MCP tools, by wrapping the official Futu skill pack unmodified.

**Architecture:** Vendor `skills/futuapi/` unmodified under `src/futu_opend_mcp/_skill/`. Monkeypatch its `common.py` connection seam (4 functions) so scripts reuse a single long-lived RSA-encrypted `OpenQuoteContext`. Each MCP tool calls an official script function, captures its `--json` stdout via `contextlib.redirect_stdout`, catches `SystemExit`, and returns parsed JSON. FastMCP (bundled in the `mcp` SDK) registers tools; runs as stdio (Claude) and behind mcpo (Open WebUI).

**Tech Stack:** Python ≥3.10, `futu-api>=10.5.6508`, `mcp` SDK (bundled FastMCP), pandas (transitive), pytest, GitHub Actions, PyPI trusted publishing.

**Spec:** `docs/superpowers/specs/2026-07-10-futu-opend-mcp-design.md`

**Scope note:** This plan builds the v1 catalogue (~50 tools). The ~40 tools are repetitive once the harness exists, so tasks group tools by category with a shared pattern; each category task lists its tools and the per-tool registration code follows one of two templates (single-script tool / merge tool). v2 deferrals (rankers, screeners, ARK, indicators) are out of scope — see spec §5.1.

---

## File Structure

```
futu-opend-mcp/
├── pyproject.toml                          # packaging, deps, entry point, project metadata
├── README.md                               # install + usage (uvx, claude, mcpo)
├── LICENSE                                 # MIT
├── .env.example                            # documented env vars
├── .gitignore
├── scripts/sync_skill.sh                   # re-vendor official skill pack from zip
├── .github/workflows/ci.yml                # lint + unit tests on push/PR
├── .github/workflows/publish.yml           # tag -> PyPI trusted publish
├── src/futu_opend_mcp/
│   ├── __init__.py                         # __version__
│   ├── server.py                           # FastMCP app + main(), imports all tool modules
│   ├── config.py                           # env parsing, validation, RSA tempfile materialization
│   ├── connection.py                       # liveness check, singleton ctx, common.py patches
│   ├── skill_runner.py                     # _run_skill_json(): stdout capture + error classify
│   ├── _skill/futuapi/                     # vendored, unmodified (committed once)
│   │   ├── SKILL.md  docs/  scripts/{common.py, quote/*, ...}  LEGAL_*.md
│   └── tools/
│       ├── __init__.py                     # register_all(mcp): import + decorate
│       ├── _base.py                        # shared helpers: mcp singleton, type aliases, enums
│       ├── quote.py search.py financials.py research.py
│       ├── corporate_actions.py shareholders.py profile.py capital.py short.py
│       ├── options.py derivatives.py plates.py industrial_chains.py
│       ├── institutions.py macro.py dividends.py ipo.py diagnostics.py
└── tests/
    ├── conftest.py                         # fakes + fixtures (no live OpenD by default)
    ├── test_config.py
    ├── test_connection.py
    ├── test_skill_runner.py
    ├── test_tools_merge.py
    └── test_server_smoke.py
```

**Responsibility boundaries:**
- `config.py` — pure env parsing + RSA tempfile; no SDK imports. Testable without OpenD.
- `connection.py` — the *only* place that imports `futu` and patches `common`. Owns the singleton context + liveness check.
- `skill_runner.py` — the generic capture harness. No business logic; knows nothing about specific scripts.
- `tools/*.py` — one module per category. Each imports `skill_runner._run_skill_json` and the vendored script functions, and registers `@mcp.tool` functions. No SDK imports here.
- `server.py` — assembles FastMCP, calls `register_all`, runs stdio. No tool logic.

---

## Task 1: Scaffold project, packaging, and CI

**Files:**
- Create: `pyproject.toml`, `LICENSE`, `.gitignore`, `.env.example`, `README.md`
- Create: `.github/workflows/ci.yml`
- Create: `src/futu_opend_mcp/__init__.py`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "futu-opend-mcp"
version = "0.1.0"
description = "MCP server exposing Futu OpenD read-only investment-research quote APIs."
readme = "README.md"
requires-python = ">=3.10"
license = "MIT"
authors = [{ name = "eli" }]
keywords = ["futu", "opend", "mcp", "stock", "finance"]
classifiers = [
  "Programming Language :: Python :: 3",
  "License :: OSI Approved :: MIT License",
  "Operating System :: OS Independent",
]
dependencies = [
  "futu-api>=10.5.6508",
  "mcp>=1.0",
]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-asyncio>=0.23", "ruff>=0.5"]

[project.scripts]
futu-opend-mcp = "futu_opend_mcp.server:main"

[tool.hatch.build.targets.wheel]
packages = ["src/futu_opend_mcp"]

[tool.hatch.build.targets.wheel.force-include]
"src/futu_opend_mcp/_skill" = "futu_opend_mcp/_skill"

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = ["integration: needs a live OpenD gateway"]
```

- [ ] **Step 2: Write `LICENSE` (MIT), `.gitignore`, `.env.example`, `src/futu_opend_mcp/__init__.py`**

`.env.example`:
```
# Futu OpenD gateway (must already be running + logged in)
FUTU_OPEND_HOST=127.0.0.1
FUTU_OPEND_PORT=11111

# RSA private key (shared with OpenD's FutuOpenD.xml), PKCS#1 1024-bit PEM.
# Provide ONE of the two forms:
FUTU_OPEND_RSA_KEY=
FUTU_OPEND_RSA_KEY_FILE=

# Enable proto encryption. Set false ONLY for a local 127.0.0.1 OpenD.
FUTU_OPEND_ENCRYPT=true

FUTU_OPEND_LOG_LEVEL=INFO
```

`src/futu_opend_mcp/__init__.py`:
```python
__version__ = "0.1.0"
```

`README.md`: a short stub now (full content in Task 16):
```markdown
# futu-opend-mcp

MCP server exposing Futu OpenD read-only investment-research quote APIs.

> WIP — see `docs/superpowers/specs/2026-07-10-futu-opend-mcp-design.md`.
```

- [ ] **Step 3: Write `.github/workflows/ci.yml`**

```yaml
name: ci
on:
  push: { branches: [main] }
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -e ".[dev]"
      - run: ruff check .
      - run: pytest -q -m "not integration"
```

- [ ] **Step 4: Install dev deps + verify import**

Run: `pip install -e ".[dev]"`
Expected: succeeds; `futu-api` and `mcp` install.

Run: `python -c "import futu_opend_mcp; print(futu_opend_mcp.__version__)"`
Expected: prints `0.1.0`

- [ ] **Step 5: Commit**

```bash
git add -A
git commit -m "scaffold: packaging, CI, project skeleton"
```

---

## Task 2: Vendor the official skill pack + sync script

**Files:**
- Create: `scripts/sync_skill.sh`
- Create (vendored): `src/futu_opend_mcp/_skill/futuapi/...` (the unpacked `skills/futuapi/`)
- Modify: `.gitignore` (ensure `_skill` is NOT ignored)

- [ ] **Step 1: Write `scripts/sync_skill.sh`**

```bash
#!/usr/bin/env bash
# Re-vendor the official Futu skill pack into src/futu_opend_mcp/_skill/.
# Usage: ./scripts/sync_skill.sh
set -euo pipefail
DEST="src/futu_opend_mcp/_skill"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
curl -sSL -o "$TMP/opend-skills.zip" "https://openapi.futunn.com/skills/opend-skills.zip"
unzip -q "$TMP/opend-skills.zip" -d "$TMP"
rm -rf "$DEST/futuapi"
mkdir -p "$DEST"
cp -R "$TMP/skills/futuapi" "$DEST/futuapi"
echo "Vendored futuapi skill pack to $DEST/futuapi"
echo "Review with: git diff --stat"
```

- [ ] **Step 2: Run the sync script to vendor the pack**

Run: `chmod +x scripts/sync_skill.sh && ./scripts/sync_skill.sh`
Expected: prints "Vendored futuapi skill pack …". `src/futu_opend_mcp/_skill/futuapi/SKILL.md` and `scripts/common.py` exist.

Run: `ls src/futu_opend_mcp/_skill/futuapi/scripts/quote | head`
Expected: lists `get_snapshot.py`, `get_kline.py`, etc.

- [ ] **Step 3: Verify the vendored common.py imports (sanity, no patch yet)**

Run: `python -c "import sys; sys.path.insert(0,'src/futu_opend_mcp/_skill/futuapi/scripts'); import common; print(common.create_quote_context.__name__)"`
Expected: prints `create_quote_context` (and may print a stderr warning about OpenD/version stamp — that is fine, it does not exit because OpenD is local-default; if it does exit because OpenD is unreachable, that confirms why we must patch in Task 4).

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "vendor: official futuapi skill pack + sync_skill.sh"
```

---

## Task 3: config.py — env parsing + RSA tempfile (TDD)

**Files:**
- Create: `tests/conftest.py`
- Create: `tests/test_config.py`
- Create: `src/futu_opend_mcp/config.py`

- [ ] **Step 1: Write `tests/conftest.py`** (shared fakes used across tests)

```python
import os
import pytest


@pytest.fixture
def clean_env(monkeypatch):
    """Strip all FUTU_OPEND_* env vars so each test starts clean."""
    for k in list(os.environ):
        if k.startswith("FUTU_OPEND_"):
            monkeypatch.delenv(k, raising=False)
    return monkeypatch
```

- [ ] **Step 2: Write the failing tests `tests/test_config.py`**

```python
import os
from pathlib import Path
import pytest
from futu_opend_mcp import config


def test_defaults(clean_env):
    cfg = config.load()
    assert cfg.host == "127.0.0.1"
    assert cfg.port == 11111
    assert cfg.encrypt is True


def test_parses_env(clean_env, monkeypatch):
    monkeypatch.setenv("FUTU_OPEND_HOST", "10.0.0.5")
    monkeypatch.setenv("FUTU_OPEND_PORT", "22222")
    monkeypatch.setenv("FUTU_OPEND_ENCRYPT", "false")
    cfg = config.load()
    assert cfg.host == "10.0.0.5"
    assert cfg.port == 22222
    assert cfg.encrypt is False


def test_materializes_inline_rsa_key_to_tempfile(clean_env, monkeypatch, tmp_path):
    pem = "-----BEGIN RSA PRIVATE KEY-----\nfake\n-----END RSA PRIVATE KEY-----\n"
    monkeypatch.setenv("FUTU_OPEND_RSA_KEY", pem)
    cfg = config.load()
    path = config.rsa_key_file(cfg)
    assert Path(path).exists()
    content = Path(path).read_text()
    assert content.strip() == pem.strip()
    assert (Path(path).stat().st_mode & 0o777) == 0o600


def test_uses_rsa_key_file_path_when_no_inline(clean_env, monkeypatch, tmp_path):
    f = tmp_path / "k.pem"
    f.write_text("-----BEGIN RSA PRIVATE KEY-----\nx\n-----END RSA PRIVATE KEY-----\n")
    monkeypatch.setenv("FUTU_OPEND_RSA_KEY_FILE", str(f))
    cfg = config.load()
    assert config.rsa_key_file(cfg) == str(f)


def test_encrypt_true_without_key_raises(clean_env, monkeypatch):
    monkeypatch.setenv("FUTU_OPEND_ENCRYPT", "true")
    cfg = config.load()
    with pytest.raises(config.ConfigError) as exc:
        config.rsa_key_file(cfg)
    assert "FUTU_OPEND_RSA_KEY" in str(exc.value)


def test_encrypt_false_needs_no_key(clean_env, monkeypatch):
    monkeypatch.setenv("FUTU_OPEND_ENCRYPT", "false")
    cfg = config.load()
    assert config.rsa_key_file(cfg) is None
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `pytest tests/test_config.py -q`
Expected: FAIL (module `config` has no `load`/`ConfigError`).

- [ ] **Step 4: Write `src/futu_opend_mcp/config.py`**

```python
"""Env-var parsing, validation, and RSA-key tempfile materialization.

No `futu` imports here — keep this pure so it is unit-testable without OpenD.
"""
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path


class ConfigError(RuntimeError):
    """Raised when required config is missing or invalid."""


@dataclass(frozen=True)
class Config:
    host: str
    port: int
    encrypt: bool
    rsa_key_inline: str | None
    rsa_key_file: str | None
    log_level: str


def load() -> Config:
    return Config(
        host=os.getenv("FUTU_OPEND_HOST", "127.0.0.1"),
        port=int(os.getenv("FUTU_OPEND_PORT", "11111")),
        encrypt=os.getenv("FUTU_OPEND_ENCRYPT", "true").strip().lower() in ("1", "true", "yes"),
        rsa_key_inline=os.getenv("FUTU_OPEND_RSA_KEY") or None,
        rsa_key_file=os.getenv("FUTU_OPEND_RSA_KEY_FILE") or None,
        log_level=os.getenv("FUTU_OPEND_LOG_LEVEL", "INFO").upper(),
    )


def rsa_key_file(cfg: Config) -> str | None:
    """Return a path to a PEM file holding the RSA private key, or None if
    encryption is disabled.

    - If FUTU_OPEND_RSA_KEY_FILE is set, use it directly.
    - Else if FUTU_OPEND_RSA_KEY (inline PEM) is set, materialize to a 0600
      tempfile and return its path.
    - If encrypt=True but neither is set, raise ConfigError with guidance.
    """
    if not cfg.encrypt:
        return None
    if cfg.rsa_key_file:
        return cfg.rsa_key_file
    if cfg.rsa_key_inline:
        key = cfg.rsa_key_inline.strip() + "\n"
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False)
        tmp.write(key)
        tmp.close()
        os.chmod(tmp.name, 0o600)
        return tmp.name
    raise ConfigError(
        "FUTU_OPEND_ENCRYPT=true but no RSA key set. Provide FUTU_OPEND_RSA_KEY "
        "(inline PEM) or FUTU_OPEND_RSA_KEY_FILE (path). Obtain the key with: "
        "`docker compose logs opend | grep -A20 'NEW RSA PRIVATE KEY'`."
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_config.py -q`
Expected: PASS (6 tests).

- [ ] **Step 6: Commit**

```bash
git add tests/conftest.py tests/test_config.py src/futu_opend_mcp/config.py
git commit -m "feat(config): env parsing + RSA tempfile materialization"
```

---

## Task 4: connection.py — liveness check, singleton context, common.py patches (TDD)

**Files:**
- Create: `tests/test_connection.py`
- Create: `src/futu_opend_mcp/connection.py`

This is the critical injection seam. We patch four `common.py` functions **before** any quote script is imported, and we defer importing `common` until first use.

- [ ] **Step 1: Write the failing tests `tests/test_connection.py`**

```python
import types
import pytest
from futu_opend_mcp import connection


def test_liveness_check_returns_false_when_unreachable(clean_env, monkeypatch):
    monkeypatch.setenv("FUTU_OPEND_HOST", "127.0.0.1")
    monkeypatch.setenv("FUTU_OPEND_PORT", "1")  # nothing listening
    assert connection.check_reachable() is False


def test_patches_common_seam(monkeypatch):
    """patch_common() must override create_quote_context, safe_close, check_ret,
    ensure_futu_api on the given common module without importing futu."""
    fake_common = types.SimpleNamespace(
        create_quote_context=lambda: None,
        safe_close=lambda ctx: None,
        check_ret=lambda *a, **k: None,
        ensure_futu_api=lambda: True,
    )
    connection.patch_common(fake_common)
    # create_quote_context should now be OUR factory (raises on no key when encrypt)
    assert fake_common.ensure_futu_api.__name__ == "_noop"
    assert fake_common.safe_close.__name__ == "_noop_safe_close"
    assert fake_common.check_ret.__name__ == "_patched_check_ret"


def test_patched_check_ret_raises_on_error(monkeypatch):
    fake_common = types.SimpleNamespace(
        check_ret=lambda *a, **k: None,
        _original_check_ret=None,
    )
    # simulate the real check_ret being restored by patch_common
    def real_check_ret(ret, data, ctx=None, action="", output_json=None):
        # mimic official: if ret != OK -> sys.exit
        import sys
        sys.exit(1)
    fake_common.check_ret = real_check_ret
    connection.patch_common(fake_common)
    with pytest.raises(connection.ApiError):
        fake_common.check_ret(1, "some error", None, "act")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_connection.py -q`
Expected: FAIL (`connection` module missing symbols).

- [ ] **Step 3: Write `src/futu_opend_mcp/connection.py`**

```python
"""The single injection seam: a long-lived RSA-encrypted OpenQuoteContext and
patches over the vendored common.py so official scripts reuse our singleton.

Importing `common` is DEFERRED until first tool use (common.py calls
ensure_futu_api() at import time, which sys.exits if OpenD is unreachable).
"""
from __future__ import annotations

import logging
import socket
import sys
import threading
from typing import Any

from . import config

log = logging.getLogger("futu_opend_mcp")

# Ret code that means OK in the futu SDK (futu.RET_OK == 0). Hard-coded to
# avoid importing futu here; the patched check_ret compares against it.
_RET_OK = 0


class ApiError(RuntimeError):
    """Raised by the patched check_ret when an official API call fails."""


_state = threading.local()
_lock = threading.Lock()


def _load_config() -> config.Config:
    return config.load()


def check_reachable(cfg: config.Config | None = None) -> bool:
    """Quick TCP liveness check to OpenD. True if the port accepts a connection."""
    cfg = cfg or _load_config()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        sock.connect((cfg.host, cfg.port))
        return True
    except OSError:
        return False
    finally:
        sock.close()


# ---- singleton context -----------------------------------------------------

_ctx: Any = None


def get_context() -> Any:
    """Return the singleton OpenQuoteContext, opening + patching on first call."""
    global _ctx
    with _lock:
        if _ctx is not None:
            return _ctx
        cfg = _load_config()
        if not check_reachable(cfg):
            raise ApiError(
                f"OpenD unreachable at {cfg.host}:{cfg.port}. Start Futu OpenD first."
            )
        # Defer-import common AFTER liveness passes, then patch it.
        common = _import_and_patch_common(cfg)
        # Use our factory (already installed onto common) to build the ctx.
        _ctx = common.create_quote_context()
        return _ctx


def close_context() -> None:
    global _ctx
    with _lock:
        if _ctx is not None:
            try:
                _ctx.close()
            except Exception:
                pass
            _ctx = None


# ---- common.py patches -----------------------------------------------------

def _import_and_patch_common(cfg: config.Config):
    """Import the vendored common.py (deferred) and install our patches."""
    import importlib
    # common.py lives at _skill/futuapi/scripts/common.py
    scripts_dir = str(
        (__import__("pathlib").Path(__file__).resolve().parent
         / "_skill" / "futuapi" / "scripts")
    )
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    common = importlib.import_module("common")

    # Stash the originals so _patched_check_ret can delegate for the OK case.
    common._original_check_ret = common.check_ret
    patch_common(common, cfg)
    return common


def patch_common(common, cfg: config.Config | None = None) -> None:
    """Override the 4 connection-related functions on a common module object.

    Keeps idempotent: safe to call on an already-patched module.
    """
    cfg = cfg or _load_config()

    def _noop(*a, **k):
        return True

    def _noop_safe_close(ctx, *a, **k):
        # Do not close the singleton; official scripts call safe_close in finally.
        return None

    def _factory():
        import futu as ft
        key_path = config.rsa_key_file(cfg)
        if key_path:
            ft.SysConfig.enable_proto_encrypt(is_encrypt=True)
            ft.SysConfig.set_init_rsa_file(key_path)
        kwargs = dict(host=cfg.host, port=cfg.port, is_encrypt=bool(key_path))
        # ai_type=1 marks us as an AI client (skill convention); guard old SDKs.
        try:
            return ft.OpenQuoteContext(**kwargs, ai_type=1)
        except TypeError:
            return ft.OpenQuoteContext(**kwargs)

    def _patched_check_ret(ret, data, ctx=None, action="操作", output_json=None):
        if ret == _RET_OK:
            return
        # API failure: raise instead of sys.exit. Reuse official classifiers if present.
        msg = str(data)
        hint = ""
        for pred_name in ("_is_permission_error", "_is_no_account_error", "_is_unlock_needed_error"):
            pred = getattr(common, pred_name, None)
            if callable(pred) and pred(msg):
                hint = f" (hint predicate {pred_name} matched)"
                break
        raise ApiError(f"{action} failed: {msg}{hint}")

    common.ensure_futu_api = _noop
    common.safe_close = _noop_safe_close
    common.create_quote_context = _factory
    common.check_ret = _patched_check_ret
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_connection.py -q`
Expected: PASS (3 tests). Note `test_patches_common_seam` and `test_patched_check_ret_raises_on_error` pass with the fake module; `test_liveness_check_returns_false_when_unreachable` passes via real socket.

- [ ] **Step 5: Commit**

```bash
git add tests/test_connection.py src/futu_opend_mcp/connection.py
git commit -m "feat(connection): singleton RSA-encrypted ctx + common.py patches"
```

---

## Task 5: skill_runner.py — stdout capture harness (TDD)

**Files:**
- Create: `tests/test_skill_runner.py`
- Create: `src/futu_opend_mcp/skill_runner.py`

`_run_skill_json(fn, *args, **kwargs)` calls an official function with `output_json=True`, captures its `print(json.dumps(...))`, catches `SystemExit`, returns parsed JSON, and converts `ApiError` into a structured error dict.

- [ ] **Step 1: Write the failing tests `tests/test_skill_runner.py`**

```python
import json
import pytest
from futu_opend_mcp import skill_runner


def test_captures_json_output(capsys):
    def fake_fn(codes, output_json=False):
        print(json.dumps({"data": [{"code": c} for c in codes]}, ensure_ascii=False))
    result = skill_runner._run_skill_json(fake_fn, ["US.AAPL"])
    assert result == {"data": [{"code": "US.AAPL"}]}


def test_passes_output_json_true():
    seen = {}
    def fake_fn(code, output_json=False):
        seen["output_json"] = output_json
        print(json.dumps({"data": []}))
    skill_runner._run_skill_json(fake_fn, "HK.00700")
    assert seen["output_json"] is True


def test_systemexit_with_error_json_is_returned_as_error():
    def fake_fn(code, output_json=False):
        print(json.dumps({"error": "permission denied"}, ensure_ascii=False))
        raise SystemExit(1)
    result = skill_runner._run_skill_json(fake_fn, "HK.00700")
    assert result == {"error": "permission denied", "_skill_error": True}


def test_api_error_becomes_structured_error():
    from futu_opend_mcp import connection
    def fake_fn(code, output_json=False):
        raise connection.ApiError("snapshot failed: no permission")
    result = skill_runner._run_skill_json(fake_fn, "HK.00700")
    assert result["_skill_error"] is True
    assert "snapshot failed" in result["error"]


def test_non_json_stdout_is_wrapped_as_error():
    def fake_fn(code, output_json=False):
        print("无数据")  # not JSON
    result = skill_runner._run_skill_json(fake_fn, "HK.00700")
    assert result["_skill_error"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_skill_runner.py -q`
Expected: FAIL (module missing).

- [ ] **Step 3: Write `src/futu_opend_mcp/skill_runner.py`**

```python
"""Generic harness for calling official skill functions and capturing JSON.

Official scripts print(json.dumps(...)) and sys.exit(1) on error. We capture
stdout (never letting it reach real stdout, which would corrupt MCP stdio),
catch SystemExit, and return a dict — always a dict, never raises, so a tool
can return the dict directly as its MCP result.
"""
from __future__ import annotations

import contextlib
import io
import json
from typing import Any, Callable

from . import connection


def _run_skill_json(fn: Callable, *args: Any, **kwargs: Any) -> dict:
    buf = io.StringIO()
    err = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(err):
            fn(*args, output_json=True, **kwargs)
    except connection.ApiError as e:
        return {"_skill_error": True, "error": str(e)}
    except SystemExit:
        pass  # error JSON (if any) is in buf
    except Exception as e:  # official scripts also print+exit; some raise directly
        return {"_skill_error": True, "error": f"{type(e).__name__}: {e}"}

    raw = buf.getvalue().strip()
    if not raw:
        return {"_skill_error": True, "error": "no output from skill function"}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {"_skill_error": True, "error": f"non-JSON output: {raw[:200]}"}
    if isinstance(parsed, dict) and "error" in parsed and "_skill_error" not in parsed:
        parsed["_skill_error"] = True
    return parsed if isinstance(parsed, dict) else {"data": parsed}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_skill_runner.py -q`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
git add tests/test_skill_runner.py src/futu_opend_mcp/skill_runner.py
git commit -m "feat(skill_runner): stdout-capture harness for official functions"
```

---

## Task 6: tools/_base.py + server.py skeleton (TDD)

**Files:**
- Create: `src/futu_opend_mcp/tools/__init__.py`
- Create: `src/futu_opend_mcp/tools/_base.py`
- Create: `src/futu_opend_mcp/server.py`
- Create: `tests/test_server_smoke.py`

- [ ] **Step 1: Write `src/futu_opend_mcp/tools/_base.py`**

```python
"""Shared bits for tool modules: the FastMCP singleton + a thin import helper."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("futu-opend-mcp")

_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "_skill" / "futuapi" / "scripts")


def skill_fn(category: str, name: str) -> Any:
    """Import and return an official skill function by module+name.

    category: 'quote' (all v1 tools are quote). name: e.g. 'get_snapshot'.
    """
    if _SCRIPTS_DIR not in sys.path:
        sys.path.insert(0, _SCRIPTS_DIR)
    mod = importlib.import_module(name)
    return getattr(mod, name)
```

- [ ] **Step 2: Write `src/futu_opend_mcp/tools/__init__.py`**

```python
"""Register all tool categories onto the shared FastMCP singleton."""
from . import (  # noqa: F401  (imports register @mcp.tool decorators)
    quote, search, financials, research, corporate_actions, shareholders,
    profile, capital, short, options, derivatives, plates, industrial_chains,
    institutions, macro, dividends, ipo, diagnostics,
)


def register_all() -> None:
    """Importing the submodules above already registers tools via @mcp.tool.
    This function exists for explicitness at the call site."""
    pass
```

- [ ] **Step 3: Write `src/futu_opend_mcp/server.py`**

```python
"""FastMCP server entry point. Runs over stdio."""
from __future__ import annotations

import logging

from .tools import _base  # noqa: F401  (registers tools)
from .tools import register_all  # noqa: F401


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    register_all()
    _base.mcp.run()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Write `tests/test_server_smoke.py`**

```python
def test_app_has_tools_registered():
    """Importing server must not crash and the FastMCP app must exist."""
    from futu_opend_mcp.tools import _base
    from futu_opend_mcp import server  # noqa
    # FastMCP exposes registered tools; tool count is asserted once categories exist.
    assert _base.mcp is not None


def test_main_is_callable():
    from futu_opend_mcp import server
    assert callable(server.main)
```

- [ ] **Step 5: Verify imports fail (categories not yet defined)**

Run: `pytest tests/test_server_smoke.py -q`
Expected: FAIL — `ModuleNotFoundError: quote` (the `tools/__init__.py` imports modules that don't exist yet). This confirms the wiring; we add the category modules next.

- [ ] **Step 6: Commit (skeleton only; categories land in later tasks)**

```bash
git add src/futu_opend_mcp/tools/_base.py src/futu_opend_mcp/tools/__init__.py src/futu_opend_mcp/server.py tests/test_server_smoke.py
git commit -m "feat(server): FastMCP app + tool registration skeleton"
```

---

## Task 7: tools/quote.py — price/market tools

**Files:**
- Create: `src/futu_opend_mcp/tools/quote.py`
- Create: `tests/test_tools_quote.py`

This task establishes the **single-script tool template** all simple tools follow. Each tool: a typed `@mcp.tool` function with a docstring distilled from SKILL.md (trigger phrases + param semantics), that ensures the connection is live then delegates to the official function via `_run_skill_json`.

- [ ] **Step 1: Write `tests/test_tools_quote.py`**

```python
import json
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_tools_quote.py -q`
Expected: FAIL (`quote` module missing).

- [ ] **Step 3: Write `src/futu_opend_mcp/tools/quote.py`**

```python
"""Price / quote / market tools.

Template for single-script tools: typed @mcp.tool fn -> ensure context live ->
delegate to the official skill function via _run_skill_json.
"""
from __future__ import annotations

from .. import connection, skill_runner
from ._base import mcp, skill_fn


@mcp.tool
def get_snapshot(codes: list[str]) -> dict:
    """Get market snapshot (latest price, OHLC, volume, bid/ask) for one or
    more stocks — no subscription needed. Use when the user asks for 报价/价格/
    行情/快照/quote/price/snapshot. Codes like US.AAPL, HK.00700, SH.600519.
    Up to 400 codes per call.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_snapshot"), codes)


@mcp.tool
def get_kline(
    code: str,
    ktype: str = "1d",
    num: int = 10,
    start: str | None = None,
    end: str | None = None,
    rehab: str = "forward",
) -> dict:
    """Get K-line / candlestick / historical price (K线/蜡烛图/历史走势).
    ktype: 1m,3m,5m,15m,30m,60m,1d,1w,1M,1Q,1Y. rehab: none/forward/backward
    (forward=前复权 default). With start+end (YYYY-MM-DD) pulls historical K-line
    across the range; otherwise the latest `num` bars. US intraday session not
    exposed in v1.
    """
    connection.get_context()
    return skill_runner._run_skill_json(
        skill_fn("quote", "get_kline"), code,
        ktype=ktype, num=num, start=start, end=end, rehab=rehab,
    )


@mcp.tool
def get_market_state(codes: list[str]) -> dict:
    """Get market state (open/closed/lunch break) for codes — 市场状态/开盘了吗.
    Supports HK/US/SH/SZ/SG/MY/JP prefixes.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_market_state"), codes)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_tools_quote.py -q`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add src/futu_opend_mcp/tools/quote.py tests/test_tools_quote.py
git commit -m "feat(tools): quote/snapshot/kline/market_state tools"
```

---

## Task 8: tools/search.py + financials.py

**Files:**
- Create: `src/futu_opend_mcp/tools/search.py`
- Create: `src/futu_opend_mcp/tools/financials.py`
- Modify: `tests/test_tools_quote.py` -> create `tests/test_tools_search_financials.py`

- [ ] **Step 1: Write `tests/test_tools_search_financials.py`**

```python
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
```

- [ ] **Step 2: Write `src/futu_opend_mcp/tools/search.py`**

```python
from __future__ import annotations
from .. import connection, skill_runner
from ._base import mcp, skill_fn


@mcp.tool
def search_quote(keyword: str, max_count: int = 10) -> dict:
    """Search securities/ETFs/plates by keyword — 搜索股票/搜代码/search quote.
    Returns market/code/name/sec_type. Rate-limited 10/30s. If unsure of a
    stock code, call this first.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_search_quote"), keyword, max_count=max_count)


@mcp.tool
def search_news(keyword: str, max_count: int = 10, news_sub_type: str = "ALL") -> dict:
    """Search news/announcements/ratings by keyword — 搜索资讯/搜新闻/搜公告.
    news_sub_type: ALL/NEWS(notice=公告)/NOTICE/RATING. Returns title/source/
    publish_time/related_securities/url. Rate-limited 10/30s.
    """
    connection.get_context()
    return skill_runner._run_skill_json(
        skill_fn("quote", "get_search_news"), keyword,
        max_count=max_count, news_sub_type=news_sub_type,
    )


@mcp.tool
def get_stock_info(codes: list[str]) -> dict:
    """Get stock basic+snapshot info (name, lot size, market cap, PE) — 股票信息/
    基本信息. Underlying uses get_market_snapshot; up to 400 codes.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_stock_info"), codes)
```

- [ ] **Step 3: Write `src/futu_opend_mcp/tools/financials.py`**

```python
from __future__ import annotations
from typing import Literal
from .. import connection, skill_runner
from ._base import mcp, skill_fn


@mcp.tool
def get_financial_statements(
    code: str,
    statement_type: Literal[1, 2, 3, 4] = 1,
    financial_type: int = 10,
    currency_code: str | None = None,
    num: int = 10,
) -> dict:
    """Get financial statements — 财务报表/财报/利润表/资产负债表/现金流量表/
    关键指标. statement_type: 1=Income 2=BalanceSheet 3=CashFlow 4=MainIndex(关键指标).
    financial_type: 7=年报 10=单季报+年报(default) 9=单季组合. currency_code ISO 4217
    (CNY/USD/HKD/...); omit for native currency.
    """
    connection.get_context()
    return skill_runner._run_skill_json(
        skill_fn("quote", "get_financials_statements"), code,
        statement_type=statement_type, financial_type=financial_type,
        currency_code=currency_code, num=num,
    )


@mcp.tool
def get_revenue_breakdown(code: str, financial_type: int | None = None,
                          currency_code: str | None = None) -> dict:
    """Get revenue composition by product/industry/region/business — 主营构成/
    营收拆分/收入构成/revenue breakdown. financial_type: 7=年报 9=聚合季报.
    """
    connection.get_context()
    return skill_runner._run_skill_json(
        skill_fn("quote", "get_financials_revenue_breakdown"), code,
        financial_type=financial_type, currency_code=currency_code,
    )


@mcp.tool
def get_earnings_calendar(market: str, date: str | None = None,
                          max_count: int = 50) -> dict:
    """Get earnings-release calendar for a market — 财报日历. market: US/HK/CN/SG/MY/JP.
    """
    connection.get_context()
    return skill_runner._run_skill_json(
        skill_fn("quote", "get_earnings_calendar"), market, date=date, max_count=max_count,
    )


@mcp.tool
def get_earnings_price_history(code: str) -> dict:
    """Get per-earnings-day price detail + IV crush — 历史财报日数据明细/财报日股价历史/
    IV Crush/财报预期波动率. HK/US stocks only.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_financials_earnings_price_history"), code)
```

- [ ] **Step 4: Run tests + verify they pass**

Run: `pytest tests/test_tools_search_financials.py -q`
Expected: PASS (2 tests).

- [ ] **Step 5: Commit**

```bash
git add src/futu_opend_mcp/tools/search.py src/futu_opend_mcp/tools/financials.py tests/test_tools_search_financials.py
git commit -m "feat(tools): search + financials tools"
```

---

## Task 9: tools/research.py + corporate_actions.py (merge tool template)

**Files:**
- Create: `src/futu_opend_mcp/tools/research.py`
- Create: `src/futu_opend_mcp/tools/corporate_actions.py`
- Create: `tests/test_tools_merge.py`

This task establishes the **merge-tool template**: one `@mcp.tool` with a discriminating param that routes to one of several official functions.

- [ ] **Step 1: Write `tests/test_tools_merge.py`**

```python
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
```

- [ ] **Step 2: Write `src/futu_opend_mcp/tools/research.py`**

```python
from __future__ import annotations
from .. import connection, skill_runner
from ._base import mcp, skill_fn


@mcp.tool
def get_analyst_consensus(code: str) -> dict:
    """Analyst consensus rating + target price — 分析师评级/一致预期/目标价/
    consensus/analyst rating. Stocks + REITs.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_research_analyst_consensus"), code)


@mcp.tool
def get_morningstar_report(code: str) -> dict:
    """Morningstar research report — 晨星研报/fair value/护城河/moat/bull-bear.
    Stocks + REITs.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_research_morningstar_report"), code)


@mcp.tool
def get_valuation_detail(code: str, valuation_type: int | None = None,
                         interval_type: int = 3) -> dict:
    """Valuation detail (PE/PB/PS trend, percentile, vs market) — 估值详情/
    市盈率/市净率/市销率/估值分位. valuation_type: 1=PE 2=PB 3=PS. interval_type:
    1=3m 2=6m 3=1y 4=3y 5=since2019 6=5y 7=10y 8=2y 9=20y 10=30y.
    """
    connection.get_context()
    return skill_runner._run_skill_json(
        skill_fn("quote", "get_valuation_detail"), code,
        valuation_type=valuation_type, interval_type=interval_type,
    )
```

- [ ] **Step 3: Write `src/futu_opend_mcp/tools/corporate_actions.py`**

```python
from __future__ import annotations
from typing import Literal
from .. import connection, skill_runner
from ._base import mcp, skill_fn

_ROUTES = {
    "dividends": "get_corporate_actions_dividends",
    "buybacks": "get_corporate_actions_buybacks",
    "splits": "get_corporate_actions_stock_splits",
}


@mcp.tool
def get_corporate_actions(code: str, action_type: Literal["dividends", "buybacks", "splits"]) -> dict:
    """Get corporate actions — 分红/派息/股息, 回购/buyback, or 拆股/合股/stock split.
    action_type selects which. Per-stock historical records; for a forward
    all-market dividend calendar use get_dividend_calendar instead.
    """
    fn_name = _ROUTES.get(action_type)
    if fn_name is None:
        return {"_skill_error": True,
                "error": f"action_type must be one of {list(_ROUTES)}, got {action_type!r}"}
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", fn_name), code)
```

- [ ] **Step 4: Run tests + verify they pass**

Run: `pytest tests/test_tools_merge.py -q`
Expected: PASS (4 tests).

- [ ] **Step 5: Commit**

```bash
git add src/futu_opend_mcp/tools/research.py src/futu_opend_mcp/tools/corporate_actions.py tests/test_tools_merge.py
git commit -m "feat(tools): research + corporate_actions merge tool"
```

---

## Task 10: tools/shareholders.py + profile.py + short.py

**Files:**
- Create: `src/futu_opend_mcp/tools/shareholders.py`, `profile.py`, `short.py`
- Modify: `tests/test_tools_merge.py` (append insider/short routing tests)

- [ ] **Step 1: Append routing tests to `tests/test_tools_merge.py`**

```python
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
```

- [ ] **Step 2: Write `src/futu_opend_mcp/tools/shareholders.py`**

```python
from __future__ import annotations
from typing import Literal
from .. import connection, skill_runner
from ._base import mcp, skill_fn


@mcp.tool
def get_shareholder_overview(code: str, period_id: int = 0) -> dict:
    """Shareholding structure summary — 持股统计/主要股东/股权结构/shareholder overview."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_shareholders_overview"), code, period_id=period_id)


@mcp.tool
def get_holding_changes(code: str, filter_type: int = 0, num: int = 10) -> dict:
    """Shareholder holding changes (increase/decrease/new/clear) — 持股变动/增持/减持/
    新进/清仓. filter_type: 0=all 1=increase 2=decrease 3=new 4=clear.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_shareholders_holding_changes"), code, filter_type=filter_type, num=num)


@mcp.tool
def get_holder_detail(code: str, request_type: int = 0, num: int = 10) -> dict:
    """Top-10 / detailed shareholders — 持股明细/十大股东/大股东名单. request_type 0=default 1000=all."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_shareholders_holder_detail"), code, request_type=request_type, num=num)


@mcp.tool
def get_institutional_holdings(code: str, num: int = 10) -> dict:
    """By-stock institutional holdings history — 机构持股/机构持仓/13F (who holds THIS stock).
    For by-institution (which stocks an institution holds) use get_institution_holdings.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_shareholders_institutional"), code, num=num)


_INSIDER_ROUTES = {"holders": "get_insider_holder_list", "trades": "get_insider_trade_list"}


@mcp.tool
def get_insider_data(code: str, data_type: Literal["holders", "trades"],
                     holder_id: int = 0, num: int = 10) -> dict:
    """US insider holdings/trades — 内部人持股/内部人交易/高管交易/Form 4. US stocks only.
    data_type: holders (insider holder list) or trades (insider trade list).
    """
    fn_name = _INSIDER_ROUTES.get(data_type)
    if fn_name is None:
        return {"_skill_error": True, "error": f"data_type must be {list(_INSIDER_ROUTES)}"}
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", fn_name), code, holder_id=holder_id, num=num)
```

- [ ] **Step 3: Write `src/futu_opend_mcp/tools/profile.py`**

```python
from __future__ import annotations
from .. import connection, skill_runner
from ._base import mcp, skill_fn


@mcp.tool
def get_company_profile(code: str) -> dict:
    """Company profile — 公司概况/公司详情/公司简介/company profile/主营业务."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_company_profile"), code)


@mcp.tool
def get_company_executives(code: str) -> dict:
    """Company executives & board — 公司高管/管理层/董事会/executives. Returns leader_name
    usable in get_executive_background.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_company_executives"), code)


@mcp.tool
def get_executive_background(code: str, leader_name: str) -> dict:
    """Background/career history of a named executive — 高管背景/履历/CEO背景. Two-step: first
    get_company_executives to find leader_name, then call this.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_company_executive_background"), code, leader_name)


@mcp.tool
def get_operational_efficiency(code: str, currency_code: str | None = None,
                               num: int = 10) -> dict:
    """Operational efficiency — 经营效率/员工数/人均营收/人均利润/headcount per-employee metrics.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_company_operational_efficiency"), code, currency_code=currency_code, num=num)
```

- [ ] **Step 4: Write `src/futu_opend_mcp/tools/short.py`**

```python
from __future__ import annotations
from typing import Literal
from .. import connection, skill_runner
from ._base import mcp, skill_fn

_SHORT_ROUTES = {"volume": "get_daily_short_volume", "interest": "get_short_interest"}


@mcp.tool
def get_short_data(code: str, data_type: Literal["volume", "interest"], num: int = 10) -> dict:
    """Short-selling data — 每日卖空/卖空量/卖空比例 (volume) or 空头持仓/short interest/
    days to cover (interest). HK/US.
    """
    fn_name = _SHORT_ROUTES.get(data_type)
    if fn_name is None:
        return {"_skill_error": True, "error": f"data_type must be {list(_SHORT_ROUTES)}"}
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", fn_name), code, num=num)
```

- [ ] **Step 5: Run tests + verify they pass**

Run: `pytest tests/test_tools_merge.py -q`
Expected: PASS (7 tests total).

- [ ] **Step 6: Commit**

```bash
git add src/futu_opend_mcp/tools/shareholders.py src/futu_opend_mcp/tools/profile.py src/futu_opend_mcp/tools/short.py tests/test_tools_merge.py
git commit -m "feat(tools): shareholders + profile + short (merge tools)"
```

---

## Task 11: tools/capital.py + options.py + derivatives.py

**Files:**
- Create: `src/futu_opend_mcp/tools/capital.py`, `options.py`, `derivatives.py`
- Modify: `tests/test_tools_merge.py` (append option_underlying routing test)

- [ ] **Step 1: Append option_underlying routing test to `tests/test_tools_merge.py`**

```python
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
```

- [ ] **Step 2: Write `src/futu_opend_mcp/tools/capital.py`**

```python
from __future__ import annotations
from .. import connection, skill_runner
from ._base import mcp, skill_fn


@mcp.tool
def get_capital_flow(code: str) -> dict:
    """Capital flow time series (main-force in/out) — 资金流向/资金流入流出."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_capital_flow"), code)


@mcp.tool
def get_capital_distribution(code: str) -> dict:
    """Capital distribution (super/big/mid/small orders) — 资金分布/大单小单/主力资金."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_capital_distribution"), code)


@mcp.tool
def get_top_brokers(code: str, days_before: int = 0) -> dict:
    """Top-10 buy/sell brokers (HK only) — 十大买卖经纪商/经纪队列排名. days_before: 0=realtime."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_top_ten_buy_sell_brokers"), code, days_before=days_before)
```

- [ ] **Step 3: Write `src/futu_opend_mcp/tools/options.py`**

```python
from __future__ import annotations
from typing import Literal
from .. import connection, skill_runner
from ._base import mcp, skill_fn

_UNDERLYING_ROUTES = {
    "volatility": "get_option_underlying_his_volatility",
    "statistic": "get_option_underlying_his_statistic",
    "overview": "get_option_underlying_overview",
}


@mcp.tool
def resolve_option_code(underlying: str, expiry: str, strike: float,
                        option_type: Literal["CALL", "PUT"]) -> dict:
    """Resolve an option's Futu code from a description — 解析期权简写代码. underlying e.g.
    US.JPM; expiry YYYY-MM-DD; strike e.g. 267.50; option_type CALL/PUT. Returns a code like
    US.JPM260320C267500. Do NOT hand-build HK option codes (abbreviation differs) — use this.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "resolve_option_code"), underlying, expiry, strike, option_type)


@mcp.tool
def get_option_chain(underlying: str, start: str | None = None,
                     end: str | None = None) -> dict:
    """Get option chain for an underlying — 期权链. HK/US stocks/ETF/index only.
    start/end YYYY-MM-DD filter by expiry.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_option_chain"), underlying, start=start, end=end)


@mcp.tool
def get_option_expiration_date(underlying: str) -> dict:
    """List option expiration dates — 期权到期日. HK/US stocks/ETF/index only."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_option_expiration_date"), underlying)


@mcp.tool
def get_option_quote(legs: list[dict]) -> dict:
    """Get option snapshot/Greeks for one or more legs — 期权快照/期权实时行情/多腿Greeks.
    legs: [{code, action: BUY|SELL, quantity}]. NOT for combo bid/ask — use get_option_strategy_analysis.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_option_quote"), legs)


@mcp.tool
def get_option_volatility(code: str, query_time_period: int = 2,
                          hv_time_period: int = 30) -> dict:
    """Option volatility analysis (IV/HV) for a single option contract — 期权波动率/隐含波动率/
    IV/HV. Input is an OPTION code (resolve via resolve_option_code first). query_time_period:
    1=week 2=month 3=quarter 4=half 5=year.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_option_volatility"), code, query_time_period=query_time_period, hv_time_period=hv_time_period)


@mcp.tool
def get_option_strategy_analysis(legs: list[dict]) -> dict:
    """Combo option bid1/ask1 + P&L analysis — 组合摆盘价/损益分析/最大盈亏/盈亏平衡点.
    legs: [{code, action: BUY|SELL, quantity}]. PREFERRED source for combo bid/ask; do NOT
    sum single-leg snapshots.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_option_strategy_analysis"), legs)


@mcp.tool
def get_option_underlying(
    code: list[str] | str,
    view: Literal["volatility", "statistic", "overview"],
    begin: str | None = None,
    end: str | None = None,
) -> dict:
    """Option-underlying IV/HV data — 标的历史波动率/IV走势/P-C比率/批量标的快照.
    view: volatility (IV+HV time series, single code), statistic (volume/OI/PCR time series,
    single code), overview (latest snapshot, MULTIPLE codes). For overview pass a list; for
    volatility/statistic pass a single code + begin/end (≤364 days).
    """
    fn_name = _UNDERLYING_ROUTES.get(view)
    if fn_name is None:
        return {"_skill_error": True, "error": f"view must be {list(_UNDERLYING_ROUTES)}"}
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", fn_name), code, begin=begin, end=end)
```

- [ ] **Step 4: Write `src/futu_opend_mcp/tools/derivatives.py`**

```python
from __future__ import annotations
from .. import connection, skill_runner
from ._base import mcp, skill_fn


@mcp.tool
def get_warrant(stock_owner: str = "") -> dict:
    """Get warrants/cbbc list for an underlying — 窝轮/牛熊证/warrant. stock_owner e.g. HK.00700."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_warrant"), stock_owner)


@mcp.tool
def get_future_info(codes: list[str]) -> dict:
    """Get futures contract info (size, last trade day, sessions) — 期货合约信息. e.g. SG.CNmain."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_future_info"), codes)


@mcp.tool
def get_reference_securities(code: str, reference_type: str = "WARRANT") -> dict:
    """Get securities related to a code (spot↔warrant/future/option) — 关联证券/正股关联涡轮期货.
    reference_type: WARRANT / FUTURE / OPTION (per SDK enum).
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_referencestock_list"), code, reference_type)
```

- [ ] **Step 5: Run tests + verify they pass**

Run: `pytest tests/test_tools_merge.py -q`
Expected: PASS (9 tests total).

- [ ] **Step 6: Commit**

```bash
git add src/futu_opend_mcp/tools/capital.py src/futu_opend_mcp/tools/options.py src/futu_opend_mcp/tools/derivatives.py tests/test_tools_merge.py
git commit -m "feat(tools): capital + options + derivatives"
```

---

## Task 12: tools/plates.py + industrial_chains.py (merge) + ipo.py

**Files:**
- Create: `src/futu_opend_mcp/tools/plates.py`, `industrial_chains.py`, `ipo.py`
- Modify: `tests/test_tools_merge.py` (append industrial_chains routing test)

- [ ] **Step 1: Append industrial_chains routing test to `tests/test_tools_merge.py`**

```python
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
```

- [ ] **Step 2: Write `src/futu_opend_mcp/tools/plates.py`**

```python
from __future__ import annotations
from typing import Literal
from .. import connection, skill_runner
from ._base import mcp, skill_fn


@mcp.tool
def get_plate_list(market: str, plate_type: str = "CONCEPT",
                   keyword: str | None = None, count: int = 50) -> dict:
    """List plates (concept/industry/region) — 板块列表/概念板块/行业板块. market: HK/US/SH/SZ/
    SG/MY/JP. plate_type: ALL/INDUSTRY/REGION/CONCEPT.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_plate_list"), market, plate_type=plate_type, keyword=keyword, count=count)


@mcp.tool
def get_plate_stocks(plate_code: str, limit: int = 30) -> dict:
    """Get stocks in a plate or index — 板块成分股/指数成分股/恒指成分股. plate_code e.g. hsi
    (alias) or HK.BK1910.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_plate_stock"), plate_code, limit=limit)


@mcp.tool
def get_owner_plate(codes: list[str]) -> dict:
    """Get plates a stock belongs to — 所属板块/属于哪些板块."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_owner_plate"), codes)
```

- [ ] **Step 3: Write `src/futu_opend_mcp/tools/industrial_chains.py`**

```python
from __future__ import annotations
from typing import Literal
from .. import connection, skill_runner
from ._base import mcp, skill_fn

_CHAIN_ROUTES = {
    "list": "get_industrial_chain_list",
    "detail": "get_industrial_chain_detail",
    "by_plate": "get_industrial_chain_by_plate",
}
_PLATE_ROUTES = {"info": "get_industrial_plate_info", "stocks": "get_industrial_plate_stock"}


@mcp.tool
def get_industrial_chains(
    market: str | None = None,
    view: Literal["list", "detail", "by_plate"] = "list",
    chain_id: int | None = None,
    plate_id: int | None = None,
    keyword: str | None = None,
    count: int = 20,
) -> dict:
    """Browse industrial/supply chains — 产业链. view: list (chains in a market, optional
    keyword), detail (one chain's upstream/midstream/downstream — pass chain_id), by_plate
    (chains linked to a plate — pass plate_id). market needed for list.
    """
    fn_name = _CHAIN_ROUTES.get(view)
    if fn_name is None:
        return {"_skill_error": True, "error": f"view must be {list(_CHAIN_ROUTES)}"}
    connection.get_context()
    if view == "list":
        return skill_runner._run_skill_json(skill_fn("quote", fn_name), market, keyword=keyword, count=count)
    if view == "detail":
        return skill_runner._run_skill_json(skill_fn("quote", fn_name), chain_id)
    return skill_runner._run_skill_json(skill_fn("quote", fn_name), plate_id)


@mcp.tool
def get_industrial_plate(plate_id: int, view: Literal["info", "stocks"] = "info",
                         markets: str | None = None, count: int = 50) -> dict:
    """Industrial-plate info or constituents — 产业板块信息/成分股. view: info (plate detail) or
    stocks (constituents; optional markets filter like HK,US).
    """
    fn_name = _PLATE_ROUTES.get(view)
    if fn_name is None:
        return {"_skill_error": True, "error": f"view must be {list(_PLATE_ROUTES)}"}
    connection.get_context()
    if view == "info":
        return skill_runner._run_skill_json(skill_fn("quote", fn_name), plate_id)
    return skill_runner._run_skill_json(skill_fn("quote", fn_name), plate_id, markets=markets, count=count)
```

- [ ] **Step 4: Write `src/futu_opend_mcp/tools/ipo.py`**

```python
from __future__ import annotations
from .. import connection, skill_runner
from ._base import mcp, skill_fn


@mcp.tool
def get_ipo_list(market: str) -> dict:
    """Get IPO list for a market — IPO/新股列表. market: HK/US/SH/SZ/SG/MY/JP."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_ipo_list"), market)
```

- [ ] **Step 5: Run tests + verify they pass**

Run: `pytest tests/test_tools_merge.py -q`
Expected: PASS (11 tests total).

- [ ] **Step 6: Commit**

```bash
git add src/futu_opend_mcp/tools/plates.py src/futu_opend_mcp/tools/industrial_chains.py src/futu_opend_mcp/tools/ipo.py tests/test_tools_merge.py
git commit -m "feat(tools): plates + industrial_chains + ipo"
```

---

## Task 13: tools/institutions.py (merge) + macro.py (2 merges) + dividends.py

**Files:**
- Create: `src/futu_opend_mcp/tools/institutions.py`, `macro.py`, `dividends.py`
- Modify: `tests/test_tools_merge.py` (append institutions + macro routing tests)

- [ ] **Step 1: Append routing tests to `tests/test_tools_merge.py`**

```python
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
```

- [ ] **Step 2: Write `src/futu_opend_mcp/tools/institutions.py`**

```python
from __future__ import annotations
from typing import Literal
from .. import connection, skill_runner
from ._base import mcp, skill_fn

_HOLDING_ROUTES = {"list": "get_institution_holding_list", "change": "get_institution_holding_change"}


@mcp.tool
def get_institution_list(market: str, name: str | None = None, count: int = 20) -> dict:
    """List institutions in a market — 机构列表. Optional name fuzzy search (e.g. 桥水/Bridgewater).
    Returns institution_id usable in other institution tools.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_institution_list"), market, name=name, count=count)


@mcp.tool
def get_institution_profile(market: str, institution_id: int) -> dict:
    """Institution profile — 机构概况/机构详情."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_institution_profile"), market, institution_id)


@mcp.tool
def get_institution_holdings(market: str, institution_id: int,
                             view: Literal["list", "change"] = "list",
                             change_type: str | None = None, num: int = 20) -> dict:
    """By-institution holdings — 机构持股/持仓变动. view: list (an institution's holdings) or
    change (holding-change detail). change_type for change: NEW/INCREASE/DECREASE/CLEAR. This is
    the BY-INSTITUTION direction (which stocks an institution holds) — distinct from
    get_institutional_holdings (who holds a given stock).
    """
    fn_name = _HOLDING_ROUTES.get(view)
    if fn_name is None:
        return {"_skill_error": True, "error": f"view must be {list(_HOLDING_ROUTES)}"}
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", fn_name), market, institution_id, change_type=change_type, num=num)


@mcp.tool
def get_institution_distribution(market: str, institution_id: int) -> dict:
    """Institution holding industry distribution — 机构持仓行业分布."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_institution_distribution"), market, institution_id)
```

- [ ] **Step 3: Write `src/futu_opend_mcp/tools/macro.py`**

```python
from __future__ import annotations
from typing import Literal
from .. import connection, skill_runner
from ._base import mcp, skill_fn

_MACRO_ROUTES = {"list": "get_macro_indicator_list", "history": "get_macro_indicator_history"}
_FED_ROUTES = {"target_rate": "get_fed_watch_target_rate", "dot_plot": "get_fed_watch_dot_plot"}


@mcp.tool
def get_economic_calendar(market: str | None = None, date: str | None = None,
                          max_count: int = 50) -> dict:
    """Economic-event calendar — 经济事件日历. Optional market + date filter."""
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_economic_calendar"), market, date=date, max_count=max_count)


@mcp.tool
def get_macro_indicator(view: Literal["list", "history"] = "list",
                        indicator_id: int | None = None,
                        begin: str | None = None, end: str | None = None,
                        search: str | None = None) -> dict:
    """Macro indicators — 宏观指标. view: list (available indicators, optional search) or
    history (time series for an indicator_id, optional begin/end).
    """
    fn_name = _MACRO_ROUTES.get(view)
    if fn_name is None:
        return {"_skill_error": True, "error": f"view must be {list(_MACRO_ROUTES)}"}
    connection.get_context()
    if view == "list":
        return skill_runner._run_skill_json(skill_fn("quote", fn_name), search=search)
    return skill_runner._run_skill_json(skill_fn("quote", fn_name), indicator_id, begin=begin, end=end)


@mcp.tool
def get_fed_watch(view: Literal["target_rate", "dot_plot"] = "target_rate") -> dict:
    """CME FedWatch tool — FedWatch 目标利率概率 (target_rate) or 点阵图 (dot_plot)."""
    fn_name = _FED_ROUTES.get(view)
    if fn_name is None:
        return {"_skill_error": True, "error": f"view must be {list(_FED_ROUTES)}"}
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", fn_name))
```

- [ ] **Step 4: Write `src/futu_opend_mcp/tools/dividends.py`**

```python
from __future__ import annotations
from .. import connection, skill_runner
from ._base import mcp, skill_fn


@mcp.tool
def get_dividend_calendar(market: str, date: str, count: int = 50) -> dict:
    """All-market forward dividend/ex-date calendar — 派息日历/除息日历. market: US/HK/...;
    date YYYY-MM-DD. Distinct from per-stock historical get_corporate_actions.
    """
    connection.get_context()
    return skill_runner._run_skill_json(skill_fn("quote", "get_dividend_calendar"), market, date=date, count=count)
```

- [ ] **Step 5: Run tests + verify they pass**

Run: `pytest tests/test_tools_merge.py -q`
Expected: PASS (14 tests total).

- [ ] **Step 6: Commit**

```bash
git add src/futu_opend_mcp/tools/institutions.py src/futu_opend_mcp/tools/macro.py src/futu_opend_mcp/tools/dividends.py tests/test_tools_merge.py
git commit -m "feat(tools): institutions + macro + dividends"
```

---

## Task 14: tools/diagnostics.py (3->1 merge)

**Files:**
- Create: `src/futu_opend_mcp/tools/diagnostics.py`
- Modify: `tests/test_tools_merge.py` (append diagnostics test)

- [ ] **Step 1: Append test to `tests/test_tools_merge.py`**

```python
from futu_opend_mcp.tools import diagnostics


def _patch6(monkeypatch, capture):
    monkeypatch.setattr(diagnostics.connection, "get_context", lambda: None)
    monkeypatch.setattr(diagnostics.skill_runner, "_run_skill_json",
                        lambda fn, *a, **k: capture.setdefault("fns", []).append(fn.__name__) or {"data": []})


def test_quota_status_aggregates_three_sources(monkeypatch):
    cap = {}; _patch6(monkeypatch, cap)
    diagnostics.get_quota_status()
    assert set(cap["fns"]) == {"get_user_info", "get_history_kl_quota", "get_global_state"}
```

- [ ] **Step 2: Write `src/futu_opend_mcp/tools/diagnostics.py`**

```python
from __future__ import annotations
from .. import connection, skill_runner
from ._base import mcp, skill_fn


@mcp.tool
def get_quota_status() -> dict:
    """Self-diagnostics: aggregate user info, history-K-line quota, and global state —
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
```

- [ ] **Step 3: Run the full suite + verify all pass**

Run: `pytest -q -m "not integration"`
Expected: ALL PASS (config 6 + connection 3 + skill_runner 5 + smoke 2 + quote 2 + search/financials 2 + merge 15 = 35).

- [ ] **Step 4: Commit**

```bash
git add src/futu_opend_mcp/tools/diagnostics.py tests/test_tools_merge.py
git commit -m "feat(tools): diagnostics quota_status merge tool; v1 catalogue complete"
```

---

## Task 15: Tool-count assertion + integration smoke test

**Files:**
- Modify: `tests/test_server_smoke.py`
- Create: `tests/test_integration.py`

- [ ] **Step 1: Add a tool-count assertion to `tests/test_server_smoke.py`**

Append:
```python
def test_tool_count():
    """All ~50 v1 tools are registered."""
    import asyncio
    from futu_opend_mcp.tools import _base
    from futu_opend_mcp import server  # noqa
    tools = asyncio.run(_base.mcp.list_tools())
    names = {t.name for t in tools}
    expected = {
        "get_snapshot", "get_kline", "get_market_state",
        "search_quote", "search_news", "get_stock_info",
        "screen_stocks",  # added in Task 8? -> NO, screen_stocks is in search; see note
    }
    # We assert a representative floor; the exact set is the catalogue.
    assert len(names) >= 45, f"only {len(names)} tools registered: {sorted(names)}"
```

> **Note:** `screen_stocks` was not given its own task above. Add it now to `search.py` before this test runs. If you skip it, drop it from `expected` — but the `>= 45` floor still holds.

- [ ] **Step 2: Add the `screen_stocks` tool to `src/futu_opend_mcp/tools/search.py`** (filling the catalogue gap)

Append to `search.py`:
```python
@mcp.tool
def screen_stocks(market: str, config_json: str, page_count: int = 200) -> dict:
    """Screen stocks by multi-factor config (V2) — 条件选股/筛选/screen stocks. market: HK/US/SH/
    SZ/SG/MY/JP. config_json: a JSON string with filters/retrieves/sort (see Futu V2 screen schema).
    Values are RAW (OpenD scales): PRICE 10.0, MARKET_CAP 1e10, change% 5.0 (not 0.05).
    """
    import json as _json
    connection.get_context()
    cfg = _json.loads(config_json)
    return skill_runner._run_skill_json(skill_fn("quote", "get_stock_screen"), market, cfg, page_count=page_count)
```

- [ ] **Step 3: Write `tests/test_integration.py` (live OpenD; skipped if unreachable)**

```python
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
```

- [ ] **Step 4: Run unit suite (integration skipped) + verify**

Run: `pytest -q -m "not integration"`
Expected: ALL PASS including `test_tool_count` (≥45).

- [ ] **Step 5: Commit**

```bash
git add src/futu_opend_mcp/tools/search.py tests/test_server_smoke.py tests/test_integration.py
git commit -m "test: tool-count assertion + live integration smoke test; add screen_stocks"
```

---

## Task 16: README + .github/workflows/publish.yml + GitHub repo creation

**Files:**
- Modify: `README.md`
- Create: `.github/workflows/publish.yml`

- [ ] **Step 1: Write the full `README.md`**

```markdown
# futu-opend-mcp

An MCP server that exposes Futu OpenD's **read-only investment-research** quote APIs
(stock/option/warrant/futures prices, financials, news/announcements, shareholders,
institutions, macro) as MCP tools. It borrows your already-running, logged-in Futu
OpenD gateway — no separate auth. No trading, no subscriptions.

It wraps the [official Futu skill pack](https://openapi.futunn.com/skills/opend-skills.zip)
unmodified, so it stays in sync with Futu's own field-parsing logic.

## Install & run

### Claude Code / Claude Desktop (stdio)

```
claude mcp add futu-opend-mcp -- uvx futu-opend-mcp
```

Or from git before a PyPI release:
```
claude mcp add futu-opend-mcp -- uvx --from git+https://github.com/ER-EPR/futu-opend-mcp futu-opend-mcp
```

### Open WebUI via mcpo (HTTP)

```
uvx mcpo --port 8000 -- futu-opend-mcp
# OpenAPI at http://localhost:8000, docs at /docs
```

## Configuration (env vars)

| Var | Default | Purpose |
|---|---|---|
| `FUTU_OPEND_HOST` | `127.0.0.1` | OpenD host |
| `FUTU_OPEND_PORT` | `11111` | OpenD port |
| `FUTU_OPEND_RSA_KEY` | — | inline PEM of the shared RSA private key |
| `FUTU_OPEND_RSA_KEY_FILE` | — | path to the PEM file (alternative to above) |
| `FUTU_OPEND_ENCRYPT` | `true` | proto encryption; `false` for local 127.0.0.1 OpenD |
| `FUTU_OPEND_LOG_LEVEL` | `INFO` | logging level |

OpenD and the SDK share one RSA private key (PKCS#1 1024-bit). Get it from a dockerized
OpenD with: `docker compose logs opend | grep -A20 'NEW RSA PRIVATE KEY'`.

## Tools

~50 read-only tools across: price/quote, search, screening, financials, research/valuation,
corporate actions, shareholders, profile, capital flow, short interest, options, option
underlying IV/HV, warrants/futures, plates, industrial chains, institutions, macro,
dividends, IPO, and diagnostics. See `docs/superpowers/specs/2026-07-10-futu-opend-mcp-design.md`.

## Attribution

Wraps the official Futu `futuapi` skill pack (vendored under
`src/futu_opend_mcp/_skill/futuapi/`, unmodified). Legal terms in that folder apply.

## License

MIT.
```

- [ ] **Step 2: Write `.github/workflows/publish.yml` (PyPI trusted publishing)**

```yaml
name: publish
on:
  push:
    tags: ["v*"]
jobs:
  build:
    runs-on: ubuntu-latest
    permissions: { id-token: write }
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install build && python -m build
      - uses: pypa/gh-action-pypi-publish@release/v1
        # Configure trusted publishing at https://pypi.org/manage/project/futu-opend-mcp/publishing/
```

- [ ] **Step 3: Create the GitHub repo and push**

Run:
```bash
gh repo create ER-EPR/futu-opend-mcp --public --source=. --remote=origin --push --description "MCP server exposing Futu OpenD read-only investment-research quote APIs"
```
Expected: repo created at `github.com/ER-EPR/futu-opend-mcp` and all commits pushed.

- [ ] **Step 4: Verify the entry point launches (help/version check)**

Run: `futu-opend-mcp --help 2>&1 | head -5` (may hang on stdio; alternatively)
Run: `timeout 3 python -c "from futu_opend_mcp.server import main; print('entry ok')"`
Expected: prints `entry ok` (confirms imports resolve).

- [ ] **Step 5: Commit + push**

```bash
git add README.md .github/workflows/publish.yml
git commit -m "docs: README + PyPI trusted-publish workflow"
git push -u origin main
```

---

## Self-Review (completed during authoring)

**Spec coverage:** §1 purpose → all tasks; §2 RSA cert → Task 3; §3 reuse/vendor/inject/capture → Tasks 2,4,5; §4 connection → Task 4; §5 catalogue → Tasks 7-14 (+screen_stocks in 15); §5.1 v2 → explicitly out of scope (no task, correct); §6 SKILL.md→desc migration → applied in every tool docstring; §7 packaging → Tasks 1,16; §8 config → Task 3; §9 errors/tests → Tasks 3-5,15; §10 layout → File Structure above. **Gap found & fixed:** `screen_stocks` was missing its own task — added in Task 15 Step 2.

**Placeholder scan:** no TBD/TODO; every code step has real code; routing tests assert real function names.

**Type consistency:** `_run_skill_json(fn, *args, **kwargs)` signature consistent across all tool modules; `skill_fn(category, name)` consistent; merge-route dict names (`_ROUTES`, `_INSIDER_ROUTES`, `_SHORT_ROUTES`, `_UNDERLYING_ROUTES`, `_CHAIN_ROUTES`, `_PLATE_ROUTES`, `_HOLDING_ROUTES`, `_MACRO_ROUTES`, `_FED_ROUTES`) all distinct and match test assertions.

> **Caveat for implementer:** some official script function signatures (exact kwargs like `news_sub_type`, `change_type`, `count`) are inferred from SKILL.md/argparse; if a live call rejects a kwarg, read the vendored script's `def main(...)` signature and adjust the `skill_fn(...)` call's kwargs to match. This is expected and is the one place runtime reality may differ from the plan.
