# Changelog

All notable changes to this package are documented here. Each behaviour change
references the SCOPE.md feature ID(s) it implements.

The format follows [Keep a Changelog](https://keepachangelog.com/); the project
adheres to semantic versioning.

## [Unreleased]

## [1.0.1] - 2026-06-11

### Changed
- Docs only (no public-surface change): `CONTRIBUTING.md` makes lint + format an
  explicit step in the dev loop, and `CLAUDE.md` / `CONTRIBUTING.md` add the
  adversarial-diff *review* as the final pre-commit step — aligning this repo
  with the family-wide dev-loop convention.
- CI: bump the GitHub Actions group (3 updates) via Dependabot.

## [1.0.0] - 2026-06-06

First stable release — the public surface is considered stable; this is the v1.0
milestone for the Claude routine family.

### Added
- Self-contained trunk-on-main `CONTRIBUTING.md`, `LICENSE` (MIT) + `license`
  field, `.github/workflows/release.yml` (tag -> GitHub Release) and
  `.github/dependabot.yml` (weekly pip + actions PRs).
- Code-coverage gate: `pytest-cov`, **fail_under = 80** in `[tool.coverage]`.
- Ruff lint + format gate (`[tool.ruff]`), run in CI before the tests.

### Changed
- CI: `ruff check` + `ruff format --check` before `pytest`; `actions/checkout` -> v5.
- Code reformatted by `ruff format` (no behaviour change); `.gitignore` ignores
  coverage artefacts.

## [0.3.0] - 2026-06-01

### Changed
- **[F-001]** — **BREAKING (behaviour).** The env helpers (`env_required`,
  `env_opt`/`env_get`, `env_int`, `env_float`) gain a `shared: bool = False`
  keyword. With a prefix set, the unprefixed fallback now applies **only** when
  `shared=True`; with `shared=False` (the new default) a prefixed lookup reads
  **only** `<prefix>_<key>`. The no-prefix (standalone) path is unchanged. Mark
  family-shared credentials/infra (`WC_*`, `DROPBOX_*`) with `shared=True`;
  routine-own knobs stay prefix-only so they cannot leak between sibling routines
  sharing one environment. Consumers roll forward by bumping the pin and marking
  their shared keys.

### Added
- **[F-007]** Prefix-required routine-own keys with a one-time migration warning.
  When a prefix-required lookup (`shared=False`) misses but the unprefixed form
  **is** set, the helpers emit a one-time `WARNING:` to stderr naming both forms
  (the stray value is ignored), so an old-style unprefixed value surfaces loudly
  instead of silently reverting to the default. The numeric helpers (F-006) honour
  the same flag and warning.

## [0.2.0] - 2026-06-01

### Added
- **[F-006]** `env_int(key, default=None, *, prefix="")` and `env_float(...)` —
  numeric env helpers using the same project-prefix-with-fallback lookup as
  `env_opt`, returning `default` when unset and aborting with a clear `SystemExit`
  naming the variable (`Invalid <KEY>='<value>': expected an integer.` /
  `… a number.`) when the value is set but malformed, instead of an uncaught
  `ValueError`. Folds the per-routine `_int`/`_float` helpers the WooCommerce
  family each carried into the shared core (review Step 9). Additive — existing
  names unchanged.

## [0.1.0] - 2026-05-31

Initial release: the vendor-agnostic, standard-library-only core, extracted from
`claude-woocommerce-commons` so every routine — not only the WooCommerce family —
can share one tested copy of the generic plumbing instead of re-implementing it
(review thread T-1 / option C: a dependency-light core + a thin vendor toolkit on
top).

### Added
- **F-001** `env_required` / `env_opt` / `env_get` environment helpers with the
  project-prefix-with-fallback lookup.
- **F-002** Tolerant `parse_num()` (comma thousands separators; comma-decimal
  locale input documented as out of scope).
- **F-003** `build_remote_path(base, folder, filename)` remote-path builder.
- **F-004** `currency_symbol()` 3-letter-code → display symbol.
- **F-005** `log()` timestamped run-log line.
