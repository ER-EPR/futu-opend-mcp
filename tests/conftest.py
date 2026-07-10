import os
import pytest


@pytest.fixture
def clean_env(monkeypatch):
    """Strip all FUTU_OPEND_* env vars so each test starts clean."""
    for k in list(os.environ):
        if k.startswith("FUTU_OPEND_"):
            monkeypatch.delenv(k, raising=False)
    return monkeypatch
