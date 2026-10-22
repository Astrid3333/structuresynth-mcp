"""Static analyzer (linter) for EisenScript, tailored to the libssynth backend."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

SUPPORTED_PRIMITIVES = {
    "box", "sphere", "cylinder", "line", "dot", "grid", "mesh", "template",
}
ORIGINAL_ONLY_PRIMITIVES = {
    "torus", "cone", "tube", "helix", "circle", "point",
}
TRANSFORMATIONS = {
    "x", "y", "z", "rx", "ry", "rz", "s", "matrix", "reflect",
    "fx", "fy", "fz", "hue", "sat", "brightness", "val", "v",
    "color", "alpha",
}
MODIFIERS = {"weight", "w", "maxdepth", "md"}
SET_COMMANDS = {"seed", "colorpool", "background", "maxdepth", "recursion"}
KEYWORDS = SUPPORTED_PRIMITIVES | TRANSFORMATIONS | MODIFIERS | SET_COMMANDS | {
    "rule", "set", "random",
}

_RULE_RE = re.compile(r"\brule\s+([A-Za-z_]\w*)", re.IGNORECASE)
_WORD_RE = re.compile(r"[A-Za-z_]\w*")
_COMMENT_RE = re.compile(r"/\*.*?\*/|//[^\n]*", re.DOTALL)
_SET_MAXDEPTH_RE = re.compile(r"\bset\s+maxdepth\s+(\d+)", re.IGNORECASE)


@dataclass
class Analysis:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    info: dict = field(default_factory=dict)


def _strip_comments(src: str) -> str:
    return _COMMENT_RE.sub(" ", src)


def _brace_match(src: str) -> tuple[bool, str | None]:
    depth = 0
    for ch in src:
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth < 0:
                return False, "Closing '}' without matching '{'."
    if depth > 0:
        return False, f"Unclosed '{{' ({depth} still open)."
    return True, None


def _rule_spans(src: str) -> list[tuple[str, int, int, str]]:
    """Return (name, start, end, body) for each `rule name ... { ... }` block."""
    spans: list[tuple[str, int, int, str]] = []
    for m in _RULE_RE.finditer(src):
        name = m.group(1)
        brace_at = src.find("{", m.end())
        if brace_at < 0:
            continue
        depth = 0
        for i in range(brace_at, len(src)):
            if src[i] == "{":
                depth += 1
            elif src[i] == "}":
                depth -= 1
                if depth == 0:
                    spans.append((name, m.start(), i + 1, src[brace_at + 1:i]))
                    break
    return spans


def _rule_bodies(src: str) -> dict[str, str]:
    return {name: body for name, _, _, body in _rule_spans(src)}


def _called_rules(text: str, rule_names: set[str]) -> set[str]:
    """Rule names referenced as actions inside text."""
    # Remove transformation blocks so their keywords aren't mistaken for calls.
    stripped = re.sub(r"\{[^}]*\}", " ", text)
    return {w for w in _WORD_RE.findall(stripped) if w in rule_names}


def _find_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """Simple DFS cycle enumeration (small graphs: rule call graph)."""
    cycles: list[list[str]] = []
    visited: set[str] = set()

    def dfs(node: str, stack: list[str]) -> None:
        for nxt in graph.get(node, ()):
            if nxt in stack:
                cyc = stack[stack.index(nxt):] + [nxt]
                key = tuple(sorted(set(cyc)))
                if key not in {tuple(sorted(set(c))) for c in cycles}:
                    cycles.append(cyc)
            elif nxt not in visited:
                dfs(nxt, stack + [nxt])

    for n in graph:
        if n not in visited:
            visited.add(n)
            dfs(n, [n])
    return cycles


def analyze(script: str) -> Analysis:
    """Lint an EisenScript: braces, unknown actions, recursion/maxdepth, info."""
    res = Analysis(ok=True)
    src = _strip_comments(script)

    balanced, brace_err = _brace_match(src)
    if not balanced:
        res.errors.append(brace_err or "Unbalanced braces.")
        res.ok = False
        return res

    rule_names = {m.group(1) for m in _RULE_RE.finditer(src)}
    bodies = _rule_bodies(src)
    global_md = _SET_MAXDEPTH_RE.search(src)
    global_maxdepth = int(global_md.group(1)) if global_md else None

    # Modifiers per rule: everything between rule name and '{'.
    rule_maxdepth: dict[str, int | None] = {}
    for m in _RULE_RE.finditer(src):
        name = m.group(1)
        brace_at = src.find("{", m.end())
        header = src[m.end():brace_at] if brace_at >= 0 else ""
        md = re.search(r"\b(?:maxdepth|md)\s+(\d+)", header, re.IGNORECASE)
        rule_maxdepth[name] = int(md.group(1)) if md else None

    # Word tokens in action positions. Rule bodies and top-level code both
    # contain `{ transforms } action` sequences; strip only the innermost
    # transformation blocks by first removing rule definitions, then scanning
    # top-level + each body separately (bodies still have their own { } blocks).
    spans = _rule_spans(src)
    top_level = src
    for _, start, end, _ in sorted(spans, key=lambda s: -s[1]):
        top_level = top_level[:start] + top_level[end:]

    def action_words(code: str) -> list[str]:
        stripped = re.sub(r"\{[^}]*\}", " ", code)
        return _WORD_RE.findall(stripped)

    used: set[str] = set()
    warn_seen: set[str] = set()

    def classify(words: list[str]) -> None:
        for w in words:
            if w in rule_names or w in KEYWORDS:
                used.add(w)
                continue
            if w in ORIGINAL_ONLY_PRIMITIVES:
                if w not in warn_seen:
                    warn_seen.add(w)
                    res.warnings.append(
                        f"Primitive '{w}' exists in the original Structure Synth "
                        "but is NOT supported by this backend (libssynth) — it "
                        "will fail to parse."
                    )
            else:
                msg = f"Unknown action '{w}': not a rule, primitive, or keyword."
                if msg not in res.errors:
                    res.errors.append(msg)

    classify(action_words(top_level))
    for _, _, _, body in spans:
        classify(action_words(body))

    # Recursion analysis.
    graph = {name: _called_rules(bodies.get(name, ""), rule_names) for name in rule_names}
    called_anywhere = set().union(*graph.values()) if graph else set()
    top_calls = _called_rules(top_level, rule_names)
    for name in sorted(rule_names):
        if name not in called_anywhere and name not in top_calls:
            res.warnings.append(f"Rule '{name}' is defined but never called.")

    cycles = _find_cycles(graph)
    if cycles and global_maxdepth is None:
        unprotected = [
            cyc for cyc in cycles
            if all(rule_maxdepth.get(n) is None for n in cyc if n in rule_maxdepth)
        ]
        for cyc in unprotected:
            res.warnings.append(
                f"Recursion cycle {' -> '.join(cyc)} has no 'maxdepth' modifier "
                "and no global 'set maxdepth' — this may time out."
            )

    if not rule_names and not SUPPORTED_PRIMITIVES.intersection(
        action_words(top_level)
    ):
        res.warnings.append("Script defines no rules and draws no primitives.")

    res.info = {
        "rules": sorted(rule_names),
        "rule_count": len(rule_names),
        "global_maxdepth": global_maxdepth,
        "cycles": [" -> ".join(c) for c in cycles],
        "has_seed": bool(re.search(r"\bset\s+seed\b", src, re.IGNORECASE)),
    }
    res.ok = not res.errors
    return res
