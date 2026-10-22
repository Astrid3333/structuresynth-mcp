# Patches

## `libssynth-cli-line-numbers-colors.patch`

Small, upstream-able fixes to [libssynth](https://github.com/jcelerier/libssynth)
for this MCP server:

1. **Parse errors with line numbers** — `Exceptions::Exception` now inherits
   `std::exception` (so `catch (std::exception&)` actually catches it instead of
   `std::terminate`/SIGABRT), `Tokenizer` stores real char positions, and
   `CommandLine.cpp` converts the position to a 1-based line and exits 1.
2. **Unmatched `[` no longer trips a QString assert** — bounds are checked
   before `QString::at()`.
3. **Color-group OBJ output** — `ObjRenderer` is constructed with
   `groupByColor=true`, so groups become `g <name>#rrggbb` / `usemtl <name>#rrggbb`.
   The Python side (`colors.py`) turns those into a companion `.mtl`.

Apply on a fresh clone:

```bash
git clone https://github.com/jcelerier/libssynth.git
cd libssynth
git apply /path/to/patches/libssynth-cli-line-numbers-colors.patch
# then build (see README of structuresynth-mcp)
```
