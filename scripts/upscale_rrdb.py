"""Torch-free Real-ESRGAN (RRDBNet, x2/x4) inference with numpy + BLAS.

Usage: python3 -I scripts/upscale_rrdb.py <weights.pth> <in.png> <out.png> [--out-scale 2]

Weights: RealESRGAN_x2plus.pth (used for this site) / RealESRGAN_x4plus.pth from
https://github.com/xinntao/Real-ESRGAN/releases (BSD-3-Clause). The x4 result is
resampled to --out-scale with Lanczos (no-op for x2plus at --out-scale 2). RGBA input: RGB goes through the network,
alpha is resampled with Lanczos.
"""
import argparse
import pickle
import sys
import time
import zipfile

import numpy as np
from PIL import Image

# ---- .pth loading without torch -----------------------------------------------------
_DTYPES = {"FloatStorage": np.float32, "HalfStorage": np.float16, "DoubleStorage": np.float64}


def load_pth(path):
    zf = zipfile.ZipFile(path)
    names = zf.namelist()
    root = names[0].split("/")[0]
    pkl = next(n for n in names if n.endswith("data.pkl"))

    class _Storage:
        def __init__(self, dtype, key):
            self.dtype, self.key = dtype, key

    def rebuild(storage, offset, size, stride, *args):
        buf = np.frombuffer(zf.read(f"{root}/data/{storage.key}"), dtype=storage.dtype)
        n = int(np.prod(size)) if size else 1
        if not size:
            return buf[offset].copy()
        item = buf.itemsize
        return np.lib.stride_tricks.as_strided(buf[offset:], shape=size, strides=[s * item for s in stride]).copy()

    class U(pickle.Unpickler):
        def find_class(self, mod, name):
            if name == "_rebuild_tensor_v2":
                return rebuild
            if mod == "collections" and name == "OrderedDict":
                import collections
                return collections.OrderedDict
            if mod.startswith("torch") and name in _DTYPES:
                return name
            if mod == "torch._utils" and name == "_rebuild_parameter":
                return lambda t, *a: t
            raise pickle.UnpicklingError(f"blocked {mod}.{name}")

        def persistent_load(self, pid):
            _, storage_type, key, _loc, _n = pid
            name = storage_type if isinstance(storage_type, str) else storage_type
            return _Storage(_DTYPES[name], key)

    sd = U(zf.open(pkl)).load()
    for k in ("params_ema", "params"):
        if k in sd:
            sd = sd[k]
            break
    return {k: v.astype(np.float32) for k, v in sd.items()}


# ---- network ---------------------------------------------------------------------------
def conv(x, w, b):
    """x: (H, W, C) float32, w: (O, C, 3, 3) -> (H, W, O); zero padding 1."""
    H, W, C = x.shape
    p = np.pad(x, ((1, 1), (1, 1), (0, 0)))
    cols = np.lib.stride_tricks.sliding_window_view(p, (3, 3), axis=(0, 1))  # H, W, C, 3, 3
    cols = cols.reshape(H * W, C * 9)
    out = cols @ w.reshape(w.shape[0], -1).T
    out += b
    return out.reshape(H, W, -1)


def lrelu(x):
    return np.where(x > 0, x, x * 0.2)


def up2(x):
    return x.repeat(2, axis=0).repeat(2, axis=1)


class RRDBNet:
    def __init__(self, sd):
        self.sd = sd
        self.n_blocks = 1 + max(int(k.split(".")[1]) for k in sd if k.startswith("body."))
        # x2plus feeds a pixel-unshuffled (12-channel) image; x4 models take RGB.
        self.unshuffle = sd["conv_first.weight"].shape[1] == 12
        self.scale = 2 if self.unshuffle else 4

    def c(self, name, x):
        return conv(x, self.sd[name + ".weight"], self.sd[name + ".bias"])

    def rdb(self, prefix, x):
        x1 = lrelu(self.c(prefix + ".conv1", x))
        x2 = lrelu(self.c(prefix + ".conv2", np.concatenate([x, x1], 2)))
        x3 = lrelu(self.c(prefix + ".conv3", np.concatenate([x, x1, x2], 2)))
        x4 = lrelu(self.c(prefix + ".conv4", np.concatenate([x, x1, x2, x3], 2)))
        x5 = self.c(prefix + ".conv5", np.concatenate([x, x1, x2, x3, x4], 2))
        return x5 * 0.2 + x

    def __call__(self, img):
        if self.unshuffle:
            H, W, C = img.shape
            img = img.reshape(H // 2, 2, W // 2, 2, C).transpose(0, 2, 4, 1, 3).reshape(H // 2, W // 2, C * 4)
        feat = self.c("conv_first", img)
        body = feat
        for i in range(self.n_blocks):
            o = self.rdb(f"body.{i}.rdb1", body)
            o = self.rdb(f"body.{i}.rdb2", o)
            o = self.rdb(f"body.{i}.rdb3", o)
            body = o * 0.2 + body
        feat = feat + self.c("conv_body", body)
        feat = lrelu(self.c("conv_up1", up2(feat)))
        feat = lrelu(self.c("conv_up2", up2(feat)))
        return self.c("conv_last", lrelu(self.c("conv_hr", feat)))


def upscale(net, rgb, tile=96, pad=10):
    """rgb: (H, W, 3) uint8 -> (sH, sW, 3) uint8, tiled like Real-ESRGAN's tile mode."""
    s = net.scale
    H, W, _ = rgb.shape
    x = rgb.astype(np.float32) / 255
    out = np.zeros((H * s, W * s, 3), np.float32)
    tiles = [(y, xx) for y in range(0, H, tile) for xx in range(0, W, tile)]
    t0 = time.time()
    for n, (y, xx) in enumerate(tiles):
        y0, y1 = max(0, y - pad), min(H, y + tile + pad)
        x0, x1 = max(0, xx - pad), min(W, xx + tile + pad)
        patch = x[y0:y1, x0:x1]
        ph, pw = patch.shape[0] % 2, patch.shape[1] % 2
        if net.unshuffle and (ph or pw):  # pixel-unshuffle needs even sizes (reflect pad like Real-ESRGAN)
            patch = np.pad(patch, ((0, ph), (0, pw), (0, 0)), mode="reflect")
        res = net(patch)
        ty1, tx1 = min(H, y + tile), min(W, xx + tile)
        out[y * s:ty1 * s, xx * s:tx1 * s] = res[(y - y0) * s:(ty1 - y0) * s, (xx - x0) * s:(tx1 - x0) * s]
        if n % 20 == 0:
            el = time.time() - t0
            print(f"  tile {n + 1}/{len(tiles)}  {el:.0f}s  eta {el / (n + 1) * (len(tiles) - n - 1):.0f}s", flush=True)
    return (np.clip(out, 0, 1) * 255).round().astype(np.uint8)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("weights")
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--out-scale", type=float, default=2)
    a = ap.parse_args()
    net = RRDBNet(load_pth(a.weights))
    im = Image.open(a.src)
    alpha = im.getchannel("A") if im.mode == "RGBA" else None
    rgb = np.array(im.convert("RGB"))
    big = Image.fromarray(upscale(net, rgb))
    size = (round(im.width * a.out_scale), round(im.height * a.out_scale))
    res = big.resize(size, Image.LANCZOS) if size != big.size else big
    if alpha is not None:
        res = res.convert("RGBA")
        res.putalpha(alpha.resize(size, Image.LANCZOS))
    res.save(a.dst)
    print("saved", a.dst, res.size)


if __name__ == "__main__":
    sys.exit(main())
