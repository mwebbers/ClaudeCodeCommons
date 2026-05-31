# Changelog

All notable changes to this package are documented here. Each behaviour change
references the SCOPE.md feature ID(s) it implements.

The format follows [Keep a Changelog](https://keepachangelog.com/); the project
adheres to semantic versioning.

## [Unreleased]

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
