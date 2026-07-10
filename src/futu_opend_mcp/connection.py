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
from pathlib import Path
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
        (Path(__file__).resolve().parent
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
