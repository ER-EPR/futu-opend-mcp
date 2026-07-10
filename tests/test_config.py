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
