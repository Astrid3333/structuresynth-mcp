# structuresynth-mcp

MCP (Model Context Protocol) server for **[Structure Synth](http://structuresynth.sourceforge.net/)**
— generate 3D meshes from **EisenScript** grammars, headlessly.

Give an LLM agent a tool to write procedural 3D structure grammars and get back
real geometry (Wavefront OBJ) with mesh statistics, ready for viewing, 3D
printing, or further processing.

## What it does

| Tool | Description |
| --- | --- |
| `render_script(script, seed?, output_path?, timeout?)` | Run an EisenScript grammar → `.obj` mesh; returns path, vertex/face counts, bounding box. |
| `preview_script(script, output_path?, seed?, timeout?)` | Render + return a PNG preview (matplotlib Agg, CPU only). |
| `preview_obj(obj_path, output_path?)` | PNG preview of an existing OBJ. |
| `validate_script(script)` | Parse-check a grammar without keeping geometry. |
| `analyze_script(script)` | Linter: braces, unknown actions, unsupported primitives, recursion without `maxdepth` (timeout risk), unused rules. |
| `eisenscript_reference()` | Embedded EisenScript cheat sheet (primitives, transformations, modifiers). |
| `export_mesh_tool(obj_path, format, output_path?)` | Convert OBJ → `stl`/`glb`/`gltf`/`ply`/`off` (requires optional `trimesh`). |
| `render_gallery(out_dir, seed?, with_preview?)` | Batch-render every bundled example to OBJ (+ PNG). |
| `send_to_unreal(obj_path, dest_path?, name?)` | Import an OBJ into a running Unreal editor (TCP bridge, port 55557). |
| `list_examples()` | Browse bundled example grammars. |
| `get_example(name)` | Fetch the full source of an example. |
| `engine_status()` | Locate the render engine binary / install hint. |

Rendering is powered by **[libssynth](https://github.com/jcelerier/libssynth)**
(`ssynthgen`), a modernized, Qt-light port of Structure Synth's engine that
exports OBJ from the command line. This MCP server is a thin Python wrapper.

**Patched engine**: the recommended `ssynthgen` build includes small patches
(upstream-able) that give parse errors real **line numbers**, exit code 1 instead
of SIGABRT, and color-group OBJ output (`usemtl #rrggbb` groups, converted to
`.mtl` by this server). Build instructions below.

## Requirements

1. **Python ≥ 3.10** and [`uv`](https://docs.astral.sh/uv/) (or pip).
2. **`ssynthgen`** — build once from [libssynth](https://github.com/jcelerier/libssynth):

   ```bash
   git clone https://github.com/jcelerier/libssynth.git
   cmake -S libssynth -B libssynth/build -DCMAKE_BUILD_TYPE=Release
   cmake --build libssynth/build -j
   # put it somewhere on your PATH, e.g.:
   cp libssynth/build/ssynthgen ~/.local/bin/
   ```

   Dependencies: CMake ≥ 3.13, a C++20 compiler, Qt5 (Core/Gui/Xml), Boost headers, fmt.

   If `ssynthgen` is not on `PATH`, point the server at it:

   ```bash
   export SSYNTHGEN_PATH=/path/to/ssynthgen
   ```

## Install

```bash
git clone https://github.com/Astrid3333/structuresynth-mcp.git
cd structuresynth-mcp
uv sync                    # core
uv sync --extra export     # + matplotlib/trimesh for preview, STL/glTF export
```

## Run

```bash
uv run structuresynth-mcp          # stdio MCP server
```

## Use with an MCP client

### Claude Desktop

`claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "structuresynth": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/structuresynth-mcp", "run", "structuresynth-mcp"],
      "env": {
        "SSYNTHGEN_PATH": "/home/you/.local/bin/ssynthgen"
      }
    }
  }
}
```

### opencode

```bash
opencode mcp add structuresynth -- uv --directory /absolute/path/to/structuresynth-mcp run structuresynth-mcp
```

## EisenScript in 30 seconds

```
set maxdepth 40
set seed 42

r1

rule r1 maxdepth 10 {
  { x 1 ry 10 } r1
  { y 1 hue 20 } r1
  box
}
```

Rules call each other; transformations in `{ }` modify the state; primitives
(`box`, `sphere`, `cylinder`, `tube`, `grid`, `line`, `point`, `circle`, `cone`,
`torus`, `helix`, …) draw geometry. See the
[official EisenScript reference](http://structuresynth.sourceforge.net/reference.php)
and the bundled examples.

## Limits

- The bundled engine (`libssynth`) covers the core language; a few exotic
  original examples (e.g. `Konstrukt.es`, `Thingy.es`) use primitives or
  features it does not implement (torus, cone, helix, circle, point, tube).
- Parse errors report `(line N)` when using the patched `ssynthgen` build;
  the stock upstream build aborts with a generic message.
- `preview_*` uses matplotlib's software renderer — fine for previews, not
  ray-traced quality; previews are skipped for meshes above 50k faces.
- JavaScript animation scripting of the original GUI app is out of scope.

## License

MIT for this MCP server. `libssynth` and Structure Synth are LGPL; bundled
`.es` example scripts are from the official Structure Synth distribution —
see [`src/structuresynth_mcp/examples/ATTRIBUTION.md`](src/structuresynth_mcp/examples/ATTRIBUTION.md).

## Credits

- [Structure Synth](http://structuresynth.sourceforge.net/) by Mikael Hvidtfeldt Christensen (Syntopia).
- [libssynth](https://github.com/jcelerier/libssynth) by Jérémie / contributors — headless engine.
- [Model Context Protocol](https://modelcontextprotocol.io/).
