import pytest

from structuresynth_mcp.export import SUPPORTED_FORMATS, ExportError, export_mesh

CUBE = """v 0 0 0
v 1 0 0
v 1 1 0
v 0 1 0
v 0 0 1
v 1 0 1
v 1 1 1
v 0 1 1
f 1 2 3 4
f 5 6 7 8
f 1 2 6 5
f 2 3 7 6
f 3 4 8 7
f 4 1 5 8
"""


@pytest.fixture
def cube_obj(tmp_path):
    p = tmp_path / "cube.obj"
    p.write_text(CUBE)
    return p


def test_export_missing_trimesh_or_stl(cube_obj, tmp_path):
    trimesh = pytest.importorskip("trimesh", reason="trimesh not installed")
    out = tmp_path / "cube.stl"
    result = export_mesh(cube_obj, out, fmt="stl")
    assert out.exists()
    assert out.stat().st_size > 0
    assert result == str(out)


def test_export_bad_format(cube_obj):
    pytest.importorskip("trimesh")
    with pytest.raises(ExportError, match="Unsupported format"):
        export_mesh(cube_obj, fmt="fbx")


def test_export_missing_obj(tmp_path):
    pytest.importorskip("trimesh")
    with pytest.raises(ExportError, match="not found"):
        export_mesh(tmp_path / "nope.obj", fmt="stl")


def test_supported_formats():
    assert "stl" in SUPPORTED_FORMATS
    assert "glb" in SUPPORTED_FORMATS
