"""Wrapper around the ssynthgen CLI (libssynth, Structure Synth engine)."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

DEFAULT_TIMEOUT = 120

_SEED_RE = re.compile(r"^\s*set\s+seed\s+\S+", re.MULTILINE)


class EngineNotFound(RuntimeError):
    """ssynthgen binary is not available."""


class ScriptError(RuntimeError):
    """EisenScript failed to parse or generate."""

    def __init__(self, message: str, returncode: int | None = None):
        super().__init__(message)
        self.returncode = returncode


def find_ssynthgen(explicit: str | None = None) -> str | None:
    """Locate the ssynthgen binary: explicit arg > SSYNTHGEN_PATH > PATH."""
    candidates = []
    if explicit:
        candidates.append(explicit)
    env = os.environ.get("SSYNTHGEN_PATH")
    if env:
        candidates.append(env)
    which = shutil.which("ssynthgen")
    if which:
        candidates.append(which)
    home = Path.home() / ".local/bin/ssynthgen"
    candidates.append(str(home))
    for cand in candidates:
        if cand and Path(cand).is_file():
            return cand
    return None


def require_ssynthgen(explicit: str | None = None) -> str:
    path = find_ssynthgen(explicit)
    if not path:
        raise EngineNotFound(
            "ssynthgen not found. Install libssynth (https://github.com/jcelerier/libssynth) "
            "and set SSYNTHGEN_PATH or add ssynthgen to PATH."
        )
    return path


def inject_seed(script: str, seed: int) -> str:
    """Ensure the script starts with `set seed N` (Structure Synth preprocessor)."""
    if _SEED_RE.search(script):
        return _SEED_RE.sub(f"set seed {seed}", script, count=1)
    return f"set seed {seed}\n{script}"


@dataclass
class RenderResult:
    obj_path: str
    vertices: int
    faces: int
    bytes: int
    bbox_min: list | None = None
    bbox_max: list | None = None


def render(script: str, output_path: str | Path, seed: int | None = None,
           timeout: int = DEFAULT_TIMEOUT, binary: str | None = None) -> RenderResult:
    """Run EisenScript through ssynthgen and write an OBJ file."""
    from .mesh_stats import obj_stats

    exe = require_ssynthgen(binary)
    if seed is not None:
        script = inject_seed(script, seed)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile("w", suffix=".es", delete=False, encoding="utf-8") as tf:
        tf.write(script)
        script_path = tf.name
    try:
        with open(out, "wb") as fh:
            try:
                proc = subprocess.run(
                    [exe, script_path],
                    stdout=fh,
                    stderr=subprocess.PIPE,
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired:
                out.unlink(missing_ok=True)
                raise ScriptError(f"Render timed out after {timeout}s "
                                  "(script may be too deep or recursive without maxdepth).") from None
    finally:
        Path(script_path).unlink(missing_ok=True)

    if proc.returncode != 0:
        out.unlink(missing_ok=True)
        stderr = (proc.stderr or b"").decode("utf-8", "replace").strip()
        detail = stderr or "unknown parse/generation error"
        # Older libssynth builds abort (SIGABRT) without a message; the
        # patched build prints a ParseError with line info and exits 1.
        if proc.returncode in (-6, 134) or "terminate called" in stderr:
            detail = "EisenScript parse error (engine aborted; update ssynthgen for line info)."
        raise ScriptError(detail, returncode=proc.returncode)

    if not out.exists() or out.stat().st_size == 0:
        out.unlink(missing_ok=True)
        raise ScriptError("Engine produced no output (script may generate no geometry).")

    stats = obj_stats(out)
    return RenderResult(obj_path=str(out), **stats)


def validate(script: str, timeout: int = 60, binary: str | None = None) -> tuple[bool, str]:
    """Parse-check a script by running the engine; returns (ok, message)."""
    exe = require_ssynthgen(binary)
    with tempfile.NamedTemporaryFile("w", suffix=".es", delete=False, encoding="utf-8") as tf:
        tf.write(script)
        script_path = tf.name
    out_fd, out_path = tempfile.mkstemp(suffix=".obj")
    try:
        with os.fdopen(out_fd, "wb") as sink:
            try:
                proc = subprocess.run(
                    [exe, script_path],
                    stdout=sink,
                    stderr=subprocess.PIPE,
                    timeout=timeout,
                )
            except subprocess.TimeoutExpired:
                return False, f"Validation timed out after {timeout}s."
    finally:
        Path(out_path).unlink(missing_ok=True)
        Path(script_path).unlink(missing_ok=True)

    if proc.returncode == 0:
        return True, "OK"
    stderr = (proc.stderr or b"").decode("utf-8", "replace").strip()
    if proc.returncode in (-6, 134) or "terminate called" in stderr:
        return False, "Parse error: the engine rejected this EisenScript."
    # Patched ssynthgen puts line info in stderr, e.g. "... (line 3)".
    return False, stderr or f"Engine failed with exit code {proc.returncode}."
