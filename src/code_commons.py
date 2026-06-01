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
import sys
from datetime import datetime
from typing import Any


# ---------------------------------------------------------------------------
# Environment: project prefix with shared fallback
# ---------------------------------------------------------------------------


# Tracks (prefix, key) pairs already warned about, so the migration warning (F-007)
# fires once per process per variable rather than on every lookup. Exposed as a
# module global so tests can reset it between cases.
_WARNED_PREFIX_KEYS: set[tuple[str, str]] = set()


def _env_lookup(key: str, prefix: str, shared: bool = False) -> str | None:
    """Resolve a variable, honouring the project-prefix convention (F-001, F-007).

    With no prefix this is a plain ``<key>`` lookup (backward compatible). With a
    prefix set, behaviour depends on ``shared``:

    - ``shared=True`` — a family-shared credential/infra value: try
      ``<prefix>_<key>`` first, then fall back to the unprefixed ``<key>``, so a
      family of routines can share one environment with the shared values set once
      unprefixed.
    - ``shared=False`` (default) — a routine-own knob: read **only**
      ``<prefix>_<key>``. The unprefixed form is not read, so a knob set unprefixed
      in a shared environment cannot leak between sibling routines. If the
      unprefixed form *is* set while the prefixed one is not, emit a one-time
      stderr warning naming both forms (the stray value is still ignored).

    Returns the first set & non-empty (stripped) value, or None.
    """
    if not prefix:
        names: tuple[str, ...] = (key,)
    elif shared:
        names = (f"{prefix}_{key}", key)
    else:
        names = (f"{prefix}_{key}",)
    for name in names:
        v = os.environ.get(name, "").strip()
        if v:
            return v
    # Prefix-required miss: warn once if a stray unprefixed value is being ignored.
    if prefix and not shared and os.environ.get(key, "").strip():
        pair = (prefix, key)
        if pair not in _WARNED_PREFIX_KEYS:
            _WARNED_PREFIX_KEYS.add(pair)
            print(
                f"WARNING: {prefix}_{key} is not set; ignoring a plain {key} in the "
                f"environment. Routine-own keys are read only with the {prefix} "
                f"prefix — rename it to {prefix}_{key} (shared family credentials "
                f"still allow the unprefixed form).",
                file=sys.stderr,
                flush=True,
            )
    return None


def env_required(key: str, *, prefix: str = "", shared: bool = False) -> str:
    """Return a required env var, stripped, via the project-prefix lookup. Aborts
    the run with a clear SystemExit naming the variable when it is not set. A
    routine never falls back to a placeholder for a credential or URL.

    Pass ``shared=True`` for family-shared credentials/infra so the unprefixed
    form is still read; routine-own keys (the default) are prefix-only — see
    :func:`_env_lookup`."""
    v = _env_lookup(key, prefix, shared)
    if not v:
        suffix = f" (or {prefix}_{key})" if prefix and shared else ""
        name = f"{prefix}_{key}" if prefix and not shared else key
        raise SystemExit(f"Missing required env var: {name}{suffix}")
    return v


def env_opt(
    key: str, default: str | None = None, *, prefix: str = "", shared: bool = False
) -> str | None:
    """Return an optional env var, stripped, via the project-prefix lookup, or
    ``default`` when not set. Pass ``shared=True`` for family-shared values (see
    :func:`_env_lookup`)."""
    v = _env_lookup(key, prefix, shared)
    return v if v is not None else default


# Convenience alias: the single-function spelling some routines prefer. Identical
# to env_opt (optional, prefix-with-fallback, returns ``default`` when unset).
env_get = env_opt


def env_int(
    key: str, default: int | None = None, *, prefix: str = "", shared: bool = False
) -> int | None:
    """Optional env var parsed as an ``int``, via the project-prefix lookup. Returns
    ``default`` when unset (``shared`` controls the unprefixed fallback, see
    :func:`_env_lookup`).

    When the value **is** set but is not a valid integer, this aborts with a clear
    ``SystemExit`` naming the variable (``Invalid <KEY>='<value>': expected an
    integer.``) instead of raising an uncaught ``ValueError`` mid-run — so a typo in
    a numeric knob fails a routine's ``--dry-run`` config check cleanly. ``default``
    is returned as-is and never re-parsed (F-006)."""
    raw = _env_lookup(key, prefix, shared)
    if raw is None:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        raise SystemExit(f"Invalid {key}={raw!r}: expected an integer.")


def env_float(
    key: str, default: float | None = None, *, prefix: str = "", shared: bool = False
) -> float | None:
    """Optional env var parsed as a ``float`` (see :func:`env_int`). Returns
    ``default`` when unset; aborts with a clear ``SystemExit`` naming the variable
    (``Invalid <KEY>='<value>': expected a number.``) when set but malformed (F-006)."""
    raw = _env_lookup(key, prefix, shared)
    if raw is None:
        return default
    try:
        return float(raw)
    except (TypeError, ValueError):
        raise SystemExit(f"Invalid {key}={raw!r}: expected a number.")


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
