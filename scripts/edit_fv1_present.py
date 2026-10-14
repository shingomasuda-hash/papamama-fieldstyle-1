"""Shrink FV1's 予約者全員にプレゼント block and tighten the gaps around it.

Usage: python3 -I scripts/edit_fv1_present.py <in> <out> [--k 1|2]

<in> is FIELDSTYLE_FV_LP1-1-1.jpg (522x1952) for --k 1, or its @2x upscale
(1044x3904) for --k 2. Rows above the block (logo, copy, car, FIELDSTYLE,
date) are kept untouched. The block (gift box, ribbon, PRESENT cards) is scaled
by SCALE and centred. The area around it is rebuilt from the original's own
background: a low-frequency gradient estimated around the block, plus the
paper texture taken from the empty rows above/below the block.
"""
import argparse

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

# 1x geometry (rows in the 522x1952 original)
KEEP_Y = 1118  # last row of the date line; everything above is kept as-is
BLOCK = (1198, 1830)  # block rows incl. a small margin (content 1204–1826)
CLEAN = [(1124, 1194), (1834, 1946)]  # empty textured rows used as texture source
SCALE = 0.8
GAP_TOP, GAP_BOTTOM = 40, 44  # new gaps: date → block, block → FV bottom


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--k", type=int, default=1)
    a = ap.parse_args()
    k = a.k
    im = Image.open(a.src).convert("RGB")
    W, H = im.size
    assert (W, H) == (522 * k, 1952 * k), im.size
    f = np.array(im).astype(np.float32)

    y0 = KEEP_Y * k
    L = f[y0:]  # lower area
    Lh = L.shape[0]

    # --- block mask (filled shapes, dilated, feathered) --------------------------
    blur = np.array(Image.fromarray(L.astype(np.uint8)).filter(ImageFilter.GaussianBlur(25 * k))).astype(np.float32)
    dev = np.abs(L - blur).max(2)
    content = dev > 25
    content[: (BLOCK[0] - KEEP_Y) * k] = False
    content[(BLOCK[1] - KEEP_Y) * k:] = False
    content = ndimage.binary_dilation(content, iterations=6 * k)
    content = ndimage.binary_fill_holes(content)
    content = ndimage.binary_dilation(content, iterations=4 * k)

    # --- low-frequency background (normalised convolution around the block) ------
    valid = ~ndimage.binary_dilation(content, iterations=8 * k)
    valid[-2 * k:] = False  # skip the 1px light line at the very bottom of the source
    # Estimated at 1x resolution for every k (then upscaled), so the @2x result matches
    # 1x; at full @2x resolution the Gaussian weights deep inside the masked block fall
    # below float precision and produced dark blotches.
    W1, H1 = W // k, Lh // k
    L1 = np.array(Image.fromarray(np.clip(L, 0, 255).astype(np.uint8)).resize((W1, H1), Image.BOX)).astype(np.float64)
    v1 = np.array(Image.fromarray(valid.astype(np.uint8) * 255).resize((W1, H1), Image.BOX)) > 250
    num = ndimage.gaussian_filter(L1 * v1[..., None], (40, 40, 0))
    den = ndimage.gaussian_filter(v1.astype(np.float64), 40)[..., None]
    lf1 = num / np.maximum(den, 1e-12)
    lf = np.array(Image.fromarray(np.clip(lf1, 0, 255).astype(np.uint8)).resize((W, Lh), Image.BICUBIC)).astype(np.float32)
    hp = L - lf  # texture (only meaningful where valid)

    # --- new lower area --------------------------------------------------------------
    bh = (BLOCK[1] - BLOCK[0]) * k
    sbh = round(bh * SCALE)
    sbw = round(W * SCALE)
    # Heights are computed in 1x units and multiplied by k, so @2x is exactly twice 1x.
    top_off1 = (1204 - BLOCK[0]) * SCALE  # margin inside the scaled box
    bot_off1 = (BLOCK[1] - 1826) * SCALE
    new_h = k * (GAP_TOP + round((BLOCK[1] - BLOCK[0]) * SCALE - top_off1 - bot_off1) + GAP_BOTTOM)
    box_y = round(k * (GAP_TOP - top_off1))

    # gradient: resample the original's low-frequency field to the new height
    lf_new = np.array(
        Image.fromarray(np.clip(lf, 0, 255).astype(np.uint8)).resize((W, new_h), Image.BICUBIC)
    ).astype(np.float32)

    # texture: stack clean strips (with mirrored variants) and cross-fade the joins
    strips = []
    for r0, r1 in CLEAN:
        s = hp[(r0 - KEEP_Y) * k:(r1 - KEEP_Y) * k]
        strips += [s, s[::-1], s[:, ::-1], s[::-1, ::-1]]
    order = [strips[i % len(strips)] for i in (0, 4, 1, 5, 2, 6, 3, 7, 0, 4, 1, 5)]
    xf = 8 * k
    tex = order[0].copy()
    for s in order[1:]:
        if tex.shape[0] >= new_h:
            break
        w = np.linspace(0, 1, xf, dtype=np.float32)[:, None, None]
        tex[-xf:] = tex[-xf:] * (1 - w) + s[:xf] * w
        tex = np.concatenate([tex, s[xf:]])
    tex = tex[:new_h]
    bg = lf_new + tex

    # keep the original first rows below the date and cross-fade into the rebuilt bg
    keep = 12 * k
    fade = 20 * k
    bg[:keep] = L[:keep]
    w = np.linspace(0, 1, fade, dtype=np.float32)[:, None, None]
    bg[keep:keep + fade] = L[keep:keep + fade] * (1 - w) + bg[keep:keep + fade] * w

    # --- scaled block composited with a feathered mask ---------------------------------
    by0 = (BLOCK[0] - KEEP_Y) * k
    box = Image.fromarray(np.clip(L[by0:by0 + bh], 0, 255).astype(np.uint8)).resize((sbw, sbh), Image.LANCZOS)
    m = Image.fromarray((content[by0:by0 + bh] * 255).astype(np.uint8)).resize((sbw, sbh), Image.BILINEAR)
    m = np.array(m.filter(ImageFilter.GaussianBlur(3 * k))).astype(np.float32)[..., None] / 255
    bx = (W - sbw) // 2
    region = bg[box_y:box_y + sbh, bx:bx + sbw]
    bg[box_y:box_y + sbh, bx:bx + sbw] = np.array(box).astype(np.float32) * m + region * (1 - m)

    out = np.concatenate([f[:y0], bg]).clip(0, 255).astype(np.uint8)
    Image.fromarray(out).save(a.dst, quality=95, subsampling=0, optimize=True)
    print("saved", a.dst, out.shape[1], "x", out.shape[0])


if __name__ == "__main__":
    main()
