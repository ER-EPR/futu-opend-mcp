"""Env-var parsing, validation, and RSA-key tempfile materialization.

No `futu` imports here - keep this pure so it is unit-testable without OpenD.
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
