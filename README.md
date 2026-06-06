# Claude Code Commons

Vendor-agnostic, **standard-library-only** plumbing shared by Claude routine
repos. One tiny installable package, versioned and tested in isolation, so a fix
lands in every routine at once instead of being copy-pasted — and with **no
third-party dependency**, so a routine can adopt it without pulling in a web
client or spreadsheet engine.

It contains **no vendor or report logic** — only the generic helpers routines
have in common. Heavier, vendor-specific toolkits (e.g.
`claude-woocommerce-commons`) build on top of it.

## What's inside

| Area | API |
|------|-----|
| Env | `env_required(key, *, prefix)`, `env_opt(key, default, *, prefix)`, `env_get` (alias of `env_opt`) |
| Parsing | `parse_num()` — tolerant of loose JSON (comma thousands separators) |
| Currency | `currency_symbol(code)` — 3-letter code → display symbol |
| Paths | `build_remote_path(base, folder, filename)` — slash-normalised join |
| Logging | `log(msg)` — `[HH:MM:SS] msg`, flushed |

See `SCOPE.md` for the full feature contract.

## Install

```bash
pip install -e ".[test]"        # local dev (editable) + pytest
```

The package exposes a single top-level module:

```python
from code_commons import env_required, env_opt, parse_num, build_remote_path, log

url = env_required("WC_URL", prefix="STOCK")        # STOCK_WC_URL, else WC_URL
path = build_remote_path("/Reports", "Stock", "report.xlsx")  # /Reports/Stock/report.xlsx
```

## Tests

```bash
pytest
```

A coverage test (`tests/test_scope_coverage.py`) fails if any `SCOPE.md` feature
lacks a test or a test references a feature not in `SCOPE.md`.

## Contributing

Branching is **trunk-on-main**, and releases go through a strict
version = changelog = tag gate. See [CONTRIBUTING.md](./CONTRIBUTING.md) for the full
procedure and the `ruff` + `pytest` quality gates.
