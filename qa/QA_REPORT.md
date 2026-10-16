# LP1 QA report

> **2026-10-16 SNS links (on request).** Both open in a new tab (`rel="noopener noreferrer"`). All checks pass with 9 hotspots at 509/390/375 px, FV1 and FV2: exact `href`, and each is the top element at its centre.
> - **Instagram icon:** now links to https://www.instagram.com/papamamacars/ (previously the LMES link `…uLand=pxS26L`).
> - **Facebook icon:** new hotspot to https://www.facebook.com/papamamacars/?locale=ja_JP, placed over the drawn icon (body rect 218,12970,76,76).
> - **LINE icon:** still unlinked, because no destination was supplied.

> **2026-10-14 FV1 present block resized (on request).** `lp1-fv-1.jpg` is now 522×1700, made by `scripts/edit_fv1_present.py` from `reference/lp1-fv-1-original.jpg`.
> - **Block:** gift / ribbon / PRESENT cards scaled to 80% and centred.
> - **Gaps:** date→block 86→40px, block→FV bottom 125→44px.
> - **Background:** rebuilt from the original's own gradient and paper texture. Rows above the block are unchanged apart from JPEG re-encoding (mean 1.05/255).
> - **@2x:** the same edit applied to the upscaled original (1044×3400, exactly 2×).
> - **Bug fixed during review:** a dark blotch in the @2x background next to card 01. The gradient estimate is now computed at 1x for both versions.
> - **QA:** all functional checks pass; DPR 3 loads 34/34 @2x; at 509px the body is still pixel-identical and identical between FV1 and FV2.
> - **Body untouched:** the yellow band above the body's top buttons (100px, part of the original body design) is unchanged.

> **2026-10-14 FV1 swap.** `lp1-fv-1.jpg` ← `FIELDSTYLE_FV_LP1-1-1.jpg` (522×1952, byte-for-byte), which adds the 予約者全員にプレゼント block. FV2 is unchanged. All functional checks pass. FV1 vs source at 509px: mean 1.93 (resampling only). Body at 509px is still pixel-identical, and FV1/FV2 bodies are identical. FV1 is served 1x-only until its @2x upscale is added; the other 33 images are @2x on DPR 3. The source again has a 1px light bottom row, kept as-is.

> **High-DPI (@2x) enabled.** Every image now has a Real-ESRGAN x2plus @2x version chosen by `srcset`.
> - **DPR 1:** loads 0 @2x files (34/34 originals), so the pixel results below are unchanged.
> - **DPR 3** (390px viewport): loads 34/34 @2x files.
> - **Tile seams:** tiles are feather-blended. In the body @2x, row-to-row change at tile edges averages 2.75 vs 2.99 mid-tile (the earlier hard-cut version measured 3.88 vs 3.37, with visibly broken button shadows), so no seams.
> - **Visual check:** at 3× (FV lettering, CTA buttons, staff card, store-info text) the text is sharper with no glyph distortion. Before/after: `qa/preview/hidpi-before-after-3x.png` (local).

> **2026-10-13 FV swap.** FV1/FV2 were replaced with the files now in Drive `LP1/`: `FIELDSTYLE_FV_LP2-1.jpg` (590×1335) and `7 1FIELDSTYLE_FV_LP2-2.jpg` (573×1298). They're byte-for-byte copies. QA was re-run and all functional checks pass. At 509px the body is still pixel-identical to `lp1-body.png`, and FV1 vs FV2 bodies are identical. The new FV1 scales to a fractional height (1151.72px at 509), so its PIL comparison shows edge-only resampling noise (mean ≈3.5), with no structural difference. Both new source files carry a 1px light line: FV1 on its right column, FV2 on its bottom row. That's in the originals and kept as-is.

Environment: `next build` + `next start` (production), headless Chromium 1194 (Playwright), DPR 1.
Reproduce with `node scripts/verify.mjs && python3 -I scripts/compare.py`. Outputs go to `qa/screenshots/` (not committed).

## Functional checks (`scripts/verify.mjs`): all passed

| Check | Widths | Result |
| --- | --- | --- |
| FV and body join with no gap (body top == FV bottom) | 509 / 390 / 375, FV1 & FV2 | OK |
| No horizontal page scroll | same | OK |
| 8 CTA hotspots: `href` matches the supplied URL character for character | same | OK |
| Each hotspot is the top element at its centre (not covered) | same | OK |
| `?fv=2`: CTA geometry, body height and slider initial state identical to FV1 | 509 / 390 / 375 | OK |
| Touch swipe (CDP touchStart/Move/End) ×6 then back: cards 1→2→3→4→5→6→1→6, dot in sync, snap error ≤ 0.51px | 390 | OK |
| Keyboard →×6, ←×1: 1,2,3,4,5,6,1,6 | 509 | OK |
| Dots 6→1 each show their card, `aria-current` in sync | 509 | OK |
| Mouse drag −160, −160, +160 px: 2, 3, 2 | 509 | OK |
| Routes `/`, `/lp1`, `/?fv=2`, `/?fv=abc`, `/lp1?fv=2` | 390 | correct FV, no console errors except `/favicon.ico` 404 (no favicon supplied) |
| Tab order | 390 | CTAs → slider → 6 dots → footer CTAs → Instagram (visual order) |

## Pixel comparison (`scripts/compare.py`)

Values are the per-pixel max channel difference (0–255).

| Area | 509px (native) | 390px | 375px |
| --- | --- | --- | --- |
| Body outside STAFF vs `lp1-body.png` | **0 (identical)** | mean 1.44 (resampling only) | mean 1.47 (resampling only) |
| STAFF stage at rest (excluding pager) vs design | mean 2.9 (FV1) / 3.8 (FV2) | mean 5.7 | mean 4.5 |
| FV vs FV source resized by PIL (browser scales 594→509) | mean 2.3 | mean 8.6 | mean 8.8 |
| Body FV1 vs FV2, outside STAFF | **identical** | max 14 on 28 rows (sub-pixel phase) | max 15 on 30 rows (sub-pixel phase) |
| Desktop 1280px body vs `lp1-body.png` | **0 (identical)**; Chrome snaps the 385.5px offset to 386 | | |

- At 390/375 the browser downscales the images, so both the FV and the body differ from a PIL resample. That is resampling, not layout: there are no shifted bands.
- The FV1/FV2 bodies differ by ≤15 levels at narrow widths only because the two FVs scale to different fractional heights (1013.73px vs 1016.88px at 390), which changes the sub-pixel phase of the body resample.
- The STAFF residual is the scaled card edges (the cards are rendered from 586px sources, while the design was a JPEG), plus the items below.

## Known visual differences (intentional, see README)

1. Pager has **6 dots instead of 5** (rows 9789–9800 of the full design). The design's 5 dots were centred at x 193.2–318.0 with the 3rd active. The new 6 dots, same size/colour/spacing, are at x 177.6–333.6 with the 1st active, because card 1 is shown.
2. Neighbour peeks at the STAFF left/right edges are about **2px** off (design 419/423px pitch → uniform 421px).
3. While a card is moving, its strings can show a 1–2px notch where they meet the branch. At rest the design is reproduced.
4. Chromium's full-page screenshot resets the slider's inner scroll (an artifact of the capture tool, not reachable by users). The STAFF stage is therefore verified from element screenshots.
