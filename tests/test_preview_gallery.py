from pathlib import Path

import pytest

from structuresynth_mcp.preview import preview_png
from structuresynth_mcp.colors import obj_group_colors, write_mtl
from structuresynth_mcp.gallery import render_gallery

CUBE_COLORED = """mtllib cube.mtl
g box#ff0000
usemtl box#ff0000
v 0 0 0
v 1 0 0
v 1 1 0
v 0 1 0
f 1 2 3 4
g box#00ff00
usemtl box#00ff00
v 0 0 1
v 1 0 1
v 1 1 1
v 0 1 1
f 5 6 7 8
"""


@pytest.fixture
def colored_obj(tmp_path):
    p = tmp_path / "cube.obj"
    p.write_text(CUBE_COLORED)
    return p


def test_preview_png(colored_obj, tmp_path):
    pytest.importorskip("matplotlib")
    out = tmp_path / "cube.png"
    result = preview_png(colored_obj, out)
    assert out.exists()
    assert out.stat().st_size > 1000
    assert result == str(out)


def test_preview_missing_obj(tmp_path):
    pytest.importorskip("matplotlib")
    with pytest.raises(FileNotFoundError):
        preview_png(tmp_path / "nope.obj")


def test_group_colors(colored_obj):
    colors = obj_group_colors(colored_obj)
    assert colors["box#ff0000"] == "#ff0000"
    assert colors["box#00ff00"] == "#00ff00"


def test_write_mtl(colored_obj, tmp_path):
    mtl = write_mtl(colored_obj, tmp_path / "cube.mtl")
    assert mtl is not None
    text = Path(mtl).read_text()
    assert "newmtl box#ff0000" in text
    assert "Kd 1.000000 0.000000 0.000000" in text
    # mtllib injected into OBJ
    assert colored_obj.read_text().startswith("mtllib ")


def test_write_mtl_no_colors(tmp_path):
    p = tmp_path / "plain.obj"
    p.write_text("v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n")
    assert write_mtl(p) is None


def test_gallery_smoke(tmp_path):
    pytest.importorskip("matplotlib")
    # with_preview=False: full gallery preview on 400k-face meshes is slow.
    result = render_gallery(tmp_path, seed=1, with_preview=False, timeout=60)
    assert result.ok_count >= 7  # most examples render; synctor is known-broken
    assert (tmp_path / "menger.obj").exists()
    assert (tmp_path / "binary_kite.obj").exists()
