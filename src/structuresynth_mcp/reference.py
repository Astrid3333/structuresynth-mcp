"""Static EisenScript reference (verified against libssynth's parser)."""

from __future__ import annotations

REFERENCE = """\
# EisenScript quick reference (libssynth backend)

## Structure
```
set maxdepth 30          // global settings (executed at startup)
set seed 42
set colorpool random
set background #101018

r1                       // start: first action calls rule r1

rule r1 maxdepth 10 w 2 {   // rule with modifiers
  { x 1 ry 10 } r1          // transform then recurse
  box                       // draw a primitive
}
```

## Built-in primitives (supported by libssynth / ssynthgen)
| Name | Draws |
| --- | --- |
| `box` | Unit cube (0,0,0)-(1,1,1) |
| `sphere` | Unit sphere (radius from state scale) |
| `cylinder` | Cylinder along local x |
| `line` | Line from (0,0,0) to (1,0,0) |
| `dot` | Small point marker |
| `grid` | Grid of dots |
| `mesh` | Triangle between previous and current state |
| `template` | Custom primitive from a render template (no OBJ geometry) |

NOT supported by this backend (present in the original Structure Synth GUI):
`torus`, `cone`, `tube`, `helix`, `circle`, `point`.

## Transformations (inside `{ }`; applied right-to-left)
| Command | Meaning |
| --- | --- |
| `x n` `y n` `z n` | Translate |
| `rx a` `ry a` `rz a` | Rotate (degrees) |
| `s f` or `s fx fy fz` | Uniform / per-axis scale |
| `matrix m11..m33` | Full 3x3 linear transform |
| `reflect nx ny nz` | Reflect across plane |
| `fx` `fy` `fz` | Flip (mirror) across axis |
| `hue h` | Hue shift (HSV degrees) |
| `sat s` | Saturation |
| `brightness b` / `val v` | Value/brightness |
| `color name|#hex|random` | Set color |
| `alpha a` | Opacity |

## Rule modifiers (after rule name, before `{`)
| Command | Meaning |
| --- | --- |
| `weight w` / `w n` | Selection weight among alternatives |
| `maxdepth n` / `md n` | Stop recursing this rule at depth n |

## Iteration
`N * { transformations } action` repeats the action N times with accumulating
transform (e.g. `10 * { x 1 } box`).

## Preprocessor
- `#define name value` — textual macro (also GUI variants `(float:min-max)`).
- `random[a,b]` inline — replaced by a random number in [a,b).

## `set` commands understood by the engine
`seed <int>`, `colorpool <random|list...>`, `background <color>`,
`maxdepth <n>`, `recursion depth`.

## Tips to avoid timeouts
- Give recursive rules a `maxdepth` modifier or a global `set maxdepth`.
- Keep `maxdepth` modest (< 100) unless the structure needs deep recursion.
- Use `weight` to diversify branches; use `set seed` for reproducibility.
"""


def get_reference() -> str:
    return REFERENCE
