#!/usr/bin/env python3
"""Self-hosted visual editor for the site. No AI, no Node, no database.

    python tools/edit.py            editor at http://127.0.0.1:8000/admin/
    python tools/edit.py -p 8777    another port

Serves the built site at / and the editor at /admin/. Saving writes back to
content/ and rebuilds, so the preview on the left is always the real page.

What it edits:

  Landing page   the text inside each block, through forms. Structure, order
                 and design are not editable here on purpose; they live in
                 assets/site.css and the templates, so a contributor cannot
                 break the layout by editing copy.
  Log posts      title, summary and the body, in a block editor with headings,
                 lists, quotes, code, tables, images and YouTube embeds.

Adding a post is still a script: `build.py import <url>` for a release, or
`build.py new --title "..."` for an announcement.
"""

import argparse
import functools
import http.server
import json
import os
import posixpath
import re
import shutil
import socketserver
import sys
import time
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import blocks as blockmod          # noqa: E402
import build                       # noqa: E402
import yamledit                    # noqa: E402

ROOT = build.ROOT
EDITOR_DIR = os.path.join(HERE, "editor")
MEDIA_DIR = os.path.join(ROOT, "assets", "media")
SITE_YAML = os.path.join(build.CONTENT, "site.yaml")

# Paths never offered in the form: identifiers, URLs and switches that would
# break the build rather than change a word of copy.
SKIP_KEYS = {"id", "warn", "repo", "repo_url", "releases_url", "url",
             "feed_on_home", "signing_fingerprint"}

GROUP_TITLES = {
    "": "Site",
    "requirements": "Device requirements",
    "install_steps": "Install steps",
    "tracks": "Builds",
    "kinds": "Post kinds",
}

LABELS = {
    "title": "Site title",
    "description": "Search description",
    "standfirst": "Hero line",
    "disclaimer": "Disclaimer (hero, header and footer)",
    "licence": "Footer licence line",
    "device_lede": "Device section intro",
    "builds_lede": "Builds section intro",
    "download_lede": "Download section intro",
    "updates_lede": "Porting log intro",
    "alpha_note": "Alpha warning",
    "name": "Name",
    "lede": "Description",
    "value": "Short value",
    "check": "Checklist heading",
    "detail": "Checklist explanation",
    "lead": "Bold lead-in",
    "text": "Text",
}


# --------------------------------------------------------------------------
# Landing page fields
# --------------------------------------------------------------------------

def humanise(path):
    key = path.split(".")[-1]
    return LABELS.get(key, key.replace("_", " ").capitalize())


def site_groups():
    text = open(SITE_YAML, encoding="utf-8").read()
    idx = yamledit.index(text)
    data = build.parse_yaml(text)
    paths = [p for p in idx if p.split(".")[-1] not in SKIP_KEYS]
    values = yamledit.get_values(text, paths)

    groups, order = {}, []
    for path in paths:
        parts = path.split(".")
        top = parts[0] if len(parts) > 1 else ""
        if top == "tracks":
            gid = "tracks.%s" % parts[1]
            gtitle = "Build: %s" % data["tracks"][parts[1]].get("name", parts[1])
        elif top in GROUP_TITLES and len(parts) > 1:
            gid, gtitle = top, GROUP_TITLES[top]
        else:
            gid, gtitle = "", GROUP_TITLES[""]
        if gid not in groups:
            groups[gid] = {"id": gid or "site", "title": gtitle, "fields": []}
            order.append(gid)
        val = values.get(path, "")
        groups[gid]["fields"].append({
            "path": path,
            "label": humanise(path),
            "value": val,
            "multiline": idx[path]["kind"] != yamledit.SCALAR or len(val) > 90,
            "sub": _sub_label(path, data),
        })
    return [groups[g] for g in order]


def _sub_label(path, data):
    """A short note saying which repeated item a field belongs to."""
    parts = path.split(".")
    for i, p in enumerate(parts):
        if p.isdigit():
            parent = parts[:i]
            try:
                node = data
                for k in parent:
                    node = node[k]
                item = node[int(p)]
            except Exception:
                return ""
            for key in ("value", "title", "lead", "name", "text"):
                if isinstance(item, dict) and item.get(key):
                    return str(item[key])[:48]
            return "#%d" % (int(p) + 1)
    return ""


# --------------------------------------------------------------------------
# Posts
# --------------------------------------------------------------------------

DIRS = {"post": build.UPDATES_DIR, "page": build.PAGES_DIR}


def doc_path(kind, slug):
    base = DIRS[kind]
    p = os.path.join(base, slug + ".md")
    if not os.path.abspath(p).startswith(os.path.abspath(base)):
        raise ValueError("bad slug")
    return p


def post_path(slug):
    return doc_path("post", slug)


def list_pages():
    out = []
    for pg in build.load_pages():
        out.append({"slug": pg.slug, "title": pg.title, "nav": pg.nav,
                    "url": pg.url, "order": pg.order})
    return out


def list_posts():
    out = []
    site = build.load_site()
    for u in build.load_updates():
        out.append({
            "slug": u.slug,
            "file": os.path.basename(u.path),
            "title": u.title,
            "date": u.date.isoformat(),
            "dateLabel": u.date_label(),
            "track": u.track,
            "trackLabel": build.kind_label(site, u.track),
            "tag": u.tag,
            "assets": len(u.assets),
            "url": "/updates/%s/" % u.slug,
        })
    return out


def read_doc(kind, slug):
    with open(doc_path(kind, slug), encoding="utf-8") as fh:
        meta, body = build.split_frontmatter(fh.read())
    url = ("/updates/%s/" % slug) if kind == "post" else ("/%s/" % slug)
    return {"kind": kind, "slug": slug, "meta": meta,
            "blocks": blockmod.markdown_to_blocks(body), "url": url}


def read_post(slug):
    return read_doc("post", slug)


FM_ORDER = ["title", "track", "tag", "date", "release_url", "summary"]
PAGE_FM_ORDER = ["title", "nav", "order", "lede", "description"]

# frontmatter keys the page editor writes as folded blocks rather than one line
FOLDED_KEYS = {"summary", "lede", "description"}


def write_doc(kind, slug, meta, blks):
    if kind == "page":
        return write_page(slug, meta, blks)
    return write_post(slug, meta, blks)


def write_page(slug, meta, blks):
    path = doc_path("page", slug)
    with open(path, encoding="utf-8") as fh:
        old_meta, _ = build.split_frontmatter(fh.read())
    merged = dict(old_meta)
    for k, v in (meta or {}).items():
        merged[k] = v

    lines = ["---"]
    seen = set()
    for key in PAGE_FM_ORDER + [k for k in merged if k not in PAGE_FM_ORDER]:
        if key in seen or key not in merged:
            continue
        seen.add(key)
        val = merged[key]
        if key in FOLDED_KEYS and str(val).strip():
            lines.append("%s: >" % key)
            lines.extend(yamledit._wrap(str(val), 74, 2))
        else:
            lines.append("%s: %s" % (key, _fm_scalar(val)))
    lines.append("---")
    lines.append("")
    text = "\n".join(lines) + "\n" + blockmod.blocks_to_markdown(blks)
    atomic_write(path, text)
    return text


def write_post(slug, meta, blks):
    path = post_path(slug)
    with open(path, encoding="utf-8") as fh:
        old_meta, _ = build.split_frontmatter(fh.read())

    merged = dict(old_meta)
    for k, v in (meta or {}).items():
        merged[k] = v

    body = blockmod.blocks_to_markdown(blks)

    lines = ["---"]
    for key in FM_ORDER:
        if key not in merged:
            continue
        val = merged.get(key)
        if key == "summary":
            lines.append("summary: >")
            for ln in yamledit._wrap(val or "", 74, 2):
                lines.append(ln)
        else:
            lines.append("%s: %s" % (key, _fm_scalar(val)))
    for key in merged:
        if key in FM_ORDER or key == "assets":
            continue
        lines.append("%s: %s" % (key, _fm_scalar(merged[key])))

    lines.append("assets:")
    for a in merged.get("assets") or []:
        lines.append("  - name: %s" % _fm_scalar(a.get("name", "")))
        lines.append("    label: %s" % _fm_scalar(a.get("label", "")))
        lines.append("    bytes: %d" % int(a.get("bytes") or 0))
        lines.append("    url: %s" % (a.get("url") or ""))
        lines.append("    sha256: %s" % (a.get("sha256") or ""))
        if a.get("downloads") is not None:
            lines.append("    downloads: %d" % int(a.get("downloads") or 0))
    lines.append("---")
    lines.append("")
    text = "\n".join(lines) + "\n" + body

    atomic_write(path, text)
    return text


def _fm_scalar(v):
    if v is True:
        return "true"
    if v is False:
        return "false"
    if v is None:
        return ""
    s = str(v)
    if s == "":
        return ""
    if s.strip() != s or s[0] in "\"'#-[]{}&*!|>%@`" or ": " in s:
        return '"%s"' % s.replace("\\", "\\\\").replace('"', '\\"')
    return s


def atomic_write(path, text):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    os.replace(tmp, path)


def rebuild():
    started = time.time()
    build.cmd_build(None)
    return int((time.time() - started) * 1000)


# --------------------------------------------------------------------------
# HTML shells
# --------------------------------------------------------------------------

def page(title, body, script=""):
    return """<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<link rel="stylesheet" href="/admin/static/admin.css">
</head><body>
%s
<script src="/admin/static/common.js"></script>
%s
</body></html>""" % (build._esc(title), body, script)


def topbar(active, extra=""):
    def tab(href, label, key):
        cls = ' class="on"' if key == active else ""
        return '<a%s href="%s">%s</a>' % (cls, href, label)
    return """
<header class="bar">
  <div class="bar-l">
    <span class="logo">Blender on Android</span>
    <nav>%s%s%s</nav>
  </div>
  <div class="bar-r">%s
    <a class="ghost" href="/" target="_blank" rel="noopener">View site</a>
  </div>
</header>""" % (tab("/admin/", "Posts", "posts"),
                tab("/admin/site", "Landing page", "site"),
                tab("/admin/pages", "Pages", "pages"), extra)


def dashboard_html():
    rows = []
    for p in list_posts():
        rows.append("""
      <a class="row" href="/admin/post/%(slug)s">
        <div class="row-main">
          <div class="row-title">%(title)s</div>
          <div class="row-meta"><span class="chip %(cls)s">%(track)s</span>
            <span>%(date)s</span>%(tag)s%(assets)s</div>
        </div>
        <div class="row-go">Edit</div>
      </a>""" % {
            "slug": p["slug"],
            "title": build._esc(p["title"] or "(untitled)"),
            "cls": {"main": "up", "s24": "dn"}.get(p["track"], "nw"),
            "track": build._esc(p["trackLabel"]),
            "date": build._esc(p["dateLabel"]),
            "tag": ('<span class="mono">%s</span>' % build._esc(p["tag"])) if p["tag"] else "",
            "assets": ('<span>%d file%s</span>' % (p["assets"], "" if p["assets"] == 1 else "s"))
                      if p["assets"] else "",
        })
    body = """
%s
<main class="wrap">
  <div class="head">
    <h1>Porting log</h1>
    <p>Edit an existing post. To add one, use the script:
      <code>python tools/build.py import &lt;release url&gt;</code> for a release, or
      <code>python tools/build.py new --title "..."</code> for an announcement.</p>
  </div>
  <div class="rows">%s</div>
</main>""" % (topbar("posts"), "".join(rows))
    return page("Posts", body)


def pages_html():
    rows = []
    for pg in list_pages():
        rows.append("""
      <a class="row" href="/admin/page/%(slug)s">
        <div class="row-main">
          <div class="row-title">%(title)s</div>
          <div class="row-meta"><span class="mono">%(url)s</span>
            <span>menu: %(nav)s</span></div>
        </div>
        <div class="row-go">Edit</div>
      </a>""" % {"slug": pg["slug"], "title": build._esc(pg["title"]),
                 "url": build._esc(pg["url"]), "nav": build._esc(pg["nav"])})
    if not rows:
        rows.append('<div class="row"><div class="row-main">No pages yet.</div></div>')
    body = """
%s
<main class="wrap">
  <div class="head">
    <h1>Pages</h1>
    <p>Standalone pages such as About. To add one, create a markdown file in
      <code>content/pages/</code> and it appears here, in the footer and in the
      header menu.</p>
  </div>
  <div class="rows">%s</div>
</main>""" % (topbar("pages"), "".join(rows))
    return page("Pages", body)


def site_html():
    groups = []
    for g in site_groups():
        fields = []
        for f in g["fields"]:
            fid = "f_" + re.sub(r"[^a-zA-Z0-9]", "_", f["path"])
            sub = ('<span class="sub">%s</span>' % build._esc(f["sub"])) if f["sub"] else ""
            if f["multiline"]:
                ctl = ('<textarea id="%s" data-path="%s" rows="3">%s</textarea>'
                       % (fid, build._esc(f["path"]), build._esc(f["value"])))
            else:
                ctl = ('<input id="%s" data-path="%s" value="%s">'
                       % (fid, build._esc(f["path"]),
                          f["value"].replace('"', "&quot;")))
            fields.append('<div class="field"><label for="%s">%s%s</label>%s</div>'
                          % (fid, build._esc(f["label"]), sub, ctl))
        groups.append('<section class="group"><h2>%s</h2>%s</section>'
                      % (build._esc(g["title"]), "".join(fields)))
    body = """
%s
<main class="wrap split">
  <div class="col-form">
    <div class="head">
      <h1>Landing page</h1>
      <p>Every string on the front page. Structure and design are not editable
         here, so nothing you type can break the layout.</p>
    </div>
    %s
  </div>
  <aside class="col-preview">
    <div class="preview-bar"><span>Preview</span><button class="ghost" id="refresh">Refresh</button></div>
    <iframe id="preview" src="/?admin=1"></iframe>
  </aside>
</main>
<div class="savebar"><span id="status"></span><button id="save">Save and rebuild</button></div>
""" % (topbar("site"), "".join(groups))
    return page("Landing page", body, '<script src="/admin/static/site.js"></script>')


POST_DETAILS = """
    <section class="group">
      <h2>Post details</h2>
      <div class="field"><label for="m_title">Title</label>
        <input id="m_title" value=""></div>
      <div class="field"><label for="m_summary">Summary <span class="sub">what the feed shows</span></label>
        <textarea id="m_summary" rows="3"></textarea></div>
      <div class="field two">
        <div><label for="m_date">Date</label><input id="m_date" type="date"></div>
        <div><label for="m_tag">Tag</label><input id="m_tag"></div>
      </div>
    </section>"""

PAGE_DETAILS = """
    <section class="group">
      <h2>Page details</h2>
      <div class="field"><label for="m_title">Title</label>
        <input id="m_title" value=""></div>
      <div class="field"><label for="m_lede">Intro <span class="sub">the line under the title</span></label>
        <textarea id="m_lede" rows="2"></textarea></div>
      <div class="field two">
        <div><label for="m_nav">Menu label</label><input id="m_nav"></div>
        <div><label for="m_order">Menu order</label><input id="m_order" type="number"></div>
      </div>
      <div class="field"><label for="m_description">Search description</label>
        <textarea id="m_description" rows="2"></textarea></div>
    </section>"""


def doc_html(kind, slug):
    data = read_doc(kind, slug)
    label = "post" if kind == "post" else "page"
    return page("Edit %s" % label, """
%s
<main class="wrap split">
  <div class="col-form">
    <div class="head"><h1 id="ptitle">Edit %s</h1>
      <p class="mono" id="pfile"></p></div>
%s""" % (topbar("posts" if kind == "post" else "pages"), label,
         POST_DETAILS if kind == "post" else PAGE_DETAILS) + """

    <section class="group">
      <h2>Body</h2>
      <p class="note">Use the plus button for headings, lists, quotes, code,
        tables, images and YouTube. Select text for bold, italic and links.</p>
      <div id="editor"></div>
    </section>

    <section class="group" id="assetgroup" hidden>
      <h2>Downloads</h2>
      <p class="note">These come from the release. Changing them here changes
        what the download rows on the front page point at.</p>
      <div id="assets"></div>
    </section>
  </div>
  <aside class="col-preview">
    <div class="preview-bar"><span>Preview</span><button class="ghost" id="refresh">Refresh</button></div>
    <iframe id="preview" src="%s?admin=1"></iframe>
  </aside>
</main>
<div class="savebar"><span id="status"></span><button id="save">Save and rebuild</button></div>
""" % data["url"], """
<script src="/admin/vendor/editorjs.js"></script>
<script src="/admin/vendor/header.js"></script>
<script src="/admin/vendor/list.js"></script>
<script src="/admin/vendor/quote.js"></script>
<script src="/admin/vendor/code.js"></script>
<script src="/admin/vendor/delimiter.js"></script>
<script src="/admin/vendor/table.js"></script>
<script src="/admin/vendor/image.js"></script>
<script src="/admin/vendor/embed.js"></script>
<script src="/admin/vendor/inline-code.js"></script>
<script src="/admin/vendor/marker.js"></script>
<script src="/admin/vendor/raw.js"></script>
<script>window.DOC = %s;</script>
<script src="/admin/static/post.js"></script>"""
                % json.dumps({"kind": kind, "slug": slug}))


def post_html(slug):
    return doc_html("post", slug)


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    # ---- helpers
    def _send(self, code, body, ctype="text/html; charset=utf-8"):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self._no_store_sent = True
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj), "application/json; charset=utf-8")

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n) if n else b""

    def _static(self, base, rest, ctype_map):
        safe = posixpath.normpath("/" + rest).lstrip("/")
        path = os.path.join(base, safe.replace("/", os.sep))
        if not os.path.abspath(path).startswith(os.path.abspath(base)) \
                or not os.path.isfile(path):
            return self._send(404, "not found", "text/plain")
        ext = os.path.splitext(path)[1]
        with open(path, "rb") as fh:
            self._send(200, fh.read(), ctype_map.get(ext, "application/octet-stream"))

    # ---- routing
    def do_GET(self):
        p = urllib.parse.urlparse(self.path).path

        if p == "/admin" or p == "/admin/":
            return self._send(200, dashboard_html())
        if p == "/admin/site":
            return self._send(200, site_html())
        if p in ("/admin/pages", "/admin/pages/"):
            return self._send(200, pages_html())
        for kind in ("post", "page"):
            prefix = "/admin/%s/" % kind
            if p.startswith(prefix):
                try:
                    return self._send(200, doc_html(kind, p[len(prefix):].strip("/")))
                except (OSError, ValueError, KeyError):
                    return self._send(404, "no such %s" % kind, "text/plain")
        if p.startswith("/admin/static/"):
            return self._static(EDITOR_DIR, p[len("/admin/static/"):],
                                {".css": "text/css; charset=utf-8",
                                 ".js": "application/javascript; charset=utf-8"})
        if p.startswith("/admin/vendor/"):
            return self._static(os.path.join(EDITOR_DIR, "vendor"),
                                p[len("/admin/vendor/"):],
                                {".js": "application/javascript; charset=utf-8"})
        if p == "/admin/api/posts":
            return self._json(list_posts())
        for kind in ("post", "page"):
            prefix = "/admin/api/%s/" % kind
            if p.startswith(prefix):
                try:
                    return self._json(read_doc(kind, p[len(prefix):].strip("/")))
                except (OSError, ValueError, KeyError):
                    return self._json({"error": "no such %s" % kind}, 404)

        return super().do_GET()

    def do_POST(self):
        p = urllib.parse.urlparse(self.path).path
        try:
            if p == "/admin/api/site":
                payload = json.loads(self._body() or b"{}")
                text = open(SITE_YAML, encoding="utf-8").read()
                new = yamledit.set_values(text, payload.get("updates") or {})
                build.parse_yaml(new)          # refuse to save something unreadable
                atomic_write(SITE_YAML, new)
                return self._json({"ok": True, "ms": rebuild()})

            for kind in ("post", "page"):
                prefix = "/admin/api/%s/" % kind
                if p.startswith(prefix):
                    slug = p[len(prefix):].strip("/")
                    payload = json.loads(self._body() or b"{}")
                    write_doc(kind, slug, payload.get("meta") or {},
                              payload.get("blocks") or [])
                    return self._json({"ok": True, "ms": rebuild()})

            if p == "/admin/api/upload":
                return self._upload()

            if p == "/admin/api/build":
                return self._json({"ok": True, "ms": rebuild()})
        except Exception as exc:
            return self._json({"error": "%s: %s" % (type(exc).__name__, exc)}, 500)

        self._send(404, "not found", "text/plain")

    def _upload(self):
        name = self.headers.get("X-Filename") or "upload.bin"
        name = re.sub(r"[^A-Za-z0-9._-]", "-", os.path.basename(name)).strip("-.") or "file"
        if not os.path.isdir(MEDIA_DIR):
            os.makedirs(MEDIA_DIR)
        stem, ext = os.path.splitext(name)
        if ext.lower() not in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif"):
            return self._json({"success": 0, "error": "unsupported image type"}, 400)
        target = os.path.join(MEDIA_DIR, name)
        n = 2
        while os.path.exists(target):
            target = os.path.join(MEDIA_DIR, "%s-%d%s" % (stem, n, ext))
            n += 1
        with open(target, "wb") as fh:
            fh.write(self._body())
        url = "/assets/media/" + os.path.basename(target)
        return self._json({"success": 1, "file": {"url": url}})

    _no_store_sent = False

    def end_headers(self):
        if not self._no_store_sent:
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        code = str(args[1]) if len(args) > 1 else ""
        if not (code.startswith("2") or code.startswith("3")):
            sys.stderr.write("  %s %s\n" % (code, args[0] if args else ""))


class Server(socketserver.ThreadingTCPServer):
    # On Windows SO_REUSEADDR lets a second process bind a port that is already
    # listening, and the stale server keeps answering. Refuse instead, so a
    # forgotten server is reported rather than silently shadowing this one.
    allow_reuse_address = os.name != "nt"
    daemon_threads = True


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-p", "--port", type=int, default=8000)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()

    print("initial build")
    rebuild()
    try:
        httpd = Server((args.host, args.port), functools.partial(Handler))
    except OSError as exc:
        sys.exit("cannot bind %s:%d (%s)\nAnother server is probably still "
                 "running on that port." % (args.host, args.port, exc))
    with httpd:
        base = "http://%s:%d" % (args.host, args.port)
        print("\neditor   %s/admin/" % base)
        print("site     %s/\n" % base)
        print("ctrl+c to stop.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")


if __name__ == "__main__":
    main()
