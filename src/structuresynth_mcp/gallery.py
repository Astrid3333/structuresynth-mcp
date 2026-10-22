"""Batch-render every bundled example to OBJ + optional PNG."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from . import examples_meta
from .engine import RenderResult, ScriptError, render


@dataclass
class GalleryItem:
    name: str
    description: str
    ok: bool
    obj_path: str | None = None
    png_path: str | None = None
    vertices: int = 0
    faces: int = 0
    error: str | None = None


@dataclass
class GalleryResult:
    out_dir: str
    items: list[GalleryItem] = field(default_factory=list)

    @property
    def ok_count(self) -> int:
        return sum(1 for i in self.items if i.ok)

    @property
    def fail_count(self) -> int:
        return sum(1 for i in self.items if not i.ok)


def render_gallery(
    out_dir: str | Path,
    seed: int | None = None,
    with_preview: bool = True,
    timeout: int = 120,
) -> GalleryResult:
    """Render every bundled example into out_dir/<name>.obj (+ .png)."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    result = GalleryResult(out_dir=str(out))

    for meta in examples_meta.list_examples():
        name = meta["name"]
        item = GalleryItem(name=name, description=meta["description"], ok=False)
        try:
            script = examples_meta.get_example(name)
            obj_path = out / f"{name}.obj"
            r: RenderResult = render(script, obj_path, seed=seed, timeout=timeout)
            item.ok = True
            item.obj_path = r.obj_path
            item.vertices = r.vertices
            item.faces = r.faces
            if with_preview:
                # Skip preview for huge meshes: matplotlib Poly3DCollection
                # is O(faces) and crawls past ~50k triangles.
                if r.faces > 50_000:
                    item.error = f"preview skipped ({r.faces} faces > 50k)"
                else:
                    try:
                        from .colors import write_mtl
                        from .preview import preview_png

                        write_mtl(r.obj_path)
                        item.png_path = preview_png(r.obj_path, out / f"{name}.png",
                                                    title=name)
                    except Exception as e:  # preview is best-effort
                        item.error = f"preview failed: {e}"
        except ScriptError as e:
            item.error = str(e)
        except Exception as e:
            item.error = f"unexpected: {e}"
        result.items.append(item)
    return result
