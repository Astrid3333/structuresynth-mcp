from structuresynth_mcp.mesh_stats import obj_stats


def test_obj_stats(tmp_path):
    obj = tmp_path / "cube.obj"
    obj.write_text(
        "v 0 0 0\nv 1 0 0\nv 1 1 0\nv 0 1 0\n"
        "v 0 0 1\nv 1 0 1\nv 1 1 1\nv 0 1 1\n"
        "f 1 2 3 4\nf 5 6 7 8\n"
    )
    s = obj_stats(obj)
    assert s["vertices"] == 8
    assert s["faces"] == 2
    assert s["bbox_min"] == [0, 0, 0]
    assert s["bbox_max"] == [1, 1, 1]
    assert s["bytes"] > 0


def test_obj_stats_empty(tmp_path):
    obj = tmp_path / "empty.obj"
    obj.write_text("")
    s = obj_stats(obj)
    assert s["vertices"] == 0
    assert s["faces"] == 0
    assert "bbox_min" not in s
