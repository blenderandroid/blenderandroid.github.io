#!/usr/bin/env python3
"""Surgical edits to the YAML subset used by content/site.yaml.

Re-serialising the file from parsed data would throw away its comments,
its blank lines and its chosen line breaks. So this module indexes where each
value physically lives and rewrites only those lines. Everything it does not
touch comes out byte for byte identical.

Paths are dotted, with integers for list positions:

    standfirst
    tracks.main.name
    tracks.main.points.0.text
    requirements.1.detail
"""

import re

SCALAR = "scalar"
FOLDED = "folded"     # key: >
LITERAL = "literal"   # key: |


def _indent(line):
    return len(line) - len(line.lstrip(" "))


def _is_content(line):
    return bool(line.strip()) and not line.lstrip().startswith("#")


def index(text):
    """Map every scalar path to where it lives: {path: {kind, line, end, indent}}."""
    lines = text.replace("\r\n", "\n").split("\n")
    out = {}
    _walk_map(lines, 0, len(lines), _base_indent(lines), [], out)
    return out


def _base_indent(lines):
    for ln in lines:
        if _is_content(ln):
            return _indent(ln)
    return 0


def _next_content(lines, i, end):
    while i < end and not _is_content(lines[i]):
        i += 1
    return i


def _block_end(lines, i, end, indent):
    """Where a block scalar or nested structure that started at i stops."""
    j = i
    while j < end:
        if not _is_content(lines[j]):
            j += 1
            continue
        if _indent(lines[j]) <= indent:
            break
        j += 1
    # trim trailing blanks back out of the block
    while j - 1 > i and not lines[j - 1].strip():
        j -= 1
    return j


def _walk_map(lines, start, end, indent, path, out):
    i = start
    while i < end:
        i = _next_content(lines, i, end)
        if i >= end:
            return
        line = lines[i]
        cur = _indent(line)
        if cur < indent:
            return
        s = line.strip()
        if s.startswith("- "):
            return
        if ":" not in s:
            i += 1
            continue
        key, _, rest = s.partition(":")
        key = key.strip()
        rest = rest.strip()
        here = path + [key]
        dotted = ".".join(here)

        if rest in (">", "|"):
            stop = _block_end(lines, i + 1, end, cur)
            out[dotted] = {"kind": FOLDED if rest == ">" else LITERAL,
                           "line": i, "end": stop, "indent": cur + 2}
            i = stop
            continue

        if rest == "":
            nxt = _next_content(lines, i + 1, end)
            if nxt < end and _indent(lines[nxt]) > cur:
                stop = _block_end(lines, nxt, end, cur)
                if lines[nxt].strip().startswith("- "):
                    _walk_list(lines, nxt, stop, _indent(lines[nxt]), here, out)
                else:
                    _walk_map(lines, nxt, stop, _indent(lines[nxt]), here, out)
                i = stop
                continue
            out[dotted] = {"kind": SCALAR, "line": i, "end": i + 1, "indent": cur}
            i += 1
            continue

        out[dotted] = {"kind": SCALAR, "line": i, "end": i + 1, "indent": cur}
        i += 1


def _walk_list(lines, start, end, indent, path, out):
    i = start
    n = 0
    while i < end:
        i = _next_content(lines, i, end)
        if i >= end:
            return
        if _indent(lines[i]) < indent or not lines[i].strip().startswith("- "):
            return
        stop = i + 1
        while stop < end:
            if not _is_content(lines[stop]):
                stop += 1
                continue
            if _indent(lines[stop]) <= indent:
                break
            stop += 1
        body = lines[i].strip()[2:]
        if ":" in body and not body.startswith(("http://", "https://")):
            # rewrite the dash line as a plain key so the map walker sees it
            shim = list(lines)
            shim[i] = " " * (indent + 2) + body
            _walk_map(shim, i, stop, indent + 2, path + [str(n)], out)
        n += 1
        i = stop


def _quote(value):
    v = str(value)
    if v == "":
        return '""'
    needs = (":" in v or v.strip() != v or v[0] in "\"'#-[]{}&*!|>%@`"
             or v.lower() in ("true", "false", "yes", "no", "null", "~"))
    if needs:
        return '"%s"' % v.replace("\\", "\\\\").replace('"', '\\"')
    return v


def _wrap(text, width, indent):
    words, out, cur = str(text).split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > width:
            out.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    if cur:
        out.append(cur)
    return [" " * indent + ln for ln in out] or [" " * indent]


def set_values(text, updates):
    """Apply {path: new value}. Returns the new text; unknown paths are ignored."""
    lines = text.replace("\r\n", "\n").split("\n")
    idx = index(text)

    # apply bottom-up so earlier line numbers stay valid
    targets = [(p, v) for p, v in updates.items() if p in idx]
    targets.sort(key=lambda pv: idx[pv[0]]["line"], reverse=True)

    for path, value in targets:
        spot = idx[path]
        key = path.split(".")[-1]
        value = "" if value is None else str(value).replace("\r\n", "\n").strip()

        if spot["kind"] == SCALAR:
            pad = " " * spot["indent"]
            line = lines[spot["line"]]
            # a list item keeps its dash
            dash = "- " if line.lstrip().startswith("- ") else ""
            if dash:
                pad = " " * (spot["indent"] - 2)
            lines[spot["line"]:spot["end"]] = [
                "%s%s%s: %s" % (pad, dash, key, _quote(value))]
        else:
            keep_newlines = spot["kind"] == LITERAL
            pad = " " * spot["indent"]
            if keep_newlines:
                body = [pad + ln for ln in value.split("\n")]
            else:
                body = _wrap(value, 76 - spot["indent"], spot["indent"])
            head = lines[spot["line"]]
            lines[spot["line"]:spot["end"]] = [head] + body

    return "\n".join(lines)


def get_values(text, paths):
    """Read the current value at each path, for populating a form."""
    lines = text.replace("\r\n", "\n").split("\n")
    idx = index(text)
    out = {}
    for p in paths:
        if p not in idx:
            continue
        spot = idx[p]
        if spot["kind"] == SCALAR:
            s = lines[spot["line"]].strip()
            if s.startswith("- "):
                s = s[2:]
            _, _, rest = s.partition(":")
            rest = rest.strip()
            if len(rest) >= 2 and rest[0] in "\"'" and rest[-1] == rest[0]:
                rest = rest[1:-1]
            out[p] = rest
        else:
            body = [lines[j].strip() for j in range(spot["line"] + 1, spot["end"])]
            out[p] = ("\n".join(body) if spot["kind"] == LITERAL
                      else " ".join(x for x in body if x))
    return out
