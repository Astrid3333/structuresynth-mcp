from structuresynth_mcp.analyze import analyze
from structuresynth_mcp.reference import get_reference

GOOD = """
set maxdepth 20
set seed 1
r1
rule r1 maxdepth 5 {
  { x 1 } r1
  box
}
"""

RECURSIVE_NO_DEPTH = """
r1
rule r1 {
  { x 1 rx 5 } r1
  box
}
"""

UNSUPPORTED = "r1\nrule r1 { torus }\n"

UNKNOWN_ACTION = "r1\nrule r1 { frobnicate }\n"


def test_analyze_good():
    res = analyze(GOOD)
    assert res.ok
    assert not res.errors
    assert res.info["rule_count"] == 1
    assert res.info["has_seed"] is True
    assert res.info["global_maxdepth"] == 20


def test_analyze_unbalanced_braces():
    res = analyze("rule r1 { box")
    assert not res.ok
    assert any("Unclosed" in e for e in res.errors)


def test_analyze_unsupported_primitive():
    res = analyze(UNSUPPORTED)
    assert res.ok  # warning, not error
    assert any("torus" in w for w in res.warnings)


def test_analyze_unknown_action():
    res = analyze(UNKNOWN_ACTION)
    assert not res.ok
    assert any("frobnicate" in e for e in res.errors)


def test_analyze_recursion_without_maxdepth():
    res = analyze(RECURSIVE_NO_DEPTH)
    assert any("maxdepth" in w for w in res.warnings)


def test_analyze_unused_rule():
    res = analyze("rule orphan { box }\nbox\n")
    assert any("never called" in w for w in res.warnings)


def test_reference_content():
    ref = get_reference()
    for kw in ("box", "sphere", "maxdepth", "set seed", "torus"):
        assert kw in ref
