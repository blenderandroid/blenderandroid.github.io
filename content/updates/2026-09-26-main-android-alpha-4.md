---
title: Sound, working Cycles lighting, and a Turnip driver for Adreno
track: main
tag: android-alpha-4
date: 2026-09-26
release_url: https://github.com/simfeo/blender/releases/tag/android-alpha-4
summary: >
  Audio through AAudio, Cycles denoising, and Principled BSDF materials that no longer render almost black. Two new Turnip builds carry Mesa's open Adreno driver, and the Wanderson Magalhaes touch and keyboard work is ported in.
assets:
  - name: blender-full-turnip.apk
    label: Full, Turnip
    bytes: 289212314
    url: https://github.com/simfeo/blender/releases/download/android-alpha-4/blender-full-turnip.apk
    sha256: 
    downloads: 0
  - name: blender-full.apk
    label: Full
    bytes: 286561495
    url: https://github.com/simfeo/blender/releases/download/android-alpha-4/blender-full.apk
    sha256: 
    downloads: 0
  - name: blender-lite-turnip.apk
    label: Lite, Turnip
    bytes: 205850330
    url: https://github.com/simfeo/blender/releases/download/android-alpha-4/blender-lite-turnip.apk
    sha256: 
    downloads: 0
  - name: blender-lite.apk
    label: Lite
    bytes: 203199511
    url: https://github.com/simfeo/blender/releases/download/android-alpha-4/blender-lite.apk
    sha256: 
    downloads: 0
---

# Blender for Android: Alpha 4

Based on Blender 5.3 alpha, merged with upstream `main` from late September 2026.

Signed with the same key as the previous release, so it installs over it as an update.

## Highlights

- **Turnip flavours.** New `lite-turnip` and `full-turnip` APKs ship Mesa's open-source Turnip Vulkan driver for Adreno GPUs, loaded through libadrenotools instead of the vendor driver. They're experimental: use them if the regular APK misbehaves on your Adreno device.
- **Sound.** Audio output now uses AAudio, and it follows route changes: plugging in headphones or connecting Bluetooth moves playback to the new device.
- **Cycles denoising works in the full APK.** OpenImageDenoise is now built into the app, so the CPU denoiser can start. On phones it's slow, around 30 seconds per 1080p denoise.
- **Cycles lighting fixed.** Materials using the Principled BSDF rendered almost black. The shader compiler copied node data in a way the Android compiler was allowed to optimize away, so the surface normal was read from garbage.
- **Renders save to `Download/Blender`.** Output aimed at Blender's default `/tmp/` path used to fail on Android. Such paths now go to `Download/Blender`.

## Input and UI

These were ported from Wanderson Magalhaes' build:

- **Virtual keyboard:** function keys, Caps, a navigation pad and latching modifier keys.
- **Tool variants:** long-press a toolbar tool to open its variants.
- **Scrolling:** finger-drag scrolling in search lists and in popups taller than the screen.
- **Opening files:** open `.blend` files and links from other apps, such as a file manager or browser.
- **IME:** composing text from the on-screen keyboard shows inline while you type.
- **Preferences:** now show hardware information.

Also:

- **Adaptive launcher icon:** follows the launcher's icon shape, and supports themed (monochrome) icons on Android 13+.

## Graphics fixes

- **Adreno:** the vendor driver's vertex-input bug workaround now applies on Android. It was Windows-only before, so batches could be drawn repeated across the screen on some Adreno devices.
- **Adreno 830:** fixed a crash or black screen when the swapchain grows beyond five images.
- **Swapchain:** it now uses a composite-alpha mode the device actually supports, which fixes an undefined swapchain on some surfaces.
- **Diagnostics:** the startup log (`Download/blender-startup.log`) now records the Vulkan API version, the device features and workarounds in use, and shader workarounds. Please attach it to bug reports.

## Upstream

- **Upstream merge:** includes upstream Blender's recent Vulkan work: Vulkan 1.1 device support, `shaderDrawParameters` no longer required, and optional clip distance, plus the new BSL shader language and general 5.3 alpha changes.

## Known issues

- **Mali-G57 with driver r32 (and possibly other older Mali drivers):** UI widgets, including the virtual keyboard, and meshes are drawn with stray triangles. This is a regression from Alpha 3, and the cause is still unknown. If you have such a device and can test builds, please get in touch.
- **Moto g stylus 5G (2024), Adreno 710:** the app now starts (Alpha 3 didn't), but the viewport and UI show repeated geometry and noise.
- **Turnip on Adreno 642L:** the GPU can be lost after using EEVEE.

## Downloads

| APK | Contents |
|---|---|
| `blender-lite.apk` | Core Blender, smaller download |
| `blender-full.apk` | Adds Cycles, OpenImageDenoise and the other heavy features |
| `blender-lite-turnip.apk` | Lite, with the Turnip driver for Adreno (experimental) |
| `blender-full-turnip.apk` | Full, with the Turnip driver for Adreno (experimental) |

This is not an official Blender build and is not supported by the Blender Foundation.

