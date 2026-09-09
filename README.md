# blenderandroid.github.io

Static site for the unofficial Blender for Android port. Presents both build
tracks, makes the correct APK easy to download and verify, and publishes the
porting log as readable posts on the site rather than links out to GitHub.

Unofficial. Not affiliated with or endorsed by the Blender Foundation.

## Requirements

Python 3.6 or newer. Nothing else: the generator uses the standard library
only, so there is no `pip install`, no virtualenv and no lockfile to maintain.

## The workflow

Everything starts from a clone. There is no install step.

```bash
git clone https://github.com/blenderandroid/blenderandroid.github.io
cd blenderandroid.github.io
```

### Everything, from the editor

```bash
python tools/edit.py            # open http://127.0.0.1:8000/admin/
```

Then, in the browser:

- **Publishing a release.** Add post, paste the GitHub release URL, Add and
  open. The tag, date, file sizes, download links and any published checksum
  are read from the release, so nothing is retyped. Fix the title and summary,
  edit the body, save.
- **Posting an announcement.** Add post, Announcement tab, give it a title,
  write it, save.
- **Changing wording on the site.** Landing page, edit the fields, save.
- **Removing a post or page.** Hover its row, Delete, confirm.

Then commit and push:

```bash
git add -A && git commit -m "Add alpha 4" && git push
```

Git stays manual on purpose. Editing is local and reversible; publishing to a
public site is not, so a person reads the diff before it goes out.

The release import talks to the GitHub API **once, on your machine, at edit
time**. The published site is plain static HTML and never calls it. Nothing
about a release is written in two places, and download links cannot go stale.

### Which tool

| Tool | Use it for |
|---|---|
| `tools/edit.py` | Everything, day to day. Adding, writing, editing and deleting, with the site served beside it and rebuilt on save. |
| `tools/build.py` | The escape hatch. Regenerating the site headlessly, in CI, or when the editor itself is broken. Also the library the editor runs on. |
| `tools/serve.py` | Previewing without the editor, for example while hand-editing CSS. |

`build.py` is not a competing tool: `edit.py` imports it and calls it on every
save, so there is one generator, not two. Its command line stays because a
system that can only be driven through its own interface has no way back when
that interface is the thing that broke, and because CI has no browser.

`tools/blocks.py` and `tools/yamledit.py` are libraries used by the editor. You
never run them directly.

Only one server can hold a port, so stop one before starting the other.

## Layout

```
content/site.yaml          site-wide facts, hand-edited
content/updates/*.md       one file per release or announcement
content/pages/*.md         standalone pages such as About
assets/site.css            design, hand-authored
assets/field.js            the hero shader, hand-authored
assets/media/              images added through the editor
tools/build.py             the generator
tools/serve.py             local preview with auto-rebuild
tools/edit.py              the visual editor
tools/blocks.py            markdown <-> editor blocks
tools/yamledit.py          surgical edits to site.yaml
tools/editor/              editor front end and vendored Editor.js

index.html                 GENERATED
updates/index.html         GENERATED
updates/<slug>/index.html  GENERATED, one per post
<page>/index.html          GENERATED, one per file in content/pages
```

Generated files are committed, because GitHub Pages serves the repository as-is.
Never hand-edit them: the next build overwrites your changes. Edit `content/`
or `assets/` instead.

## Commands

### `python tools/build.py`

Regenerates the whole site. Also deletes pages for updates whose markdown file
you removed, so the output never drifts from the content.

### `python tools/build.py import <url>`

The command-line form of the editor's Add post. Pulls a GitHub release into
`content/updates/`. Accepts a release URL, or a repository URL to take its
latest release:

```bash
python tools/build.py import https://github.com/simfeo/blender/releases/tag/android-alpha-4
python tools/build.py import https://github.com/simfeo/blender          # latest
```

It captures the tag, publish date, and for each attached file the exact byte
size and the real `browser_download_url`, so download links cannot go stale. It
also tries to find a SHA-256 for each file in the release notes, matching
`sha256sum` output by filename rather than by position. When it finds nothing it
leaves the field empty and says so; the page then tells the reader the checksum
was not published rather than inventing one.

The track is matched automatically from the repository name in `site.yaml`.
Override with `--track`, the title with `--title`, and overwrite an existing
file with `--force`.

Set `GITHUB_TOKEN` in the environment if you hit the anonymous rate limit.

### `python tools/build.py new`

Scaffolds a post by hand, with no network access at all. The editor's Add post
button does the same thing, so reach for this only when scripting.

```bash
# a release, when you would rather not use import
python tools/build.py new --track main --tag android-alpha-4

# an announcement: no release, no tag, no downloads
python tools/build.py new --title "Calling for Mali testers"
```

An announcement is a normal post in the log. It carries no tag chip, shows no
download rows and no link back to GitHub, and gets its own label from the
`kinds:` map in `site.yaml`.

### `python tools/serve.py`

Local preview on `http://127.0.0.1:8000`. Before serving a page it checks
whether anything under `content/` or `assets/`, or `build.py` itself, is newer
than the last build, and regenerates if so. Edit a file, refresh, see it.
Responses are sent `no-store`, so a cached stylesheet never lies to you during a
design pass. A content file with broken frontmatter prints the error and keeps
the server up rather than killing it.

```bash
python tools/serve.py -p 8777     # another port
python tools/serve.py --no-build  # serve what is on disk, never rebuild
```

### `python tools/edit.py`

The visual editor, at `http://127.0.0.1:8000/admin/`. Self-hosted, offline, no
account and no AI. Anyone with Python can run it, edit, and commit.

```bash
python tools/edit.py            # editor at /admin/, site at /
python tools/edit.py -p 8777    # another port
```

It has three areas. Posts and Pages carry a live preview of the real page beside
the form.

| Area | What it does |
|---|---|
| **Posts** | Add from a release URL or as an announcement, edit title, summary, date, tag, body and download rows, delete |
| **Landing page** | Every string on the front page, as a form |
| **Pages** | Add, edit and delete standalone pages such as About |

**Adding a post.** Press Add post. *From a release* takes a GitHub release URL
and fills everything it can read from it. *Announcement* takes only a title.
Either way you land straight in the editor, because a new post always needs
writing. If the release published no checksum, the editor says so at the top
rather than leaving you to notice.

**Deleting.** Hover a row and press Delete. The confirm names the post, and the
markdown file is removed and its page pruned on the next build. Nothing is
pushed, so `git checkout .` brings it back until you commit.

The body uses a block editor: press the plus button for headings, lists,
quotes, code, tables, images and YouTube embeds, or select text for bold,
italic, links, highlight and inline code. Images are uploaded into
`assets/media/` and referenced from there. `Ctrl+S` saves.

Saving writes the markdown back to `content/`, rebuilds the site, and refreshes
the preview. Then you commit and push as usual.

**On the landing page, only text is editable.** Structure, order and design are
deliberately not exposed, so a contributor changing a word cannot break the
layout. Those live in `assets/site.css` and the templates.

Two implementation notes worth knowing if you extend it:

- Markdown stays the source of truth, and the editor converts to blocks and
  back. Anything the block editor cannot represent, such as a nested list or a
  GitHub `> [!WARNING]` alert, is preserved verbatim in a raw block rather than
  dropped. Round-tripping every existing release note produces byte-identical
  rendered output.
- `site.yaml` is patched line by line rather than re-serialised, so comments,
  blank lines and line breaks survive a save untouched.

## Adding a page

Create a markdown file in `content/pages/`. It appears automatically in the
header menu, in the footer, and in the editor.

```yaml
---
title: About
nav: About        # label in the menu
order: 10         # menu position, lower is earlier
lede: One line under the title.
description: Used for search results.
---

The page body, as markdown.
```

It builds to `/<filename>/index.html`, so `about.md` becomes `/about/`.

## Writing an update

Each file in `content/updates/` is frontmatter plus markdown.

```yaml
---
title: Devices with ARM Mali graphics now run
track: main
tag: android-alpha-3
date: 2026-09-07
release_url: https://github.com/simfeo/blender/releases/tag/android-alpha-3
summary: >
  What the feed shows. Two or three sentences.
assets:
  - name: blender-full.apk
    label: Full
    bytes: 284964004
    url: https://github.com/simfeo/blender/releases/download/android-alpha-3/blender-full.apk
    sha256: ""
    downloads: 17
---

The release notes, as markdown.
```

| Field | Meaning |
|---|---|
| `title` | Post title and feed headline. Rewrite what `import` grabbed; GitHub release names make poor headlines. |
| `track` | `main` or `s24`, matching a key under `tracks:` in `site.yaml`. |
| `date` | `YYYY-MM-DD`. Drives ordering and which release counts as newest. |
| `summary` | Feed excerpt. Not generated from the body, so write it. |
| `assets` | One entry per downloadable file. `bytes` is the real size; the page formats it. |
| `sha256` | Leave empty when the release publishes none. The page says so. |

Supported markdown: headings, bold, italic, inline code, links, images, fenced
code blocks, ordered and unordered lists with nesting, tables, blockquotes,
GitHub alerts (`> [!WARNING]`), and horizontal rules. Headings shift down two
levels, because the page already owns its `h1`. If the notes open with a
heading that repeats the title, it is dropped automatically.

A YouTube video is a fenced block, so the markdown stays plain text:

````
```youtube
https://www.youtube.com/watch?v=VIDEO_ID
```
````

It renders as a lazy `youtube-nocookie` iframe, which needs no JavaScript of
its own and sets no cookie until someone presses play.

## What is derived, and what is not

Adding one update file moves all of this without further edits:

- which release is newest per track, and the dates shown on the build cards
- the download rows, their filenames, sizes, checksums and links
- the size range on each build card, and the download totals per track
- feed order, the porting log index, and one page per release

Hand-edited in `site.yaml`: the device requirements, the install steps, the
signing fingerprint, the two track descriptions and their bullet points, and
the section ledes. All of those are editable through `tools/edit.py` as well.

Adding a file to `content/pages/` likewise adds it to the header menu, the
footer and the editor with no further wiring.

## Design notes

Durable design and product context lives in `PRODUCT.md`: who the site is for,
what must never be claimed, and which facts future work has to preserve. It is
committed as project documentation but is not part of the published site. The
landing page's direction contract lives in `.impeccable/`, which is gitignored
along with the rest of the local tooling.

Two constraints worth preserving:

1. **All content works with JavaScript disabled.** The hero shader is
   progressive enhancement over a static gradient; the device checklist is
   pure CSS. Visitors are often on mobile data, on the device they are about
   to install on.
2. **The unofficial status is never softened.** It is in the fixed header, the
   hero, the page description and the footer. The site must never read as an
   official Blender Foundation property.

## Troubleshooting

**"cannot bind 127.0.0.1:8000" or the page looks stale.** A server is already
running on that port, probably from an earlier session. Use another port with
`-p`, or stop the old one. On Windows, find and stop it with:

```bash
netstat -ano | findstr "127.0.0.1:8000"
taskkill /F /PID <the pid from the last column>
```

**A save fails with a parse error.** The editor refuses to write a `site.yaml`
it cannot read back, so the file on disk is untouched and the message names the
problem. Fix the field it points at and save again.

**The editor shows a block of raw markdown.** That is deliberate. Nested lists
and GitHub alerts (`> [!WARNING]`) have no block equivalent, so they are kept
verbatim instead of being mangled. Edit the markdown in place; it is written
back exactly as written.

**GitHub returns 403 on import.** You have hit the anonymous rate limit of 60
requests an hour. Set `GITHUB_TOKEN` in your environment and retry.

**A post disappeared from the site.** Deleting a file from `content/updates/`
deletes its page on the next build, by design. Restore the markdown file and
rebuild.

**Changes do not show in the preview.** The preview pane refreshes on save;
press Refresh above it if you edited files outside the editor.

## Deploying

GitHub Pages serves `main` from the repository root. Commit the generated
`index.html` and `updates/` along with your content change and push. There is
no build step on the server.
