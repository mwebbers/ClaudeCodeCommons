"""Tests for the vendor-agnostic core helpers. Each test is tagged with the
SCOPE.md feature it covers. Standard library only — nothing here touches a
network or the filesystem.
"""

import pytest

import code_commons as C


# ---------------------------------------------------------------------------
# F-001 Environment helpers
# ---------------------------------------------------------------------------


@pytest.mark.feature("F-001")
def test_env_required_present_and_missing(monkeypatch):
    monkeypatch.setenv("THING", "  value  ")
    assert C.env_required("THING") == "value"          # stripped
    monkeypatch.delenv("THING", raising=False)
    with pytest.raises(SystemExit) as exc:
        C.env_required("THING")
    assert "THING" in str(exc.value)


@pytest.mark.feature("F-001")
def test_env_prefix_with_fallback(monkeypatch):
    for k in ("WC_URL", "STOCK_WC_URL", "STOCK_KNOB", "KNOB"):
        monkeypatch.delenv(k, raising=False)
    # Prefixed value wins when set.
    monkeypatch.setenv("STOCK_WC_URL", "https://prefixed")
    monkeypatch.setenv("WC_URL", "https://shared")
    assert C.env_required("WC_URL", prefix="STOCK") == "https://prefixed"
    # Falls back to the shared unprefixed value when the prefixed one is absent.
    monkeypatch.delenv("STOCK_WC_URL", raising=False)
    assert C.env_required("WC_URL", prefix="STOCK") == "https://shared"
    # env_opt: prefixed override, else unprefixed, else default.
    monkeypatch.setenv("STOCK_KNOB", "10")
    assert C.env_opt("KNOB", "0", prefix="STOCK") == "10"
    monkeypatch.delenv("STOCK_KNOB", raising=False)
    monkeypatch.setenv("KNOB", "5")
    assert C.env_opt("KNOB", "0", prefix="STOCK") == "5"
    monkeypatch.delenv("KNOB", raising=False)
    assert C.env_opt("KNOB", "0", prefix="STOCK") == "0"


@pytest.mark.feature("F-001")
def test_env_get_is_env_opt_alias(monkeypatch):
    # env_get is the single-function spelling of env_opt (same prefix fallback).
    for k in ("KNOB", "STOCK_KNOB"):
        monkeypatch.delenv(k, raising=False)
    assert C.env_get("KNOB", "def", prefix="STOCK") == "def"
    monkeypatch.setenv("KNOB", "5")
    assert C.env_get("KNOB", prefix="STOCK") == "5"           # unprefixed fallback
    monkeypatch.setenv("STOCK_KNOB", "9")
    assert C.env_get("KNOB", prefix="STOCK") == "9"           # prefixed wins
    assert C.env_get is C.env_opt


@pytest.mark.feature("F-001")
def test_env_required_missing_names_both_forms(monkeypatch):
    monkeypatch.delenv("WC_URL", raising=False)
    monkeypatch.delenv("STOCK_WC_URL", raising=False)
    with pytest.raises(SystemExit) as exc:
        C.env_required("WC_URL", prefix="STOCK")
    msg = str(exc.value)
    assert "WC_URL" in msg and "STOCK_WC_URL" in msg


# ---------------------------------------------------------------------------
# F-002 Tolerant number parsing
# ---------------------------------------------------------------------------


@pytest.mark.feature("F-002")
@pytest.mark.parametrize("raw,expected", [
    ("1,234", 1234.0), ("1,234.56", 1234.56), ("12.5", 12.5), (None, 0.0),
    ("", 0.0), ("garbage", 0.0), (7, 7.0), ([], 0.0),
])
def test_parse_num(raw, expected):
    assert C.parse_num(raw) == expected


@pytest.mark.feature("F-002")
def test_parse_num_comma_is_thousands_not_decimal():
    # Documented contract: a comma is a THOUSANDS separator (dot-decimal domain),
    # so comma-decimal locale input is intentionally out of scope.
    assert C.parse_num("1,5") == 15.0   # NOT 1.5


# ---------------------------------------------------------------------------
# F-003 Remote-path builder
# ---------------------------------------------------------------------------


@pytest.mark.feature("F-003")
@pytest.mark.parametrize("base,folder,expected", [
    ("/Reports", "Stock", "/Reports/Stock/r.xlsx"),
    ("/Reports/", "Stock", "/Reports/Stock/r.xlsx"),    # trailing slash on base
    ("/Reports", "", "/Reports/r.xlsx"),                # empty folder -> into base
    ("/Reports", None, "/Reports/r.xlsx"),              # unset folder -> into base
    (None, "Stock", "/Stock/r.xlsx"),                   # no base -> folder at root
    ("", "", "/r.xlsx"),                                # both empty -> root
    (None, None, "/r.xlsx"),
    ("/a/b/", "/c/d/", "/a/b/c/d/r.xlsx"),              # nested + stray slashes
])
def test_build_remote_path(base, folder, expected):
    assert C.build_remote_path(base, folder, "r.xlsx") == expected


# ---------------------------------------------------------------------------
# F-004 Currency symbols
# ---------------------------------------------------------------------------


@pytest.mark.feature("F-004")
def test_currency_symbol():
    assert C.currency_symbol("EUR") == "€"
    assert C.currency_symbol("usd") == "$"          # case-insensitive
    assert C.currency_symbol("XYZ") == "XYZ"        # unmapped -> code itself
    assert C.currency_symbol("") == ""


# ---------------------------------------------------------------------------
# F-005 Timestamped run log
# ---------------------------------------------------------------------------


@pytest.mark.feature("F-005")
def test_log_timestamped(capsys):
    C.log("hello world")
    out = capsys.readouterr().out
    assert "hello world" in out
    assert out.startswith("[") and "] " in out      # [HH:MM:SS] prefix
