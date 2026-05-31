"""Vendor-agnostic plumbing shared by Claude routine repos.

Standard-library only — no third-party dependency — so any routine can depend on
it without dragging in a web client or spreadsheet engine. It owns the small,
generic helpers every routine tends to re-implement:

  - env_required / env_opt / env_get  — project-prefix-with-fallback env lookup
  - parse_num                         — tolerant numeric parsing of loose JSON
  - currency_symbol                   — 3-letter code -> display symbol
  - build_remote_path                 — join a base + sub-folder + filename
  - log                               — timestamped stdout line

Nothing here knows about any specific vendor or report. Heavier, vendor-specific
toolkits (e.g. a WooCommerce REST client) build on top of it.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any


# ---------------------------------------------------------------------------
# Environment: project prefix with shared fallback
# ---------------------------------------------------------------------------


def _env_lookup(key: str, prefix: str) -> str | None:
    """Project-prefix-with-fallback lookup: try ``<prefix>_<key>`` first, then the
    unprefixed ``<key>``. Returns the first set & non-empty (stripped) value, or
    None. With no prefix this is a plain ``<key>`` lookup (backward compatible).

    This lets a family of routines share one environment: shared values
    (credentials, tokens, common knobs) are set once unprefixed and reached via
    the fallback, while per-routine values are set prefixed so they never collide.
    """
    names = (f"{prefix}_{key}", key) if prefix else (key,)
    for name in names:
        v = os.environ.get(name, "").strip()
        if v:
            return v
    return None


def env_required(key: str, *, prefix: str = "") -> str:
    """Return a required env var, stripped, via the project-prefix-with-fallback
    lookup. Aborts the run with a clear SystemExit naming the variable when
    neither the prefixed nor the unprefixed form is set. A routine never falls
    back to a placeholder for a credential or URL."""
    v = _env_lookup(key, prefix)
    if not v:
        suffix = f" (or {prefix}_{key})" if prefix else ""
        raise SystemExit(f"Missing required env var: {key}{suffix}")
    return v


def env_opt(key: str, default: str | None = None, *, prefix: str = "") -> str | None:
    """Return an optional env var, stripped, via the project-prefix-with-fallback
    lookup, or ``default`` when neither form is set/non-empty."""
    v = _env_lookup(key, prefix)
    return v if v is not None else default


# Convenience alias: the single-function spelling some routines prefer. Identical
# to env_opt (optional, prefix-with-fallback, returns ``default`` when unset).
env_get = env_opt


# ---------------------------------------------------------------------------
# Tolerant numeric parsing
# ---------------------------------------------------------------------------


def parse_num(v: Any) -> float:
    """Parse the loosely-typed numbers JSON APIs return.

    Domain: dot-decimal numbers, optionally with comma **thousands** separators
    (``"1,234"`` -> ``1234.0``, ``"1,234.56"`` -> ``1234.56``). Plain numbers and
    numeric strings work; ``None``, ``""`` and anything unparseable return
    ``0.0`` — it never raises.

    NOT for comma-**decimal** locale input (e.g. the Dutch ``"1,5"`` meaning 1.5):
    a comma is always treated as a thousands separator here, so ``"1,5"`` parses
    to ``15.0``. Routines that ingest comma-decimal CSVs must use their own
    locale-aware parser, not this one.
    """
    if v is None or v == "":
        return 0.0
    try:
        return float(str(v).replace(",", ""))
    except (ValueError, TypeError):
        return 0.0


def log(msg: str) -> None:
    """Print a flushed ``[HH:MM:SS] msg`` line to stdout — the shared run-log format."""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Currency symbols
# ---------------------------------------------------------------------------

# Known currency code -> display symbol. Codes not in the table fall back to the
# 3-letter code itself, which is always valid in Excel number formats.
CURRENCY_SYMBOLS = {
    "EUR": "€", "USD": "$", "GBP": "£", "CHF": "CHF",
    "DKK": "kr", "SEK": "kr", "NOK": "kr", "ISK": "kr",
    "JPY": "¥", "CNY": "¥",
    "CAD": "$", "AUD": "$", "NZD": "$", "HKD": "$",
    "PLN": "zł", "CZK": "Kč", "HUF": "Ft",
}


def currency_symbol(code: str) -> str:
    """Return a display symbol for a 3-letter currency code, falling back to the
    upper-cased code itself for currencies we have not mapped."""
    return CURRENCY_SYMBOLS.get((code or "").upper(), (code or "").upper())


# ---------------------------------------------------------------------------
# Remote-path builder
# ---------------------------------------------------------------------------


def build_remote_path(base: str | None, folder: str | None, filename: str) -> str:
    """Join an optional base directory, an optional sub-folder and a filename into
    one absolute, '/'-separated remote path, normalising slashes.

    Lets a family of routines share one base (e.g. ``DROPBOX_PATH``) while each
    writes into its own sub-folder (``<PREFIX>_DROPBOX_FOLDER``): base
    ``/Reports`` + folder ``Stock`` -> ``/Reports/Stock/<filename>``. An
    empty/None folder drops the file straight into ``base``; an empty/None base
    falls back to the root — so an unset folder reproduces the previous
    single-directory behaviour. A trailing or duplicate ``/`` in either segment
    does not matter.
    """
    parts: list[str] = []
    for seg in (base, folder):
        if seg:
            parts += [p for p in seg.strip("/").split("/") if p]
    return ("/" + "/".join(parts) + "/" + filename) if parts else "/" + filename
