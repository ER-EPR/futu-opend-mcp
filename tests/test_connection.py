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
