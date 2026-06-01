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
def test_env_prefix_shared_falls_back(monkeypatch):
    # shared=True keeps the project-prefix-with-fallback behaviour for family creds.
    for k in ("WC_URL", "STOCK_WC_URL", "STOCK_KNOB", "KNOB"):
        monkeypatch.delenv(k, raising=False)
    # Prefixed value wins when set.
    monkeypatch.setenv("STOCK_WC_URL", "https://prefixed")
    monkeypatch.setenv("WC_URL", "https://shared")
    assert C.env_required("WC_URL", prefix="STOCK", shared=True) == "https://prefixed"
    # Falls back to the shared unprefixed value when the prefixed one is absent.
    monkeypatch.delenv("STOCK_WC_URL", raising=False)
    assert C.env_required("WC_URL", prefix="STOCK", shared=True) == "https://shared"
    # env_opt(shared): prefixed override, else unprefixed, else default.
    monkeypatch.setenv("STOCK_KNOB", "10")
    assert C.env_opt("KNOB", "0", prefix="STOCK", shared=True) == "10"
    monkeypatch.delenv("STOCK_KNOB", raising=False)
    monkeypatch.setenv("KNOB", "5")
    assert C.env_opt("KNOB", "0", prefix="STOCK", shared=True) == "5"
    monkeypatch.delenv("KNOB", raising=False)
    assert C.env_opt("KNOB", "0", prefix="STOCK", shared=True) == "0"


@pytest.mark.feature("F-001")
def test_env_get_is_env_opt_alias(monkeypatch):
    # env_get is the single-function spelling of env_opt (same lookup, incl. shared).
    for k in ("KNOB", "STOCK_KNOB"):
        monkeypatch.delenv(k, raising=False)
    assert C.env_get("KNOB", "def", prefix="STOCK", shared=True) == "def"
    monkeypatch.setenv("KNOB", "5")
    assert C.env_get("KNOB", prefix="STOCK", shared=True) == "5"   # unprefixed fallback
    monkeypatch.setenv("STOCK_KNOB", "9")
    assert C.env_get("KNOB", prefix="STOCK", shared=True) == "9"   # prefixed wins
    assert C.env_get is C.env_opt


@pytest.mark.feature("F-001")
def test_env_required_missing_names_both_forms(monkeypatch):
    # A shared required cred names both the prefixed and unprefixed form when missing.
    monkeypatch.delenv("WC_URL", raising=False)
    monkeypatch.delenv("STOCK_WC_URL", raising=False)
    with pytest.raises(SystemExit) as exc:
        C.env_required("WC_URL", prefix="STOCK", shared=True)
    msg = str(exc.value)
    assert "WC_URL" in msg and "STOCK_WC_URL" in msg


# ---------------------------------------------------------------------------
# F-006 Numeric environment helpers with clear errors
# ---------------------------------------------------------------------------


@pytest.mark.feature("F-006")
def test_env_int_float_parse_with_default_and_prefix(monkeypatch):
    for k in ("PAGES", "STOCK_PAGES", "RATE", "STOCK_RATE"):
        monkeypatch.delenv(k, raising=False)
    # Unset → default returned as-is (an int/float, not re-parsed); no default → None.
    assert C.env_int("PAGES", 50, prefix="STOCK") == 50
    assert C.env_float("RATE", 1.5, prefix="STOCK") == 1.5
    assert C.env_int("PAGES") is None
    assert C.env_float("RATE") is None
    # Set & valid: parsed; the prefixed form wins. shared=True keeps the fallback.
    monkeypatch.setenv("PAGES", "10")
    monkeypatch.setenv("STOCK_PAGES", "200")
    assert C.env_int("PAGES", 50, prefix="STOCK") == 200
    monkeypatch.delenv("STOCK_PAGES", raising=False)
    assert C.env_int("PAGES", 50, prefix="STOCK", shared=True) == 10
    monkeypatch.setenv("RATE", "2.5")
    assert C.env_float("RATE", 1.0) == 2.5


@pytest.mark.feature("F-006")
def test_env_int_malformed_aborts_naming_the_variable(monkeypatch):
    monkeypatch.setenv("PAGES", "abc")
    with pytest.raises(SystemExit) as exc:
        C.env_int("PAGES")
    msg = str(exc.value)
    assert "PAGES" in msg and "abc" in msg and "integer" in msg


@pytest.mark.feature("F-006")
def test_env_int_rejects_a_non_integer_number(monkeypatch):
    # "10.5" is a valid float but not an int — env_int must reject it, not truncate.
    monkeypatch.setenv("PAGES", "10.5")
    with pytest.raises(SystemExit):
        C.env_int("PAGES")


@pytest.mark.feature("F-006")
def test_env_float_malformed_aborts_naming_the_variable(monkeypatch):
    monkeypatch.setenv("RATE", "x")
    with pytest.raises(SystemExit) as exc:
        C.env_float("RATE")
    msg = str(exc.value)
    assert "RATE" in msg and "number" in msg


# ---------------------------------------------------------------------------
# F-007 Prefix-required routine-own keys + migration warning
# ---------------------------------------------------------------------------


@pytest.fixture
def reset_warned():
    """Clear the one-time-warning ledger around each test that exercises it."""
    C._WARNED_PREFIX_KEYS.clear()
    yield
    C._WARNED_PREFIX_KEYS.clear()


@pytest.mark.feature("F-007")
def test_prefix_required_ignores_plain_form(monkeypatch, reset_warned):
    # A routine-own key (shared=False, the default) is read ONLY with the prefix.
    for k in ("KNOB", "STOCK_KNOB"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("KNOB", "plain")
    assert C.env_opt("KNOB", "def", prefix="STOCK") == "def"   # plain ignored
    with pytest.raises(SystemExit):
        C.env_required("KNOB", prefix="STOCK")                  # plain ignored


@pytest.mark.feature("F-007")
def test_shared_still_reads_plain_form(monkeypatch, reset_warned):
    for k in ("KNOB", "STOCK_KNOB"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("KNOB", "plain")
    assert C.env_opt("KNOB", "def", prefix="STOCK", shared=True) == "plain"


@pytest.mark.feature("F-007")
def test_prefix_required_warns_naming_both_forms(monkeypatch, capsys, reset_warned):
    for k in ("LOOKBACK_DAYS", "MARKETING_LOOKBACK_DAYS"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("LOOKBACK_DAYS", "7")
    C.env_opt("LOOKBACK_DAYS", "5", prefix="MARKETING")
    err = capsys.readouterr().err
    assert "MARKETING_LOOKBACK_DAYS" in err and "LOOKBACK_DAYS" in err


@pytest.mark.feature("F-007")
def test_warning_is_one_time_per_pair(monkeypatch, capsys, reset_warned):
    monkeypatch.delenv("MARKETING_KNOB", raising=False)
    monkeypatch.setenv("KNOB", "x")
    C.env_opt("KNOB", prefix="MARKETING")
    C.env_opt("KNOB", prefix="MARKETING")
    assert capsys.readouterr().err.count("WARNING:") == 1


@pytest.mark.feature("F-007")
def test_no_warning_when_prefixed_set_or_shared(monkeypatch, capsys, reset_warned):
    for k in ("KNOB", "STOCK_KNOB"):
        monkeypatch.delenv(k, raising=False)
    # Prefixed set → no warning (and the plain form is simply not consulted).
    monkeypatch.setenv("STOCK_KNOB", "9")
    monkeypatch.setenv("KNOB", "plain")
    C.env_opt("KNOB", prefix="STOCK")
    # shared=True reading the plain form → no warning.
    monkeypatch.delenv("STOCK_KNOB", raising=False)
    C.env_opt("KNOB", prefix="STOCK", shared=True)
    assert "WARNING:" not in capsys.readouterr().err


@pytest.mark.feature("F-007")
def test_no_prefix_is_unchanged(monkeypatch, reset_warned):
    # No prefix at all: plain lookup as before, regardless of shared (standalone).
    monkeypatch.setenv("KNOB", "plain")
    assert C.env_opt("KNOB") == "plain"
    assert C.env_opt("KNOB", shared=True) == "plain"


@pytest.mark.feature("F-007")
def test_env_int_prefix_required_and_warns(monkeypatch, capsys, reset_warned):
    for k in ("PAGES", "STOCK_PAGES"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("PAGES", "999")
    assert C.env_int("PAGES", 50, prefix="STOCK") == 50    # plain ignored → default
    assert "STOCK_PAGES" in capsys.readouterr().err


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
