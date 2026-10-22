"""Bundled EisenScript examples (from Structure Synth's official example set).

These scripts come with Structure Synth (LGPL). They are redistributed here
for convenience with attribution; see ATTRIBUTION.md in this directory.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

# name -> (filename, one-line description)
EXAMPLES: dict[str, tuple[str, str]] = {
    "binary_kite": ("BinaryKite.es", "Recursive kite lattice (classic Structure Synth demo)."),
    "city_of_glass": ("City of Glass.es", "Fractal city skyline of stacked boxes."),
    "default": ("Default.es", "The default showcase script shipped with Structure Synth."),
    "frame_in_frame": ("FrameInFrame.es", "Nested frames; small and fast."),
    "menger": ("Menger.es", "Menger sponge approximation."),
    "mondrian": ("Mondrian.es", "Flat Mondrian-style composition."),
    "nabla": ("Nabla.es", "Nabla fractal surface."),
    "round_tree": ("RoundTree.es", "Branching tree with spheres."),
    "synctor": ("Synctor.es", "Abstract lattice of connected forms."),
}


def examples_dir() -> Path:
    return Path(str(resources.files("structuresynth_mcp.examples")))


def list_examples() -> list[dict]:
    return [
        {"name": name, "description": desc, "file": fname}
        for name, (fname, desc) in EXAMPLES.items()
    ]


def get_example(name: str) -> str:
    key = name.strip().lower().replace(" ", "_").replace("-", "_")
    if key not in EXAMPLES:
        known = ", ".join(sorted(EXAMPLES))
        raise KeyError(f"Unknown example '{name}'. Known: {known}")
    return (examples_dir() / EXAMPLES[key][0]).read_text(encoding="utf-8")
