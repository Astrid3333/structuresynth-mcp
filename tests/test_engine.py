import pytest

from structuresynth_mcp import examples_meta
from structuresynth_mcp.engine import (
    EngineNotFound,
    find_ssynthgen,
    inject_seed,
    render,
    require_ssynthgen,
    validate,
)

SIMPLE = "set maxdepth 20\nr1\nrule r1 { box }\n"


def test_find_ssynthgen():
    # Should not raise even if missing; just reports path or None
    result = find_ssynthgen()
    assert result is None or isinstance(result, str)


def test_inject_seed_appends():
    out = inject_seed("box", 42)
    assert out.startswith("set seed 42")
    assert "box" in out


def test_inject_seed_replaces():
    out = inject_seed("set seed 1\nbox", 99)
    assert "set seed 99" in out
    assert "set seed 1" not in out


def test_validate_ok_or_engine_missing():
    try:
        require_ssynthgen()
    except EngineNotFound:
        pytest.skip("ssynthgen not installed")
    ok, msg = validate(SIMPLE)
    assert ok, msg


def test_validate_bad_script():
    try:
        require_ssynthgen()
    except EngineNotFound:
        pytest.skip("ssynthgen not installed")
    ok, msg = validate("r1\nrule r1 { nonexistent_primitive }\n")
    # libssynth may abort or report; either way it should not return OK silently
    # (some unknown primitives fall back to box in Structure Synth, so use a
    # guaranteed parse error instead: unbalanced brace)
    ok2, msg2 = validate("rule r1 { box\n")
    assert not ok2 or not ok  # at least one must fail


def test_render_tmp_obj():
    try:
        require_ssynthgen()
    except EngineNotFound:
        pytest.skip("ssynthgen not installed")
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "t.obj"
        result = render(SIMPLE, out, seed=7)
        assert result.vertices == 8  # one unit cube
        assert result.faces == 6
        assert out.exists()


def test_examples_list_and_get():
    ex = examples_meta.list_examples()
    assert len(ex) >= 5
    names = {e["name"] for e in ex}
    assert "menger" in names
    src = examples_meta.get_example("menger")
    assert "rule" in src.lower()


def test_examples_get_unknown():
    with pytest.raises(KeyError):
        examples_meta.get_example("does_not_exist")
