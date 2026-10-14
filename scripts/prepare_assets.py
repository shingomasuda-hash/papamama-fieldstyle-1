"""Derive the LP1 web assets from the original design files (lossless).

Usage: python3 -I scripts/prepare_assets.py <source_dir> <repo_root>

<source_dir> must contain the files downloaded from the FIELDSTYLE Google Drive folder:
  FIELDSTYLE_LP1_2026.jpg      509x14254 full LP1 design
  FIELDSTYLE_FV_LP1-1-1.jpg    FV1 (main, 522x1952, 2026-10-14)
  FIELDSTYLE_FV_LP1-2.jpg      FV2 (alternate, 573x1298; same file as the earlier "7 1FIELDSTYLE_FV_LP2-2.jpg")
  FIELDSTYLE_LP1-LP2共通        3830x816 RGBA staff strip (PNG)

FV/full JPEGs are copied byte-for-byte. Everything else is cropped from decoded
pixels and saved as PNG, so no pixel is re-compressed.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

SRC, ROOT = Path(sys.argv[1]), Path(sys.argv[2])
DESIGN = ROOT / "public" / "design"
(DESIGN / "staff").mkdir(parents=True, exist_ok=True)
(ROOT / "reference").mkdir(exist_ok=True)

BODY_Y = 1118  # first row of the body (yellow section) in the full design
GREEN = np.array([104, 145, 41])  # flat STAFF background, sampled from the design

# Staff geometry measured by template matching against the full design (full-image px)
CARD_X = [0, 644, 1294, 1944, 2594, 3244]  # card columns inside the strip
CARD_W, CARD_H = 586, 816
SCALE = 0.6525
STATIC_X, STATIC_Y = 71, 9206  # centered static card
PEEK_LEFT, PEEK_RIGHT = 419, 423  # neighbor offsets that best match the static peeks
STAGE_Y0, STAGE_Y1 = 9180, 9840  # rows replaced by the live slider layers
DOT_Y = 9793.8
DOT_XS = [193.16, 224.5, 255.61, 286.84, 318.0]

shutil.copyfile(SRC / "FIELDSTYLE_FV_LP1-1-1.jpg", ROOT / "reference" / "lp1-fv-1-original.jpg")
# FV1 is edited (smaller present block, tighter gaps): run scripts/edit_fv1_present.py
#   reference/lp1-fv-1-original.jpg -> public/design/lp1-fv-1.jpg
shutil.copyfile(SRC / "FIELDSTYLE_FV_LP1-2.jpg", DESIGN / "lp1-fv-2.jpg")
shutil.copyfile(SRC / "FIELDSTYLE_LP1_2026.jpg", ROOT / "reference" / "lp1-full.jpg")

full = Image.open(SRC / "FIELDSTYLE_LP1_2026.jpg").convert("RGB")
assert full.size == (509, 14254), full.size
full.crop((0, BODY_Y, 509, full.height)).save(DESIGN / "lp1-body.png", optimize=True)

strip = Image.open(SRC / "FIELDSTYLE_LP1-LP2共通").convert("RGBA")
assert strip.size == (3830, 816), strip.size
shutil.copyfile(SRC / "FIELDSTYLE_LP1-LP2共通", DESIGN / "staff-all.png")
cards = []
for i, x in enumerate(CARD_X):
    c = strip.crop((x, 0, x + CARD_W, CARD_H))
    c.save(DESIGN / "staff" / f"staff-{i + 1:02d}.png", optimize=True)
    cards.append(c)

# ---- STAFF stage layers -------------------------------------------------------
f = np.array(full).astype(int)
y0, y1 = STAGE_Y0, STAGE_Y1
stage = f[y0:y1].copy()
h = y1 - y0
w = round(CARD_W * SCALE)
hh = round(CARD_H * SCALE)

def card_layer(card, x0):
    """Alpha + composite-over-green of a scaled card placed at full-image x0, STATIC_Y."""
    sc = np.array(card.resize((w, hh), Image.LANCZOS)).astype(float)
    alpha = np.zeros((h, 509))
    comp = np.zeros((h, 509, 3))
    a, b = max(0, x0), min(509, x0 + w)
    if a >= b:
        return alpha, comp
    ys = STATIC_Y - y0
    alpha[ys:ys + hh, a:b] = sc[:, a - x0:b - x0, 3] / 255
    comp[ys:ys + hh, a:b] = sc[:, a - x0:b - x0, :3]
    return alpha, comp

layers = [
    card_layer(cards[0], STATIC_X),
    card_layer(cards[5], STATIC_X - PEEK_LEFT),
    card_layer(cards[1], STATIC_X + PEEK_RIGHT),
]
card_alpha = np.maximum.reduce([l[0] for l in layers])
card_comp = sum(l[1] * l[0][..., None] for l in layers) + GREEN * (1 - card_alpha[..., None])

from scipy import ndimage  # noqa: E402

card_mask = ndimage.binary_dilation(card_alpha > 0.02, iterations=2)
yy, xx = np.mgrid[0:h, 0:509]
dot_mask = np.zeros((h, 509), bool)
for dx in DOT_XS:
    dot_mask |= (xx - dx) ** 2 + (yy - (DOT_Y - y0)) ** 2 <= 8.5 ** 2

dist_green = np.abs(stage - GREEN).sum(2)
# Pixels where the design shows the static card rather than the branch/leaf
shows_card = np.abs(stage - card_comp).sum(2) < 60

bg = stage.copy()
bg[card_mask | dot_mask] = GREEN
bg[:, 508] = stage[:, 508]  # keep the design's 1px right edge line
Image.fromarray(bg.astype(np.uint8)).save(DESIGN / "staff-stage-bg.png", optimize=True)

# Overlay drawn above the cards: branch + leaves in the top rows, right edge line.
ov_alpha = np.zeros((h, 509))
# Branch occupies rows < 9214 everywhere; only the small leaf (x < 70) hangs lower.
region = np.zeros((h, 509), bool)
region[: 9214 - y0, :] = True
region[: 9250 - y0, :70] = True
branch = region & (dist_green > 30) & ~(card_mask & shows_card)
ov_alpha = np.where(branch, np.clip(dist_green / 90, 0, 1), 0)
ov_alpha[:, 508] = 1
ov_rgb = np.where(ov_alpha[..., None] > 0, stage, 0)
ov = np.dstack([ov_rgb, (ov_alpha * 255).round()]).astype(np.uint8)
Image.fromarray(ov, "RGBA").save(DESIGN / "staff-stage-overlay.png", optimize=True)

# ---- manifest -----------------------------------------------------------------
def info(p):
    im = Image.open(p)
    return {
        "path": "/" + str(p.relative_to(ROOT / "public")) if "public" in p.parts else str(p.relative_to(ROOT)),
        "width": im.width,
        "height": im.height,
        "bytes": p.stat().st_size,
        "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
    }

files = [DESIGN / "lp1-fv-1.jpg", DESIGN / "lp1-fv-2.jpg", DESIGN / "lp1-body.png",
         DESIGN / "staff-all.png", *sorted((DESIGN / "staff").glob("*.png")),
         DESIGN / "staff-stage-bg.png", DESIGN / "staff-stage-overlay.png",
         ROOT / "reference" / "lp1-full.jpg"]
json.dump({"generatedBy": "scripts/prepare_assets.py", "files": [info(p) for p in files]},
          open(ROOT / "asset-manifest.generated.json", "w"), ensure_ascii=False, indent=2)
print("ok")
