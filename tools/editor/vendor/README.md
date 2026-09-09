# Vendored editor libraries

These are unmodified production builds of [Editor.js](https://editorjs.io/) and
its official block tools, committed here so the visual editor works with a bare
Python install. No npm, no build step, no network access at edit time.

All files are MIT licensed, copyright CodeX.

| File | Package | Version |
|---|---|---|
| `editorjs.js` | `@editorjs/editorjs` | 2.30.7 |
| `header.js` | `@editorjs/header` | 2.8.7 |
| `list.js` | `@editorjs/list` | 1.10.0 |
| `image.js` | `@editorjs/image` | 2.9.3 |
| `embed.js` | `@editorjs/embed` | 2.7.6 |
| `quote.js` | `@editorjs/quote` | 2.7.2 |
| `code.js` | `@editorjs/code` | 2.9.3 |
| `delimiter.js` | `@editorjs/delimiter` | 1.4.2 |
| `table.js` | `@editorjs/table` | 2.4.1 |
| `inline-code.js` | `@editorjs/inline-code` | 1.5.1 |
| `marker.js` | `@editorjs/marker` | 1.4.0 |
| `raw.js` | `@editorjs/raw` | 2.5.0 |

To update one, fetch its UMD build and keep the filename:

```bash
curl -sSL -o header.js https://cdn.jsdelivr.net/npm/@editorjs/header@2.8.7/dist/header.umd.js
```

Note that `@editorjs/list` 2.x changes its data shape to nested items;
`tools/blocks.py` reads both shapes, but check a round-trip after upgrading.

These files serve only the local editor at `/admin/`. They are never referenced
by the published site.
