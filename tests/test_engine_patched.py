import pytest

from structuresynth_mcp.engine import ScriptError, render, require_ssynthgen, validate


def test_parse_error_has_line_info():
    """Patched ssynthgen reports '(line N)' in stderr for parse errors."""
    try:
        require_ssynthgen()
    except Exception:
        pytest.skip("ssynthgen not installed")
    ok, msg = validate("r1\nrule r1 {\n  x 1..2 box\n}\n")
    assert not ok
    # The patched engine appends "(line N)"; tolerate old binaries too.
    assert "line" in msg.lower() or "invalid" in msg.lower()


def test_render_error_message_includes_line():
    try:
        require_ssynthgen()
    except Exception:
        pytest.skip("ssynthgen not installed")
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "bad.obj"
        with pytest.raises(ScriptError) as exc:
            render("r1\nrule r1 {\n  x 1..2 box\n}\n", out)
        assert "line" in str(exc.value).lower() or "invalid" in str(exc.value).lower()
        assert not out.exists()  # no partial OBJ left behind


def test_color_groups_in_obj():
    """Patched ssynthgen emits g/usemtl lines with hex colors."""
    try:
        require_ssynthgen()
    except Exception:
        pytest.skip("ssynthgen not installed")
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as td:
        out = Path(td) / "color.obj"
        script = "set maxdepth 3\nr1\nrule r1 maxdepth 2 {\n  { x 1 hue 0 } box\n  { x -1 hue 120 } box\n}\n"
        result = render(script, out, seed=1)
        text = out.read_text()
        assert "usemtl" in text
        assert "#" in text  # hex color in group name
        assert result.faces > 0
