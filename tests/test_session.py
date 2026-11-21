from conftest import load_addon_module

stats = load_addon_module("stats")
import sys

sys.modules["jdp_pkg_stats"] = stats


def _session_mod():
    # session.py does `from . import stats`; load it with stats injected.
    import importlib.util
    import types
    from conftest import ADDON

    pkg = types.ModuleType("jdp_pkg")
    pkg.__path__ = [str(ADDON)]
    sys.modules["jdp_pkg"] = pkg
    sys.modules["jdp_pkg.stats"] = stats
    spec = importlib.util.spec_from_file_location(
        "jdp_pkg.session", ADDON / "session.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["jdp_pkg.session"] = mod
    spec.loader.exec_module(mod)
    return mod


session = _session_mod()
settings = load_addon_module("settings")


def _long_session(start_acc, end_acc, start_s, end_s, n=60):
    s = session.Session(started=0)
    for i in range(n):
        late = i >= n - 20
        acc, secs = (end_acc, end_s) if late else (start_acc, start_s)
        ease = 3 if (i % 10) < acc * 10 else 1
        s.record(ease, secs)
    return s


def test_no_fatigue_early_or_when_steady():
    s = _long_session(0.9, 0.9, 6, 6)
    assert not session.fatigue(s, now=40 * 60)
    s2 = _long_session(0.9, 0.5, 6, 12)
    assert not session.fatigue(s2, now=10 * 60)  # too early in the session


def test_fatigue_when_accuracy_drops():
    s = _long_session(0.92, 0.6, 6, 7)
    assert session.fatigue(s, now=40 * 60)
    s.fatigue_dismissed = True
    assert not session.fatigue(s, now=40 * 60)


def test_state_payload():
    s = session.Session(started=1000)
    s.record(3, 5)
    pace = stats.Pace(10.0, 2.0, 1.0)
    cfg = settings.merged(None)
    st = session.state(s, (5, 0, 10), pace, cfg, now=1000 + 60)
    assert st["done"] == 1 and st["remaining"] == 15
    assert 0 < st["progress"] < 1
    assert st["eta"] == "about 3 min left"  # (5*2 + 10) answers * 10 s
    quick = session.state(s, (0, 0, 2), pace, cfg, now=1000 + 60)
    assert quick["eta"] == "less than a minute left"
    assert st["fatigue"] is False  # module off by default


def test_clock_format_is_portable():
    import time as t

    assert (
        session._clock(t.struct_time((2026, 1, 1, 0, 5, 0, 0, 1, 0)))
        == "12:05 AM"
    )
    assert (
        session._clock(t.struct_time((2026, 1, 1, 16, 37, 0, 0, 1, 0)))
        == "4:37 PM"
    )
    assert (
        session._clock(t.struct_time((2026, 1, 1, 12, 0, 0, 0, 1, 0)))
        == "12:00 PM"
    )
