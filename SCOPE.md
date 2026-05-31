# Scope

This document is the **single source of truth** for what this package does and
why. The README explains *how to use* it; this file defines *what it must do*.
Every feature below has an ID. Every feature ID must be covered by at least one
test (enforced by `tests/test_scope_coverage.py`). Do not add, change, or remove
a feature here without updating the tests — that is how current behaviour is
guaranteed across future changes.

## Purpose

`claude-code-commons` is the small, **vendor-agnostic, standard-library-only**
toolkit shared by Claude routine repos. It owns the generic helpers every routine
tends to re-implement — environment lookup, tolerant number parsing, currency
symbols, remote-path building and a run-log line — with **no third-party
dependency**, so any routine can install it without dragging in a web client or a
spreadsheet engine. Vendor-specific toolkits (e.g. a WooCommerce REST client)
build on top of it.

## Why it exists

Every routine needs the same handful of helpers. Copying them into each repo lets
the copies drift — a fix made in one is missed in the others. One tiny,
dependency-free package, versioned and tested in isolation, removes that hazard
and keeps the heavier vendor toolkits thin: they import the core and add only
their vendor-specific parts.

## Features (acceptance criteria)

Each feature is testable. The ID in brackets is referenced by tests via
`@pytest.mark.feature("F-00X")`.

- **[F-001] Environment helpers with project-prefix fallback.** `env_required(key,
  *, prefix="")` and `env_opt(key, default, *, prefix="")` — with `env_get` as a
  convenience alias of `env_opt` — resolve a variable by trying `<prefix>_<key>`
  first and falling back to the unprefixed `<key>` (plain `<key>` with no prefix,
  backward compatible). `env_required` aborts with a clear `SystemExit` naming the
  variable when neither form is set; `env_opt`/`env_get` return `default`. This
  lets a family of routines share one environment: shared values set once
  unprefixed, per-routine values set prefixed so they never collide.

- **[F-002] Tolerant number parsing.** `parse_num()` accepts comma **thousands**
  separators (`"1,234"` → `1234.0`), plain numbers and numeric strings, and
  returns `0.0` for `None`, `""` or unparseable input — it never raises. A comma
  is always a thousands separator (dot-decimal domain); comma-**decimal** locale
  input (`"1,5"` → `15.0`, not `1.5`) is out of scope and handled by per-routine
  locale parsers.

- **[F-003] Remote-path builder.** `build_remote_path(base, folder, filename)`
  joins an optional base directory, an optional sub-folder and a filename into one
  absolute, slash-normalised path. Lets a family share one base
  (`DROPBOX_PATH`) while each writes into its own `<PREFIX>_DROPBOX_FOLDER`
  sub-folder: base `/Reports` + folder `Stock` → `/Reports/Stock/<filename>`. An
  empty/None folder drops the file straight into `base`; an empty/None base falls
  back to the root — so an unset folder reproduces the previous single-directory
  behaviour (backward compatible).

- **[F-004] Currency symbols.** `currency_symbol(code)` maps a 3-letter currency
  code to a display symbol (case-insensitive), falling back to the upper-cased
  code itself for unmapped currencies.

- **[F-005] Timestamped run log.** `log(msg)` prints a flushed `[HH:MM:SS] msg`
  line to stdout — the shared run-log format the routines use.

## Out of scope

Anything vendor-specific (a WooCommerce/Shopify/… client, shop meta keys);
network access of any kind (this package makes no network calls); spreadsheet or
file I/O; currency *conversion* (only symbol labelling); and locale-aware
comma-decimal parsing. Vendor toolkits and the routines themselves own those. If a
new generic, dependency-free helper is ever needed, add a feature ID here first,
then a test, then the code.
