---
title: It runs, and it renders
track: main
tag: android-alpha-1
date: 2026-08-07
release_url: https://github.com/simfeo/blender/releases/tag/android-alpha-1
summary: >
  The first public build. Blender 5.3.0 Alpha on arm64 with a Vulkan driver, in two profiles, with S Pen support. On a Galaxy S22 Ultra the Full build peaked at about 1.9 GB resident.
assets:
  - name: blender-full.apk
    label: Full
    bytes: 174096015
    url: https://github.com/simfeo/blender/releases/download/android-alpha-1/blender-full.apk
    sha256: 5afb85ec19ce4caa3d1ebba5f291ae707f0fcaf6c976338db71df35b95b91e96
    downloads: 699
  - name: blender-lite.apk
    label: Lite
    bytes: 120972559
    url: https://github.com/simfeo/blender/releases/download/android-alpha-1/blender-lite.apk
    sha256: c2d6009fb79ca8336e515f64e89a6ad2a232d0f2813c09e2b0561dff1d1f7490
    downloads: 466
---

Blender 5.3.0 Alpha built for Android, as an unofficial port. Not affiliated with or endorsed by the Blender Foundation. The build supports Samsung S Pen

This is an **alpha**. It runs, it renders, and it will have rough edges.

## Which build?

| | `blender-lite.apk` | `blender-full.apk` |
|---|---|---|
| Size | 115 MB | 166 MB |
| Modeling, sculpting, UV | yes | yes |
| Eevee / Workbench viewport | yes | yes |
| Python, add-ons | yes | yes |
| **Cycles** path tracer | no | yes |
| **Video** (FFmpeg) | no | yes |
| **USD / Alembic / OpenVDB / MaterialX** | no | yes |
| LLVM | no | yes |

**Start with `lite`** unless you specifically need Cycles or the exchange formats. It is the one to use on mid-range hardware — less to load, less memory, fewer ways to run out of it.

`full` is for flagship devices. On a Galaxy S22 Ultra it peaked at about 1.9 GB resident.

## Requirements

- **arm64** device with a **Vulkan** driver (there is no OpenGL fallback)
- Android 12 (API 31) or newer
- Enough free RAM: roughly 400 MB on a mid-range tablet, up to ~2 GB on a high-end phone, since the port scales its memory pools to the device

Both builds have been run through a viewport shading stress test on:

- **Samsung Galaxy Tab S7 FE** (Adreno 642L, Vulkan 1.1) — lite
- **Samsung Galaxy S22 Ultra** (SM-S908B, Exynos 2200 / Xclipse 920, Vulkan 1.3) — lite and full

## Installing

These are not from Google Play, so Android will ask you to allow installation from an unknown source. The APKs are signed by the author; you can check the certificate matches this fingerprint:

```
SHA-256: f8b590dac5a14b530936d8b68be05a77e60bb0a2e652d9d8d079d9c93cc0cc3b
```

File checksums:

```
c2d6009fb79ca8336e515f64e89a6ad2a232d0f2813c09e2b0561dff1d1f7490  blender-lite.apk
5afb85ec19ce4caa3d1ebba5f291ae707f0fcaf6c976338db71df35b95b91e96  blender-full.apk
```

## Known limitations

- **Touch and stylus only** — the UI is Blender's desktop UI. A keyboard and mouse help a great deal. S Pen is supported, including hover and the side button.
- **No OpenGL backend.** A device without Vulkan will not start.
- Devices without `VK_KHR_dynamic_rendering` (older Adreno, e.g. the Tab S7 FE) use an emulated render-pass path. It is correct, but slower than on hardware with dynamic rendering.
- Mesa **Turnip** builds are deliberately not included. Turnip loads and renders, but only with tiled rendering disabled, which costs roughly 2.4x peak memory and still faults the GPU in Rendered shading mode.

## Source

Built from commit `7293a1d174f` in this repository, which is what this tag points at. Blender is licensed GPL-2.0-or-later; the corresponding source for these binaries is the tagged tree.

