# PAPAMAMA CAR'S — FIELDSTYLE 2026 LP1

LP1 only (Next.js App Router + TypeScript). The supplied design images are the page itself. They're displayed at their native aspect ratio, max 509px wide and centred on wider screens. On top of them sit only:

- transparent, keyboard-focusable `<a>` hotspots over the CTAs already drawn in the design, and
- a working STAFF carousel built from the original staff card PNGs.

## Routes

| URL | Content |
| --- | --- |
| `/` | LP1 (production page), FV1 |
| `/lp1` | Alias of `/` |
| `/?fv=1` | FV1 (same as no query) |
| `/?fv=2` | FV2. Only the FV image changes; body, CTAs and slider are identical |
| `/?fv=<anything else>` | Falls back to FV1 |

The FV is chosen on the server (`app/page.tsx`), so there's no FV1→FV2 flash.

## Local development

```bash
npm install
npm run dev            # http://localhost:3000
npm run build && npm start
npx tsc --noEmit
```

## Assets (`public/design/`)

Every asset comes from the client's Google Drive folder `FIELDSTYLE` (`LP1/` and `FIELDSTYLE_LP1-LP2共通`). `scripts/prepare_assets.py` rebuilds them reproducibly. Hashes and sizes are listed in `asset-manifest.generated.json`.

| File | Source | Processing |
| --- | --- | --- |
| `lp1-fv-1.jpg` (594×1544) | `LP1/FIELDSTYLE_FV_LP1-1.jpg` | byte-for-byte copy |
| `lp1-fv-2.jpg` (596×1554) | `LP1/FIELDSTYLE_FV_LP1-2.jpg` | byte-for-byte copy |
| `lp1-body.png` (509×13136) | `LP1/FIELDSTYLE_LP1_2026.jpg` rows y ≥ 1118 | lossless crop (decoded pixels → PNG) |
| `staff-all.png` (3830×816) | `FIELDSTYLE_LP1-LP2共通` | byte-for-byte copy |
| `staff/staff-01..06.png` (586×816) | cut from `staff-all.png` at x = 0, 644, 1294, 1944, 2594, 3244 | lossless crop |
| `staff-stage-bg.png` (509×660) | full design rows 9180–9840 | original pixels; only the static staff cards and the 5 static dots are replaced with the sampled flat green `rgb(104,145,41)` |
| `staff-stage-overlay.png` (509×660) | same rows | original branch / leaf pixels (and the design's 1px right-edge line) with alpha. Drawn above the cards so their strings hang behind the branch as in the design |
| `reference/lp1-full.jpg` | `LP1/FIELDSTYLE_LP1_2026.jpg` | reference only (its FV is the old version) |

The FV and body are scaled to the same display width, so they join with no gap. Hotspots and the slider are positioned relative to the body wrapper, so changing the FV never moves them.

### Note on the input files

The brief referred to `asset-manifest.json`, `cta-coordinate-hints.json`, `lp1-body.png` and pre-cut staff cards. None of these were in the repository, which was empty. All assets were therefore derived from the Drive originals above (same source files, lossless processing). CTA coordinates were measured directly from the design, not taken from hints. Measurement results are in `data/lp1Layout.ts`, and the asset hashes are in `asset-manifest.generated.json`.

Source observations, reproduced as-is: card 3 (後藤 朱里) has an empty 一言 row, and card 6 (松浦 加奈) has no 特技 row.

## Google Tag Manager

`app/layout.tsx` embeds container `GTM-KPB2C8K` using the supplied snippet unchanged:

- the `<script>` sits inside `<head>`;
- the `<noscript><iframe>` is the first element at the start of `<body>`.

It applies to every route (`/`, `/lp1`, `?fv=2`). React 19 always puts Next.js's own resource tags first in `<head>` (charset, viewport, CSS, async chunks, title/meta). The GTM script therefore follows them, which is the highest position available for an inline script in the App Router. A Next.js internal `<div hidden>` also renders at the start of `<body>`, ahead of the `<noscript>`.

## CTA hotspots (`data/lp1Layout.ts`)

The rectangles below are in `lp1-body.png` pixels (full-design y − 1118) and include each button's drop shadow. They were detected from the button colours and checked visually.

| id | Design element | Destination |
| --- | --- | --- |
| `top-consultation` | 相談予約 (below FV) | `CONSULTATION_URL` |
| `top-paint` | 塗装体験予約 (below FV) | `PAINT_URL` |
| `whatwecan-explain` | まずは説明を聞く | `CONSULTATION_URL` |
| `whatwecan-consultation` | 相談予約をする | `CONSULTATION_URL` |
| `paint-line` | LINEから予約 (塗装概要 section) | `PAINT_URL` ※ |
| `footer-consultation` | 相談予約 (footer) | `CONSULTATION_URL` |
| `footer-paint` | 塗装体験予約 (footer) | `PAINT_URL` |
| `footer-instagram` | Instagram icon (Follow Us) | `INSTAGRAM_URL` |

※ The 「LINEから予約」 button sits directly under 塗装概要 (inside the painting-experience section), so it is mapped to `PAINT_URL`. If it should go to the consultation booking instead, change `href` of `paint-line` in `data/lp1Layout.ts`.

### Links not set (left unlinked on purpose)

- **Facebook icon** (Follow Us): no destination was supplied. It's left as a plain image, and no URL was invented.
- **LINE icon** (Follow Us): no destination was supplied, so it's left unlinked.

## STAFF carousel (`components/StaffSlider.tsx`, `data/staff.ts`)

- Shows 6 staff in order: 森行 啓太 → 飯沼 蒼太郎 → 後藤 朱里 → 高木 流星 → 山田 零音 → 松浦 加奈. Rendered only from `staff-01..06.png`.
- Geometry was measured by template matching the card PNGs against the static design: scale 0.6525 (382×532 display px), card at x=71, y=9206, pitch 421px. The design shows the first card centred with neighbours peeking on both sides. The carousel loops (3 copies; only the middle copy is exposed to assistive tech), so that state is reproduced.
- Input: native touch swipe and trackpad scrolling (CSS scroll-snap), mouse drag, ←/→/Home/End when focused, and pager dots. There is no autoplay.
- ARIA: `aria-roledescription="carousel"/"slide"`, `aria-current` on the active dot, a polite live region (`n / 6：氏名`), and alt text transcribed from each card.
- The static card and its 5 dots in the body image are hidden by `staff-stage-bg.png`. The STAFF heading, branch, leaves and background are untouched.

## Visible differences from the static design (intentional)

1. **Pager: 6 dots instead of 5.** The design has 5 dots, with the 3rd active, but 6 cards were supplied. To make all 6 reachable, the pager has 6 dots with the same size (11px), colours (`rgb(74,112,8)` / white), spacing (31.2px) and vertical position. They're centred on the same axis, so each dot sits half a spacing left/right of the original positions. The 1st dot is active on load, because card 1 is shown.
2. **Neighbour peeks ±2px.** The design's left peek fits a 419px pitch and its right peek fits 423px. A uniform carousel uses 421px, so each peek is 2px off. The centred card itself is pixel-aligned.
3. **Outside the 509px column** (desktop only), the background uses the design's cream `#fefcef`.

## QA

Results: [`qa/QA_REPORT.md`](qa/QA_REPORT.md)

```bash
npm run build && npx next start -p 3000 &
node scripts/verify.mjs        # screenshots + CTA/slider/FV checks → qa/screenshots/
python3 -I scripts/compare.py  # pixel comparison vs. source images → qa/screenshots/compare.json
```

## Deploy to Vercel

1. Push this repository to GitHub.
2. On vercel.com, choose **Add New… → Project** and import the repository. The framework is auto-detected as Next.js. Keep the defaults: build `next build`, output `.next`, Node 20+.
3. Click **Deploy**. `/` and `/lp1` are server-rendered on demand (the `?fv` query is read on the server). Static images are served from `/design/*`.
4. Optional: add the production domain under **Settings → Domains**.

CLI alternative: `npm i -g vercel && vercel` (preview) → `vercel --prod`.
