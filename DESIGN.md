---
name: Blender on Android
description: A GPU field rendering in the dark, with hairline chrome and monospace data laid over it.
colors:
  void: "#0b0d1a"
  ink: "#13162b"
  night: "#1a1d3a"
  lilac: "#6a6cf6"
  mist: "#bfd2ff"
  ember: "#ff6a3d"
  display-ink: "#eef3ff"
  heading-ink: "#eaf0ff"
  text: "#dfe8ff"
  text-dim: "#8f9dc4"
  text-faint: "#7d89b2"
  rule: "#242844"
  rule-soft: "#1b1f38"
typography:
  display:
    fontFamily: "Archivo, Archivo Narrow, system-ui, sans-serif"
    fontSize: "clamp(3.4rem, min(13.5vw, 18vh), 11.5rem)"
    fontWeight: 800
    lineHeight: 0.85
    letterSpacing: "-0.035em"
  heading:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "clamp(2rem, 5.2vw, 4rem)"
    fontWeight: 700
    lineHeight: 0.95
    letterSpacing: "-0.03em"
  body:
    fontFamily: "Archivo, system-ui, sans-serif"
    fontSize: "17px"
    fontWeight: 400
    lineHeight: 1.65
    letterSpacing: "normal"
  data:
    fontFamily: "Martian Mono, ui-monospace, Cascadia Mono, Consolas, monospace"
    fontSize: "15px"
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "0.05em"
  label:
    fontFamily: "Martian Mono, ui-monospace, monospace"
    fontSize: "11px"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "0.22em"
rounded:
  none: "0"
spacing:
  xs: "6px"
  sm: "12px"
  md: "24px"
  lg: "48px"
  section: "clamp(72px, 11vh, 148px)"
  gutter: "clamp(20px, 4.5vw, 64px)"
components:
  button:
    backgroundColor: "transparent"
    textColor: "{colors.text}"
    rounded: "{rounded.none}"
    padding: "15px 22px"
    typography: "{typography.label}"
  button-primary:
    backgroundColor: "transparent"
    textColor: "{colors.ember}"
    rounded: "{rounded.none}"
    padding: "15px 22px"
    typography: "{typography.label}"
  button-primary-hover:
    backgroundColor: "{colors.ember}"
    textColor: "{colors.void}"
    rounded: "{rounded.none}"
    padding: "15px 22px"
  panel:
    backgroundColor: "{colors.void}"
    textColor: "{colors.text-dim}"
    rounded: "{rounded.none}"
    padding: "clamp(26px, 3vw, 42px)"
  panel-hover:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.text-dim}"
  checkbox-checked:
    backgroundColor: "{colors.ember}"
    textColor: "{colors.void}"
    rounded: "{rounded.none}"
    size: "22px"
---

# Design System: Blender on Android

## Overview

**The Night Render.** The page is a frame being drawn in the dark: a live GPU
field resolving behind hairline chrome, with the facts laid over it in
monospace. The metaphor is not decoration. This site exists because a Vulkan
renderer now runs on a phone, so the surface proves that claim by being a
rendered thing rather than describing one.

The mood is precise, nocturnal and unhurried. It is a technical document with a
light source. Every warm pixel is spent on one job, and the rest of the surface
stays cold and quiet so that job reads.

Anti-reference: the promotional-poster look this project has used elsewhere,
with starburst badges, four competing typefaces and drop-shadowed all-caps. It
works in a social feed and actively undermines a page asking someone to trust a
272 MB unsigned sideload. The second anti-reference is the generic dark
open-source landing page: centered headline, screenshot, feature grid.

## Colors

Dark is chosen from the use scene, not from category habit: visitors read this
on the phone they are about to install on, often at night, usually inside
Blender's own dark world already.

| Token | Value | Character | Role |
|---|---|---|---|
| `void` | `#0b0d1a` | Near-black, faintly blue | The page ground. Everything sits on it. |
| `ink` | `#13162b` | Lifted midnight | Hover ground, code blocks, quiet panels. |
| `night` | `#1a1d3a` | Raised midnight | The active or selected ground. |
| `lilac` | `#6a6cf6` | Cold electric violet | The field's light. Track labels, cool accents. |
| `mist` | `#bfd2ff` | Pale blue-white | Secondary display ink, links, code. |
| `ember` | `#ff6a3d` | Hot signal orange | Reserved. See below. |
| `display-ink` | `#eef3ff` | Coldest white | The hero display line only. |
| `heading-ink` | `#eaf0ff` | Near-white | Section and page headings. |

**Ember is reserved and must stay reserved.** It marks downloads, live state,
and warnings, and nothing else. Its authority comes entirely from scarcity: the
moment it decorates something, the download button stops being the brightest
thing on the page. It doubles as the nod to Blender's own orange without
borrowing Blender's identity.

Text tints are drawn from the ground's own hue rather than gray. All pairs meet
WCAG AA on `void`: `text` 15.8:1, `text-dim` 7.2:1, `text-faint` 5.6:1,
`ember` 6.8:1, and `void` on `ember` 6.8:1 for the button hover.

## Typography

Two families, each with a job. **Archivo** (variable, width 62 to 125) carries
display and body. Display is set condensed and heavy, width 74 to 84, at
viewport scale. **Martian Mono** sets every label, version, size, tag and
checksum.

Monospace here is not a costume for "technical". It is used only for data and
measurement: a SHA-256, a byte size, a version tag, a nav label. Prose never
takes it.

Condensed widths close up word spaces, so display and headings carry explicit
`word-spacing` between `0.08em` and `0.10em`. Without it, `WILL IT RUN` collides.

**Long prose is never set in tracked uppercase.** Labels of a few words may be;
sentences may not. The non-affiliation line learned this the hard way and is now
sentence case, in the display face, at reading size.

## Layout

Content maxes at `1440px` inside a fluid gutter of `clamp(20px, 4.5vw, 64px)`.
Sections are separated by `clamp(72px, 11vh, 148px)` and a single hairline.
Prose measures at `70ch`.

The hero is bottom-aligned in `100svh` so the field occupies the space above the
type. Its display size is capped by viewport height as well as width
(`min(13.5vw, 18vh)`), because a short landscape phone otherwise pushes the
download action below the fold.

Breakpoints: `520px` (phone chrome), `720px` (feed and post nav collapse),
`900px` (the hero index leaves the margin), `1040px` (the chrome disclaimer tail
appears).

## Elevation & Depth

**There are no shadows and no radii anywhere in this system.** Both counts are
zero in the stylesheet, and that is normative, not an oversight.

Depth is expressed two ways only:

1. **Ground value.** `void` recedes, `ink` is hover, `night` is active.
2. **Hairlines.** Exactly `1px`, in `rule` or `rule-soft`. Grid containers get
   their dividers from a `1px` gap showing the container's own background
   through, not from per-child borders.

The one blurred surface is the fixed chrome bar, which uses `backdrop-filter` so
the field reads continuously beneath it. That is a specific effect, not a
decorative glass treatment.

## Shapes

Everything is a rectangle. Buttons, panels, checkboxes, code blocks, tables and
the checklist boxes are all square-cornered. The only curves on the page come
from the shader field and from icon strokes.

Icons are authored SVG on a `24` viewBox at `1.5` to `1.8` stroke weight,
round caps and joins. No icon font, no emoji, no unicode glyphs standing in.

## Components

Component feel: **hairline and unshadowed**. Every edge is one pixel, nothing is
rounded, and lift is a change of ground rather than a shadow.

- **Buttons** are hairline rectangles that fill from the bottom on hover via a
  `scaleY` pseudo-element, flipping the label to `void`. The primary variant is
  ember-outlined at rest. Focus-visible shares the hover treatment, so keyboard
  and pointer states never diverge.
- **The device checklist** is pure CSS. Real checkboxes drive `:has()` on the
  section; there is no JavaScript. Checked state changes the ground, fills the
  box with ember, and reveals a drawn tick, so state survives being read in
  sunlight rather than depending on hue alone.
- **Panels and file rows** carry no border of their own. They sit in a grid
  whose `1px` gap shows the container background as a rule.
- **Browser surfaces are themed**, not left to the browser: selection, caret,
  scrollbar track and thumb, and focus rings all come from the palette.

## Do's and Don'ts

**Do**

- Keep ember for downloads, live state and warnings only.
- Set data in Martian Mono and prose in Archivo.
- Express depth with ground value and 1px rules.
- Give condensed display type explicit word-spacing.
- Make every piece of content work with JavaScript disabled; the shader and the
  scroll reveal are enhancements layered over a page that already renders.
- Keep the unofficial, non-affiliated status visible in the chrome, the hero
  and the footer.

**Don't**

- Add a border-radius or a box-shadow. Both are zero by decision.
- Use card shells with an icon, a heading and three lines as page structure.
- Put long prose in tracked uppercase or in monospace.
- Hide content behind an entrance animation. Content is visible by default and
  the reveal is layered on only after JavaScript confirms it can undo it.
- Use the official Blender logo as the site's mark, or frame the site as
  blender.org. It is a community port and must never read as an official
  Blender Foundation property.
- Invent a checksum, a device claim, or a screenshot of the app. Where a fact
  is not published, the page says so.
