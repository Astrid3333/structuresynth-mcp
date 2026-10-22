"""Mesh format conversion (OBJ -> STL/glTF/PLY) via optional trimesh dependency."""

from __future__ import annotations

from pathlib import Path

SUPPORTED_FORMATS = ("stl", "glb", "gltf", "ply", "off")


class ExportError(RuntimeError):
    pass


def export_mesh(obj_path: str | Path, output_path: str | Path | None = None,
                fmt: str = "stl") -> str:
    """Convert an OBJ mesh to another format. Returns the output path.

    Requires the optional dependency: pip/uv add trimesh
    """
    try:
        import trimesh
    except ImportError as e:
        raise ExportError(
            "trimesh is not installed. Install with: uv add trimesh  (or pip install trimesh)"
        ) from e

    src = Path(obj_path)
    if not src.exists():
        raise ExportError(f"OBJ not found: {src}")

    fmt = fmt.lower().lstrip(".")
    if fmt not in SUPPORTED_FORMATS:
        raise ExportError(f"Unsupported format '{fmt}'. Use one of: {', '.join(SUPPORTED_FORMATS)}")

    if output_path:
        dst = Path(output_path)
    else:
        dst = src.with_suffix(f".{fmt}")
    dst.parent.mkdir(parents=True, exist_ok=True)

    loaded = trimesh.load(src, force="scene" if fmt in ("glb", "gltf") else None)

    if isinstance(loaded, trimesh.Scene):
        if fmt in ("glb", "gltf"):
            loaded.export(dst, file_type=fmt)
        else:
            mesh = loaded.dump(concatenate=True)
            mesh.export(dst, file_type=fmt)
    else:
        loaded.export(dst, file_type=fmt)

    if not dst.exists() or dst.stat().st_size == 0:
        raise ExportError(f"Export produced no output at {dst}")
    return str(dst)
