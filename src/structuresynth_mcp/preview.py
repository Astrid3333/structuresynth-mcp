"""OBJ preview render to PNG via matplotlib Agg (software, no GPU needed)."""

from __future__ import annotations

import re
from pathlib import Path

_GROUP_COLOR_RE = re.compile(r"#([0-9a-fA-F]{6})")


def _hex_to_rgb01(h: str) -> tuple[float, float, float]:
    return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))  # type: ignore[return-value]


def _parse_obj_groups(path: Path) -> list[tuple[str, list[tuple[int, ...]]]]:
    """Parse OBJ into [(group_name, [face_vertex_indices...])]."""
    groups: list[tuple[str, list[tuple[int, ...]]]] = []
    current_name = "default"
    current_faces: list[tuple[int, ...]] = []
    vertex_offset = 0  # global 1-based vertex index of next v line
    vcount = 0

    def flush() -> None:
        nonlocal current_faces
        if current_faces:
            groups.append((current_name, current_faces))
            current_faces = []

    with path.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("v "):
                vcount += 1
            elif line.startswith("g "):
                flush()
                current_name = line[2:].strip() or "default"
            elif line.startswith("usemtl "):
                # usemtl often mirrors the group name with the color hint
                m = line[7:].strip()
                if m and m != "default":
                    current_name = m
            elif line.startswith("f "):
                idx = []
                for tok in line.split()[1:]:
                    idx.append(int(tok.split("/")[0]))
                current_faces.append(tuple(idx))
    flush()
    return groups


def preview_png(
    obj_path: str | Path,
    png_path: str | Path | None = None,
    size: tuple[int, int] = (800, 600),
    title: str = "",
) -> str:
    """Render an OBJ to a PNG using matplotlib Agg (CPU only).

    Colors come from group names of the form '#rrggbb' (written by the
    patched ssynthgen when groupByColor is on). Falls back to a single
    blue-grey if no colors are found.
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
        import numpy as np
    except ImportError as e:
        raise RuntimeError(
            "matplotlib is required for preview. Install with: uv add --extra export matplotlib"
        ) from e

    src = Path(obj_path)
    if not src.exists():
        raise FileNotFoundError(f"OBJ not found: {src}")
    if png_path is None:
        png_path = src.with_suffix(".png")
    out = Path(png_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    groups = _parse_obj_groups(src)

    # Read all vertices once (1-based indexing into this list).
    verts: list[tuple[float, float, float]] = []
    with src.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.startswith("v "):
                parts = line.split()
                verts.append((float(parts[1]), float(parts[2]), float(parts[3])))

    fig = plt.figure(figsize=(size[0] / 100, size[1] / 100), dpi=100)
    ax = fig.add_subplot(111, projection="3d")

    any_faces = False
    all_pts: list[tuple[float, float, float]] = []
    default_color = (0.55, 0.65, 0.78)

    for gname, faces in groups:
        m = _GROUP_COLOR_RE.search(gname)
        color = _hex_to_rgb01(m.group(1)) if m else default_color
        for face in faces:
            if len(face) < 3:
                continue
            # Fan-triangulate n-gons.
            for i in range(1, len(face) - 1):
                tri = (face[0], face[i], face[i + 1])
                pts = []
                ok = True
                for vi in tri:
                    if 1 <= vi <= len(verts):
                        pts.append(verts[vi - 1])
                    else:
                        ok = False
                        break
                if not ok:
                    continue
                pc = Poly3DCollection([pts], alpha=0.92, facecolor=color,
                                      edgecolor="none")
                ax.add_collection3d(pc)
                all_pts.extend(pts)
                any_faces = True

    if not any_faces:
        # Fallback: scatter the vertices so an empty/point-cloud OBJ still shows.
        if verts:
            xs, ys, zs = zip(*verts)
            ax.scatter(xs, ys, zs, s=2, c=[default_color])
            all_pts = verts
        else:
            ax.text(0.5, 0.5, 0.5, "No geometry", ha="center", va="center")

    if all_pts:
        arr = np.array(all_pts)
        lo = arr.min(axis=0)
        hi = arr.max(axis=0)
        c = (lo + hi) / 2
        r = float((hi - lo).max()) / 2 * 1.15 or 1.0
        ax.set_xlim(c[0] - r, c[0] + r)
        ax.set_ylim(c[1] - r, c[1] + r)
        ax.set_zlim(c[2] - r, c[2] + r)
        ax.set_box_aspect((1, 1, 1))

    ax.set_axis_off()
    if title:
        ax.set_title(title, fontsize=9)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return str(out)
