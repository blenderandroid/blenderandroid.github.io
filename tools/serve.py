#!/usr/bin/env python3
"""Local preview server with auto-rebuild.

    python tools/serve.py            http://127.0.0.1:8000
    python tools/serve.py -p 8777    another port
    python tools/serve.py --no-build serve what is on disk, never rebuild

Before serving any page it checks whether anything under content/ or assets/,
or build.py itself, is newer than the last build, and regenerates if so. Edit a
markdown file, hit refresh, see it. Responses are sent no-store because a
cached stylesheet during a design pass wastes more time than it saves.
"""

import argparse
import functools
import http.server
import os
import socketserver
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build  # noqa: E402

ROOT = build.ROOT
WATCH_DIRS = [os.path.join(ROOT, "content"), os.path.join(ROOT, "assets")]
WATCH_FILES = [os.path.join(os.path.dirname(os.path.abspath(__file__)), "build.py")]

_lock = threading.Lock()
_last_stamp = [0.0]


def newest_mtime():
    newest = 0.0
    for f in WATCH_FILES:
        try:
            newest = max(newest, os.path.getmtime(f))
        except OSError:
            pass
    for d in WATCH_DIRS:
        for base, _dirs, files in os.walk(d):
            for name in files:
                try:
                    newest = max(newest, os.path.getmtime(os.path.join(base, name)))
                except OSError:
                    pass
    return newest


def rebuild_if_stale():
    with _lock:
        stamp = newest_mtime()
        if stamp <= _last_stamp[0]:
            return False
        started = time.time()
        try:
            build.cmd_build(None)
        except Exception as exc:  # a broken content file must not kill the server
            print("\n  BUILD FAILED: %s\n" % exc)
            _last_stamp[0] = stamp
            return False
        _last_stamp[0] = newest_mtime()
        print("  rebuilt in %.0f ms\n" % ((time.time() - started) * 1000))
        return True


class Handler(http.server.SimpleHTTPRequestHandler):
    auto_build = True

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def do_GET(self):
        if self.auto_build and not os.path.splitext(self.path.split("?")[0])[1]:
            rebuild_if_stale()
        elif self.auto_build and self.path.split("?")[0].endswith((".html", ".css", ".js")):
            rebuild_if_stale()
        return super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, fmt, *args):
        code = str(args[1]) if len(args) > 1 else ""
        if code.startswith("2") or code.startswith("3"):
            return  # only shout about problems
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
    ap.add_argument("--no-build", action="store_true", help="serve what is on disk")
    args = ap.parse_args()

    handler = functools.partial(Handler)
    Handler.auto_build = not args.no_build

    if not args.no_build:
        print("initial build")
        rebuild_if_stale()

    try:
        server = Server((args.host, args.port), handler)
    except OSError as exc:
        sys.exit("cannot bind %s:%d (%s)\nAnother server is probably still "
                 "running on that port." % (args.host, args.port, exc))

    with server as httpd:
        url = "http://%s:%d/" % (args.host, args.port)
        print("serving %s" % ROOT)
        print("  %s" % url)
        print("  %s\n" % (url + "updates/"))
        print("edit content/ or assets/, then refresh. ctrl+c to stop.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nstopped")


if __name__ == "__main__":
    main()
