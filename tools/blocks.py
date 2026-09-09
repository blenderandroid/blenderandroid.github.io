#!/usr/bin/env python3
"""Convert between markdown and Editor.js blocks.

Markdown on disk stays the source of truth, because `build.py import` pulls
markdown out of GitHub release notes and because a diff of a markdown file is
readable. The editor speaks blocks, so this module translates both ways.

The contract that matters: **round-tripping must never lose content.** Anything
this module cannot model as a block, such as a nested list or a GitHub alert,
becomes a `raw` block holding its original markdown verbatim, and is written
back out unchanged. Silent loss is the one failure mode not tolerated here.
"""

import html as _html
import re
from html.parser import HTMLParser

HEADING = re.compile(r"^(#{1,6})\s+(.*)$")
UL_ITEM = re.compile(r"^([-*+])\s+(.*)$")
OL_ITEM = re.compile(r"^(\d+)\.\s+(.*)$")
IMAGE_ONLY = re.compile(r"^!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)$")
RULE = re.compile(r"^(-{3,}|\*{3,}|_{3,})$")
YT_ID = re.compile(r"(?:youtu\.be/|v=|embed/|shorts/)([A-Za-z0-9_-]{6,20})")

INLINE_CODE = re.compile(r"`([^`]+)`")
IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)")
LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
BOLD = re.compile(r"\*\*(.+?)\*\*", re.S)
ITALIC = re.compile(r"(?<![\*\w])\*([^\*\n]+)\*(?!\*)")


# --------------------------------------------------------------------------
# Inline: markdown <-> the small HTML subset Editor.js uses
# --------------------------------------------------------------------------

def inline_to_html(text):
    spans = []

    def stash(m):
        spans.append(m.group(1))
        return "\x00%d\x00" % (len(spans) - 1)

    text = INLINE_CODE.sub(stash, text)
    text = _html.escape(text, quote=False)
    text = IMAGE.sub(lambda m: '<img src="%s" alt="%s">'
                     % (_html.escape(m.group(2), quote=True),
                        _html.escape(m.group(1), quote=True)), text)
    text = LINK.sub(lambda m: '<a href="%s">%s</a>'
                    % (_html.escape(m.group(2), quote=True), m.group(1)), text)
    text = BOLD.sub(lambda m: "<b>%s</b>" % m.group(1), text)
    text = ITALIC.sub(lambda m: "<i>%s</i>" % m.group(1), text)
    for idx, code in enumerate(spans):
        text = text.replace("\x00%d\x00" % idx,
                            "<code>%s</code>" % _html.escape(code, quote=False))
    return text


class _ToMarkdown(HTMLParser):
    """Walk Editor.js inline HTML back into markdown."""

    WRAP = {"b": "**", "strong": "**", "i": "*", "em": "*", "code": "`"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.href = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in self.WRAP:
            self.out.append(self.WRAP[tag])
        elif tag == "a":
            self.out.append("[")
            self.href.append(a.get("href", ""))
        elif tag == "img":
            self.out.append("![%s](%s)" % (a.get("alt", ""), a.get("src", "")))
        elif tag == "br":
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in self.WRAP:
            self.out.append(self.WRAP[tag])
        elif tag == "a":
            href = self.href.pop() if self.href else ""
            self.out.append("](%s)" % href)

    def handle_data(self, data):
        self.out.append(data)

    def value(self):
        return re.sub(r"[ \t]+", " ", "".join(self.out)).strip()


def html_to_inline(text):
    p = _ToMarkdown()
    p.feed(text or "")
    p.close()
    return p.value()


# --------------------------------------------------------------------------
# markdown -> blocks
# --------------------------------------------------------------------------

def _blk(kind, data):
    return {"type": kind, "data": data}


def markdown_to_blocks(md):
    lines = (md or "").replace("\r\n", "\n").split("\n")
    out = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        s = line.strip()

        if not s:
            i += 1
            continue

        # fenced block: code, or a video embed
        if s.startswith("```"):
            lang = s[3:].strip()
            start = i
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            body = "\n".join(buf)
            if lang.lower() in ("youtube", "video"):
                m = YT_ID.search(body.strip())
                vid = m.group(1) if m else body.strip()
                out.append(_blk("embed", {
                    "service": "youtube",
                    "source": "https://www.youtube.com/watch?v=%s" % vid,
                    "embed": "https://www.youtube-nocookie.com/embed/%s" % vid,
                    "caption": "",
                }))
            else:
                out.append(_blk("code", {"code": body, "language": lang}))
            continue

        if RULE.match(s):
            out.append(_blk("delimiter", {}))
            i += 1
            continue

        m = HEADING.match(s)
        if m:
            out.append(_blk("header", {
                "text": inline_to_html(m.group(2).strip()),
                "level": min(len(m.group(1)) + 1, 6),
            }))
            i += 1
            continue

        m = IMAGE_ONLY.match(s)
        if m:
            out.append(_blk("image", {
                "file": {"url": m.group(2)},
                "caption": inline_to_html(m.group(3) or m.group(1) or ""),
                "withBorder": False, "withBackground": False, "stretched": False,
            }))
            i += 1
            continue

        # table: header row plus separator
        if "|" in s and i + 1 < n and re.fullmatch(r"[\s|:\-]+", lines[i + 1].strip()) \
                and "-" in lines[i + 1]:
            rows = []
            while i < n and "|" in lines[i]:
                rows.append([inline_to_html(c) for c in _cells(lines[i])])
                i += 1
            if len(rows) >= 2:
                del rows[1]
                out.append(_blk("table", {"withHeadings": True, "content": rows}))
                continue

        # blockquote: a plain one becomes a quote, an alert stays raw
        if s.startswith(">"):
            start = i
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            joined = "\n".join(buf).strip()
            if re.match(r"^\[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]", joined, re.I):
                out.append(_raw(lines[start:i]))
            else:
                out.append(_blk("quote", {
                    "text": inline_to_html(" ".join(x.strip() for x in buf if x.strip())),
                    "caption": "", "alignment": "left",
                }))
            continue

        # list: flat only. Anything nested is kept verbatim.
        if UL_ITEM.match(s) or OL_ITEM.match(s):
            ordered = bool(OL_ITEM.match(s))
            start = i
            items = []
            nested = False
            while i < n:
                cur = lines[i]
                if not cur.strip():
                    nxt = i + 1
                    while nxt < n and not lines[nxt].strip():
                        nxt += 1
                    if nxt < n and _indent(lines[nxt]) == 0 \
                            and (UL_ITEM.match(lines[nxt].strip())
                                 or OL_ITEM.match(lines[nxt].strip())):
                        i = nxt
                        continue
                    break
                if _indent(cur) > 0:
                    # indented: a real sub-list is nesting, anything else is
                    # just a wrapped line belonging to the item above
                    stripped_cur = cur.strip()
                    if UL_ITEM.match(stripped_cur) or OL_ITEM.match(stripped_cur):
                        nested = True
                        i += 1
                        continue
                    if items:
                        items[-1] = items[-1] + " " + inline_to_html(stripped_cur)
                        i += 1
                        continue
                    break
                mm = OL_ITEM.match(cur.strip()) if ordered else UL_ITEM.match(cur.strip())
                if not mm:
                    break
                items.append(inline_to_html(mm.group(2).strip()))
                i += 1
            if nested:
                out.append(_raw(lines[start:i]))
            else:
                out.append(_blk("list", {
                    "style": "ordered" if ordered else "unordered",
                    "items": items,
                }))
            continue

        # paragraph
        buf = []
        while i < n and lines[i].strip() and not _starts_block(lines[i]):
            buf.append(lines[i].strip())
            i += 1
        if buf:
            out.append(_blk("paragraph", {"text": inline_to_html(" ".join(buf))}))
        else:
            i += 1

    return out


def _indent(line):
    return len(line) - len(line.lstrip(" "))


def _cells(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def _raw(lines):
    return _blk("raw", {"html": "\n".join(lines).strip()})


def _starts_block(line):
    s = line.strip()
    return bool(HEADING.match(s) or s.startswith((">", "```"))
                or UL_ITEM.match(s) or OL_ITEM.match(s) or RULE.match(s))


# --------------------------------------------------------------------------
# blocks -> markdown
# --------------------------------------------------------------------------

def blocks_to_markdown(blocks):
    parts = []
    for b in blocks or []:
        kind = b.get("type")
        d = b.get("data") or {}

        if kind == "header":
            level = int(d.get("level", 2))
            # the page owns h1 and h2, so a heading never rises above markdown h2
            hashes = "#" * max(1, level - 1)
            parts.append("%s %s" % (hashes, html_to_inline(d.get("text", ""))))

        elif kind == "paragraph":
            text = html_to_inline(d.get("text", ""))
            if text:
                parts.append(text)

        elif kind == "list":
            ordered = d.get("style") == "ordered"
            rows = []
            for idx, item in enumerate(d.get("items") or [], 1):
                if isinstance(item, dict):          # Editor.js v2 nested shape
                    item = item.get("content", "")
                bullet = "%d." % idx if ordered else "-"
                rows.append("%s %s" % (bullet, html_to_inline(item)))
            parts.append("\n".join(rows))

        elif kind == "image":
            url = (d.get("file") or {}).get("url") or d.get("url", "")
            cap = html_to_inline(d.get("caption", ""))
            if cap:
                parts.append('![%s](%s "%s")' % (cap, url, cap))
            else:
                parts.append("![](%s)" % url)

        elif kind == "embed":
            src = d.get("source") or d.get("embed") or ""
            m = YT_ID.search(src)
            parts.append("```youtube\n%s\n```" % (m.group(1) if m else src))

        elif kind == "code":
            lang = d.get("language") or ""
            parts.append("```%s\n%s\n```" % (lang, d.get("code", "")))

        elif kind == "quote":
            text = html_to_inline(d.get("text", ""))
            parts.append("\n".join("> " + ln for ln in text.split("\n")))

        elif kind == "table":
            rows = d.get("content") or []
            if rows:
                head = ["| " + " | ".join(html_to_inline(c) for c in rows[0]) + " |",
                        "|" + "|".join(["---"] * len(rows[0])) + "|"]
                for r in rows[1:]:
                    head.append("| " + " | ".join(html_to_inline(c) for c in r) + " |")
                parts.append("\n".join(head))

        elif kind == "delimiter":
            parts.append("---")

        elif kind == "raw":
            parts.append(d.get("html", ""))

    return "\n\n".join(p for p in parts if p.strip()) + "\n"


if __name__ == "__main__":
    import sys
    src = open(sys.argv[1], encoding="utf-8").read()
    import json
    print(json.dumps(markdown_to_blocks(src), indent=1)[:4000])
