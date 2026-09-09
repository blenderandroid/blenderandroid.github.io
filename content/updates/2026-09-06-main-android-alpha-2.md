---
title: The port stopped building its own dependencies
track: main
tag: android-alpha-2
date: 2026-09-06
release_url: https://github.com/simfeo/blender/releases/tag/android-alpha-2
summary: >
  It now takes the prebuilt Android library set published by the Blender project. That single change is what brought back video, Cycles denoising, simulation, the exchange formats, 49 languages and every missing brush.
assets:
  - name: blender-full.apk
    label: Full
    bytes: 284964004
    url: https://github.com/simfeo/blender/releases/download/android-alpha-2/blender-full.apk
    sha256: 
    downloads: 14
  - name: blender-lite.apk
    label: Lite
    bytes: 202154763
    url: https://github.com/simfeo/blender/releases/download/android-alpha-2/blender-lite.apk
    sha256: 
    downloads: 8
---

# Blender 5.3.0 Alpha for Android

Unofficial, experimental build. Android 12 or newer, arm64 only.

Signed with the same key as the previous release, so it installs over it as an
update. No need to uninstall first, and preferences are kept.

## Two builds

- **blender-full.apk** (272 MB) - everything: Cycles, USD, OpenVDB, Alembic,
  MaterialX, LLVM, video, simulation.
- **blender-lite.apk** (193 MB) - modelling, sculpting and animation with
  EEVEE and Workbench. For weaker devices, and for work where the path tracer
  and the exchange formats are not needed.

Both carry the same interface, add-ons, touch handling, languages and brushes.

The lite build leaves out Cycles and its denoising, video (ffmpeg), USD,
Alembic, OpenVDB, MaterialX, LLVM, fluid and smoke simulation, the Ocean
modifier, motion tracking, the exact and manifold boolean solvers, Draco
compressed glTF and PDF export. Everything listed under "New since the previous
release" below applies to the full build; the lite build gets the interface,
touch, content and stability changes but not the new rendering and simulation
features.

## New since the previous release

### How it is built

The port no longer builds its own dependencies. It takes the prebuilt Android
library set published by the Blender project, the same way every other platform
consumes its `lib/<platform>` set. That single change is what made most of the
rendering and format support below possible, and it is why the two lists are as
long as they are.

For anyone building from source, the procedure is different from the previous
release. There is no dependency build step any more, only a submodule to fetch,
and NDK r30 or newer is required rather than merely preferred: the archives are
built with clang 21 and reference a libc++ internal that older NDKs do not
provide, which can produce an APK that installs and then dies at startup.

### Rendering and simulation

- **Video is back.** ffmpeg is linked in again, so video strips, movie textures
  and rendering to a video file all work.
- **Cycles denoising** with OpenImageDenoise, so renders come out clean instead
  of grainy.
- **Fluid and smoke simulation** (Mantaflow), and the **Ocean modifier**.
- **Path guiding** for Cycles.
- **Exact and manifold boolean solvers**, so cutting shapes no longer leaves
  holes.
- **Motion tracking**.
- **Draco compressed glTF**, which is what most .glb files use.
- **PDF export** from Grease Pencil.

### Content that was missing

- **Brushes and assets.** The essentials asset library now ships in the APK.
  Without it there was not a single brush in sculpt, texture paint, vertex
  paint, weight paint, grease pencil or curves, and the bundled node groups
  were absent.
- **49 interface languages.**
- **Online extensions.** The Get Extensions panel lists and installs add-ons
  from extensions.blender.org. **pip** is included, so add-ons can install
  their own Python packages.
- **LoopTools** ships in the build.
- **USD import and export** register correctly.

### Touch and stylus

- Drag anywhere on a panel, header or tool bar with one finger to scroll it. A
  tap still presses the button under your finger.
- Three fingers pan the 3D view. Two fingers orbit and pinch to zoom.
- **Stylus pressure reaches 100% with a normal press.** Android reports
  pressure against a range no hand can reach, so a pen stroke used to come out
  weaker than a finger no matter how hard you pressed.
- On-screen keyboard, with a button in the status bar to summon it.
- **The screen follows the tablet between both landscape orientations.** It used
  to be pinned to one, so turning the device around left the interface upside
  down. Portrait is still not offered.

### Interface

- Interface scale and editor borders start larger, sized for a tablet rather
  than a monitor.
- Renders, the file browser and the preferences open as a maximized area. A
  single window is all the platform provides, so "New Window" could not work
  and rendering previously failed to open anything at all.
- A splash screen while the runtime unpacks, instead of a white window.

### Stability

- **Large scenes no longer close the app without warning.** Texture size is
  capped by default; a scene with a dozen 4K maps used to exhaust the graphics
  memory and be killed by the system with nothing in the log.
- **Auto-save works, so there is crash recovery.** Blender had no usable
  temporary directory on Android and fell back to one that does not exist there,
  so every auto-save was written into nothing. After an unexpected close, use
  File then Recover then Auto Save.
- GPU subdivision falls back to the CPU when the driver refuses it.
- Workarounds for Adreno drivers that reject valid compute pipelines and
  pipeline libraries.

## Known issues

- **The first launch after installing takes a while** and shows only the splash
  screen. Around 100 MB of runtime data is unpacked, once per install.
- **The Online Essentials asset library does not work.** It downloads through a
  separate process, and Android has no working named semaphores, so Python
  cannot build the module it needs. The bundled essentials, which is where the
  brushes come from, are unaffected.
- **The app can stop responding during heavy work**, such as opening a large
  scene for the first time, and Android may offer to close it. Waiting is
  usually enough. It is caused by shader compilation blocking the frame, not by
  a hang.
- **A heavy scene can be closed by the system without warning.** Android reclaims
  memory from the foreground app when the device runs short, and Blender then
  disappears with no message. Recover through File then Recover then Auto Save.
  Recover Last Session is not the one to reach for: it reads a file written only
  on a clean exit, so after an unexpected close it returns an older state.
- **No portrait.** The screen turns between the two landscape orientations, but
  portrait is not offered. This is deliberate.
- Reading and writing .blend files outside the app needs the "All files access"
  permission, which is requested on first launch.

## Tested on

Galaxy Tab S7 FE (SM-T733, Adreno 642L, Vulkan 1.1) and Galaxy S24 Ultra
(Adreno 750, Vulkan 1.3).

Other arm64 devices with Vulkan 1.1 or newer should work. Mobile GPU drivers
vary a great deal, so a device that fails is interesting rather than surprising.

## Another build worth knowing about

Wanderson Magalhaes maintains a parallel Android build, developed on a Galaxy
S24 Ultra: https://github.com/Wanderson-Magalhaes/blender_for_android

**If you have an S24 Ultra, or another device with an Adreno 750, prefer his
build.** He found and worked around driver problems specific to that GPU which
this build does not carry: it refuses several compute pipelines that are
perfectly valid, and without those workarounds the app comes up to a grey
screen.

His build also **works in portrait**. This one turns between the two landscape
orientations only, and that is a deliberate choice here rather than something
unfinished, so if you want portrait, his is the one to use.

Several improvements in this release came from his work, adapted here: the
on-screen keyboard, the Vulkan changes he made for the Adreno 750 in the S24
Ultra, the stylus pressure calibration, the interface defaults for a touch
device, the texture size cap that stops large scenes being killed, and the
approach to packaging the essentials assets, translations and the Python
interpreter. Thanks to him for the debugging and for publishing what he found.

## Source

Built from the `android` branch. It is GPL, like Blender itself, and the
matching source is in the repository this release comes from. The prebuilt
dependency set is a submodule of that branch, and its address now points at the
repository's current home, so a fresh clone can fetch it over HTTPS without a
Blender account.

This is not an official Blender build and is not supported by the Blender
Foundation. If you would like an official Android version to exist, supporting
Blender development is the way to help: https://fund.blender.org/

