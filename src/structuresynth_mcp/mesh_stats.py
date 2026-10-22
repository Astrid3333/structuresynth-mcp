"""Minimal Wavefront OBJ statistics (vertices, faces, bounding box)."""

from __future__ import annotations

from pathlib import Path


def obj_stats(path: str | Path) -> dict:
    """Return {vertices, faces, bytes, bbox_min, bbox_max} for an OBJ file.

    Reads line by line so huge exports stay memory-bounded.
    """
    p = Path(path)
    nv = nf = 0
    xmin = ymin = zmin = float("inf")
    xmax = ymax = zmax = float("-inf")

    with p.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if not line:
                continue
            c0 = line[0]
            if c0 == "v" and line[1] in " \t":
                try:
                    _, xs, ys, zs = line.split()[:4]
                    x, y, z = float(xs), float(ys), float(zs)
                except ValueError:
                    continue
                nv += 1
                if x < xmin:
                    xmin = x
                if x > xmax:
                    xmax = x
                if y < ymin:
                    ymin = y
                if y > ymax:
                    ymax = y
                if z < zmin:
                    zmin = z
                if z > zmax:
                    zmax = z
            elif c0 == "f" and line[1] in " \t":
                nf += 1

    stats: dict = {
        "vertices": nv,
        "faces": nf,
        "bytes": p.stat().st_size,
    }
    if nv:
        stats["bbox_min"] = [round(xmin, 4), round(ymin, 4), round(zmin, 4)]
        stats["bbox_max"] = [round(xmax, 4), round(ymax, 4), round(zmax, 4)]
    return stats
