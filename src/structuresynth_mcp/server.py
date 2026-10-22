"""MCP server exposing Structure Synth (EisenScript) rendering."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from mcp.server.mcpserver import MCPServer

from . import examples_meta
from .engine import RenderResult, ScriptError, find_ssynthgen, render, validate

mcp = MCPServer(
    "structuresynth",
    instructions=(
        "Tools for Structure Synth: write EisenScript grammars and render them "
        "to 3D meshes (Wavefront OBJ). Use list_examples/get_example to learn the "
        "language style, validate_script to check syntax, and render_script to "
        "produce geometry. Engine: libssynth ssynthgen (set SSYNTHGEN_PATH if not on PATH)."
    ),
)


def _engine_status() -> str:
    exe = find_ssynthgen()
    return exe or "NOT FOUND — install libssynth and set SSYNTHGEN_PATH"


@mcp.tool()
def engine_status() -> str:
    """Report the path of the ssynthgen engine binary, or install help if missing."""
    return _engine_status()


@mcp.tool()
def list_examples() -> list[dict]:
    """List bundled EisenScript examples with short descriptions."""
    return examples_meta.list_examples()


@mcp.tool()
def get_example(name: str) -> str:
    """Return the full EisenScript source of a bundled example by name."""
    try:
        return examples_meta.get_example(name)
    except KeyError as e:
        return str(e)


@mcp.tool()
def validate_script(script: str) -> str:
    """Check an EisenScript for syntax/parse errors without keeping geometry.

    Returns 'OK' or an error message.
    """
    try:
        ok, msg = validate(script)
    except Exception as e:  # engine missing, etc.
        return f"Error: {e}"
    return msg if ok else f"Error: {msg}"


@mcp.tool()
def render_script(
    script: str,
    output_path: str = "",
    seed: int | None = None,
    timeout: int = 120,
) -> str:
    """Render EisenScript to a Wavefront OBJ mesh.

    Args:
        script: Full EisenScript source (rules, primitives, transformations).
        output_path: Where to write the .obj. Empty = temp file under the
            system temp dir (path is returned).
        seed: Optional RNG seed; injected as `set seed N` for reproducibility.
        timeout: Seconds before aborting a runaway script.

    Returns a summary: OBJ path, vertex/face counts, bounding box.
    """
    try:
        if output_path:
            out = Path(output_path).expanduser()
        else:
            fd, name = tempfile.mkstemp(suffix=".obj", prefix="structuresynth_")
            os.close(fd)
            out = Path(name)
        result: RenderResult = render(script, out, seed=seed, timeout=timeout)
    except ScriptError as e:
        return f"Render failed: {e}"
    except Exception as e:
        return f"Error: {e}"

    lines = [
        f"OBJ: {result.obj_path}",
        f"Vertices: {result.vertices}",
        f"Faces: {result.faces}",
        f"Size: {result.bytes} bytes",
    ]
    if result.bbox_min is not None and result.bbox_max is not None:
        lines.append(f"BBox: {result.bbox_min} → {result.bbox_max}")
    return "\n".join(lines)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
