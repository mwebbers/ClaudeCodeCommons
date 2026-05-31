# CLAUDE.md

Context for Claude Code in this repo. Keep this short — it loads on every session.

## What this is

`claude-code-commons` is a **library**, not a routine. It holds the small,
vendor-agnostic, **standard-library-only** helpers shared by Claude routine
repos: `env_required`/`env_opt`/`env_get`, `parse_num`, `currency_symbol`,
`build_remote_path`, `log`. It has **no vendor or report logic and no third-party
dependency**.

There is no scheduled-task/operator section here — this package does not run on
its own. It is consumed by the routine repos and by vendor toolkits (e.g.
`claude-woocommerce-commons`), which own their own runtime contracts.

## Read first

Read `SCOPE.md` before changing anything. Every feature has an ID (`F-001`…) and
must stay covered by a test (`tests/test_scope_coverage.py` enforces it).

## Working rules

- Any behaviour change starts in `SCOPE.md`: add/edit a feature ID, then write or
  update its test, then change the code. Never the other way around.
- Every test is tagged `@pytest.mark.feature("F-00X")`.
- Run `pytest` after any change.
- After a behaviour change, add a line under `[Unreleased]` in `CHANGELOG.md`.
- **No third-party dependency, ever.** The whole point is that a routine can
  install this without pulling in heavier libraries. Anything needing `requests`,
  `openpyxl`, etc. belongs in a vendor toolkit that depends on this, not here.
- **This is a dependency of routines and vendor toolkits.** A breaking change to a
  public name must bump the version and be rolled out to each consumer by bumping
  its pin. Prefer additive changes.

## Deployment floor

`requires-python` is `>=3.9` and CI runs a `3.9` / `3.11` / `3.12` matrix. The
Cowork sandbox that runs scheduled routines is **Python 3.11**, so a consumer that
`pip install`s this must be able to; keeping the floor at the lowest interpreter
any routine runs on (and testing it) guarantees that.

## Commands

- Install (editable, with tests): `pip install -e ".[test]"`
- Run tests: `pytest`
- The package exposes a single top-level module:
  `from code_commons import env_required, env_opt, parse_num, build_remote_path, currency_symbol, log`
