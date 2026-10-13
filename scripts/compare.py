"""Pixel comparison of the verify.mjs screenshots against the source design files.

Usage: python3 -I scripts/compare.py   (run after scripts/verify.mjs)

- FV: screenshot rows of the FV vs the FV source resampled to the same size.
- Body: screenshot rows of the body vs lp1-body.png resampled to the same size
  (at 509px this is 1:1, so any difference is something the page drew).
- Bands: rows where the body differs, to locate e.g. the STAFF pager change.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image

OUT = Path("qa/screenshots")
DESIGN = Path("public/design")
report = json.loads((OUT / "report.json").read_text())

BODY_Y0 = 1118
STAGE = (9180 - BODY_Y0, 9840 - BODY_Y0)
DOTS = (9780 - BODY_Y0, 9808 - BODY_Y0)


def stats(a, b):
    d = np.abs(a.astype(int) - b.astype(int)).max(axis=2)
    return d, {"mean": round(float(d.mean()), 3), "p99": int(np.percentile(d, 99)), "max": int(d.max()),
               "pct_px_gt16": round(float((d > 16).mean() * 100), 4)}


def bands(d, scale, thresh=24, min_px=3):
    rows = (d > thresh).sum(axis=1) >= min_px
    out, start = [], None
    for y, v in enumerate(list(rows) + [False]):
        if v and start is None:
            start = y
        if not v and start is not None:
            out.append((round(start / scale), round(y / scale)))
            start = None
    return out


results = {}
for tag, p in report["pages"].items():
    shot = np.array(Image.open(OUT / f"{tag}.png").convert("RGB"))
    W = round(p["bodyRect"]["w"])
    left = round(p["bodyRect"]["left"])
    fv_top, fv_h = round(p["fvRect"]["top"]), p["fvRect"]["h"]
    body_top, body_h = p["bodyRect"]["top"], p["bodyRect"]["h"]
    fv_src = Image.open(DESIGN / Path(p["fvSrc"]).name).convert("RGB")
    fv_rows = int(np.floor(fv_h))
    fv_ref = np.array(fv_src.resize((W, fv_rows), Image.LANCZOS))
    _, fv_stats = stats(shot[fv_top:fv_top + fv_rows, left:left + W], fv_ref)

    b0 = round(body_top)  # Chrome paints the body at the rounded offset
    rows = min(int(round(body_h)), shot.shape[0] - b0)
    body_src = Image.open(DESIGN / "lp1-body.png").convert("RGB")
    body_ref = np.array(body_src.resize((W, round(body_h)), Image.LANCZOS))[:rows]
    body_shot = shot[b0:b0 + rows, left:left + W]
    d, body_stats = stats(body_shot, body_ref)
    scale = body_h / 13136
    s0, s1 = int(STAGE[0] * scale), int(STAGE[1] * scale)
    k0, k1 = int(DOTS[0] * scale), int(DOTS[1] * scale)
    outside = np.ones(rows, bool)
    outside[s0:s1] = False
    _, outside_stats = stats(body_shot[outside], body_ref[outside])
    # STAFF stage: element screenshot at rest (full-page capture resets inner scroll),
    # aligned to the reference with the best of a ±1 row offset (fractional top).
    stage_shot = np.array(Image.open(OUT / f"stage-{tag}.png").convert("RGB"))
    st_top = p["stageShotTop"] - body_top
    best = None
    for off in (-1, 0, 1):
        r0 = int(np.floor(st_top)) + off
        n = min(len(stage_shot), len(body_ref) - r0)
        ref = body_ref[r0:r0 + n]
        e = np.abs(stage_shot[:n].astype(int) - ref.astype(int)).mean()
        if best is None or e < best[0]:
            best = (e, r0, n)
    _, r0, n = best
    k0r, k1r = k0 - r0, k1 - r0
    keep = np.ones(n, bool)
    keep[max(0, k0r):max(0, k1r)] = False
    _, stage_stats = stats(stage_shot[:n][keep], body_ref[r0:r0 + n][keep])
    _, dots_stats = stats(stage_shot[k0r:k1r], body_ref[r0 + k0r:r0 + k1r])
    if tag == "w509-fv1":
        dd = np.abs(stage_shot[:n].astype(int) - body_ref[r0:r0 + n].astype(int)).max(axis=2)
        Image.fromarray(np.clip(dd * 4, 0, 255).astype(np.uint8)).save(OUT / "diff-staff-509.png")
    results[tag] = {
        "fv_vs_source": fv_stats,
        "body_outside_staff_vs_source": outside_stats,
        "staff_stage_excl_pager_vs_source": stage_stats,
        "staff_pager_rows_vs_source": dots_stats,
        "diff_bands_body_px_outside_staff": bands(np.where(outside[:, None], d, 0), scale),
    }

# FV1 vs FV2: the body must be the same. Full-page bodies are compared outside the
# STAFF stage; the stage is compared via its element screenshots (best ±1 row).
for w in (509, 390, 375):
    a = report["pages"][f"w{w}-fv1"]
    b = report["pages"][f"w{w}-fv2"]
    sa = np.array(Image.open(OUT / f"w{w}-fv1.png").convert("RGB")).astype(int)[round(a["bodyRect"]["top"]):]
    sb = np.array(Image.open(OUT / f"w{w}-fv2.png").convert("RGB")).astype(int)[round(b["bodyRect"]["top"]):]
    n = min(len(sa), len(sb), round(a["bodyRect"]["h"]))
    scale = a["bodyRect"]["h"] / 13136
    mask = np.ones(n, bool)
    mask[int(STAGE[0] * scale) - 2:int(STAGE[1] * scale) + 2] = False
    d = np.abs(sa[:n] - sb[:n]).max(axis=2)[mask]
    A = np.array(Image.open(OUT / f"stage-w{w}-fv1.png").convert("RGB")).astype(int)
    B = np.array(Image.open(OUT / f"stage-w{w}-fv2.png").convert("RGB")).astype(int)
    m = min(len(A), len(B)) - 2
    stage = min((np.abs(A[1:m] - B[1 + o:m + o]).max(axis=2) for o in (-1, 0, 1)), key=lambda x: x.mean())
    results[f"w{w}-fv1-vs-fv2"] = {
        "body_outside_staff": {"identical": bool(d.max() == 0), "max_diff": int(d.max()), "rows_differing": int((d.max(axis=1) > 0).sum())},
        "staff_stage": {"mean": round(float(stage.mean()), 3), "max_diff": int(stage.max())},
    }

(OUT / "compare.json").write_text(json.dumps(results, ensure_ascii=False, indent=2))
for k, v in results.items():
    if "diff_bands_body_px_outside_staff" in v:
        b_ = v["diff_bands_body_px_outside_staff"]
        v = {**v, "diff_bands_body_px_outside_staff": f"{len(b_)} bands: {b_[:6]}"}
    print(k, json.dumps(v, ensure_ascii=False))
