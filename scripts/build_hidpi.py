"""Build the high-DPI (@2x) web assets from Real-ESRGAN x2plus outputs.

Usage: python3 -I scripts/build_hidpi.py <upscaled_dir>

<upscaled_dir> holds the outputs of scripts/upscale_rrdb.py (RealESRGAN_x2plus):
  lp1-fv-1@2x.png, lp1-fv-2@2x.png, lp1-body@2x.png, staff-01..06@2x.png

The @2x files are only served to high-density screens via srcset. The 1x files
(the original pixels) stay as they are and remain the visual reference.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

UP = Path(sys.argv[1])
ROOT = Path(__file__).resolve().parent.parent
D = ROOT / "public" / "design"
(D / "body").mkdir(exist_ok=True)

TILE_H = 1024  # 1x rows per body tile (2048 rows at 2x)
GREEN = np.array([104, 145, 41])
STAGE_Y0, STAGE_Y1 = 9180 - 1118, 9840 - 1118  # rows of the STAFF stage layers in lp1-body.png
JPEG = dict(quality=90, subsampling=0, optimize=True, progressive=True)  # 4:4:4 keeps coloured text crisp


def load(name, size):
    im = Image.open(UP / name)
    assert im.size == size, (name, im.size, size)
    return im


# FV
for n, size in (("1", (590, 1335)), ("2", (573, 1298))):
    load(f"lp1-fv-{n}@2x.png", (size[0] * 2, size[1] * 2)).convert("RGB").save(D / f"lp1-fv-{n}@2x.jpg", **JPEG)

# Body tiles (1x lossless crops of lp1-body.png + @2x JPEG)
body1 = Image.open(D / "lp1-body.png").convert("RGB")
body2 = load("lp1-body@2x.png", (1018, 26272)).convert("RGB")
tiles = []
for i, y in enumerate(range(0, body1.height, TILE_H)):
    h = min(TILE_H, body1.height - y)
    name = f"lp1-body-{i + 1:02d}"
    body1.crop((0, y, 509, y + h)).save(D / "body" / f"{name}.png", optimize=True)
    body2.crop((0, y * 2, 1018, (y + h) * 2)).save(D / "body" / f"{name}@2x.jpg", **JPEG)
    tiles.append(h)
print("tiles", tiles)

# Staff cards: WebP with lossless alpha
for i in range(1, 7):
    load(f"staff-{i:02d}@2x.png", (1172, 1632)).save(D / "staff" / f"staff-{i:02d}@2x.webp", quality=90, method=6, alpha_quality=100)

# STAFF stage layers at 2x, using the same masks as the 1x layers.
b1 = np.array(body1)[STAGE_Y0:STAGE_Y1].astype(int)
bg1 = np.array(Image.open(D / "staff-stage-bg.png").convert("RGB")).astype(int)
erased = np.abs(bg1 - b1).sum(2) > 0  # pixels the 1x background replaced with green
erased2 = ndimage.binary_dilation(erased.repeat(2, 0).repeat(2, 1), iterations=3)
s2 = np.array(body2)[STAGE_Y0 * 2:STAGE_Y1 * 2].copy()
s2[erased2] = GREEN
s2[:, 1016:] = np.array(body2)[STAGE_Y0 * 2:STAGE_Y1 * 2, 1016:]  # keep the 1px right edge line
Image.fromarray(s2.astype(np.uint8)).save(D / "staff-stage-bg@2x.png", optimize=True)

ov1 = Image.open(D / "staff-stage-overlay.png")
a2 = np.array(ov1.getchannel("A").resize((1018, 1320), Image.BILINEAR))
rgb2 = np.array(body2)[STAGE_Y0 * 2:STAGE_Y1 * 2]
rgb2 = np.where(a2[..., None] > 0, rgb2, 0)
Image.fromarray(np.dstack([rgb2, a2]).astype(np.uint8), "RGBA").save(D / "staff-stage-overlay@2x.png", optimize=True)
print("ok")
