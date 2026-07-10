# futu-opend-mcp

An MCP server that exposes Futu OpenD's **read-only investment-research** quote APIs
(stock/option/warrant/futures prices, financials, news/announcements, shareholders,
institutions, macro) as MCP tools. It borrows your already-running, logged-in Futu
OpenD gateway - no separate auth. No trading, no subscriptions.

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

### MCP JSON config

Add to `~/.claude/settings.json`, `.mcp.json`, or Claude Desktop config:

**Remote OpenD (with encryption):**
```json
{
  "mcpServers": {
    "futu-opend": {
      "command": "uvx",
      "args": ["futu-opend-mcp"],
      "env": {
        "FUTU_OPEND_HOST": "your-opend-host",
        "FUTU_OPEND_PORT": "11111",
        "FUTU_OPEND_ENCRYPT": "true",
        "FUTU_OPEND_RSA_KEY": "-----BEGIN RSA PRIVATE KEY-----\\nMIIC...\\n-----END RSA PRIVATE KEY-----"
      }
    }
  }
}
```

**Local OpenD (no encryption):**
```json
{
  "mcpServers": {
    "futu-opend": {
      "command": "uvx",
      "args": ["futu-opend-mcp"],
      "env": {
        "FUTU_OPEND_ENCRYPT": "false"
      }
    }
  }
}
```

Extract the RSA key for the env var:
```bash
docker exec futu-opend cat /rsa/rsa_private_pkcs1.pem | awk '{printf "%s\\n", $0}'
```

## Configuration (env vars)

| Var | Default | Purpose |
|---|---|---|
| `FUTU_OPEND_HOST` | `127.0.0.1` | OpenD host |
| `FUTU_OPEND_PORT` | `11111` | OpenD port |
| `FUTU_OPEND_RSA_KEY` | - | inline PEM of the shared RSA private key |
| `FUTU_OPEND_RSA_KEY_FILE` | - | path to the PEM file (alternative to above) |
| `FUTU_OPEND_ENCRYPT` | `true` | proto encryption; `false` for local 127.0.0.1 OpenD |
| `FUTU_OPEND_LOG_LEVEL` | `INFO` | logging level |

OpenD and the SDK share one RSA private key (PKCS#1 1024-bit). Get it from a dockerized
OpenD with: `docker compose logs opend | grep -A20 'NEW RSA PRIVATE KEY'`.

## Tools

~50 read-only tools across: price/quote, search, screening, financials, research/valuation,
corporate actions, shareholders, profile, capital flow, short interest, options, option
underlying IV/HV, warrants/futures, plates, industrial chains, institutions, macro,
dividends, IPO, and diagnostics. See `docs/superpowers/specs/2026-07-10-futu-opend-mcp-design.md`.

## Development

```
pip install -e ".[dev]"
pytest -q -m "not integration"   # unit tests (no OpenD needed)
ruff check .
```

Live-OpenD integration tests are marked `integration` and skip themselves when OpenD is
unreachable. Re-vendor the official skill pack with `./scripts/sync_skill.sh`.

## Attribution

Wraps the official Futu `futuapi` skill pack (vendored under
`src/futu_opend_mcp/_skill/futuapi/`, unmodified). Legal terms in that folder apply.

## License

MIT.
