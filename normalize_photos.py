#!/usr/bin/env python3
"""Normalise the dish photos: consistent exposure/colour + consistent sushi scale.

Stage 1 (safe, automatic): match every photo's Lab median + a/b to the set
median, with a limited strength so the warm counter ambience survives.

Stage 2 (needs a subject box): crop to 3:4 around the sushi so the piece fills
a fixed share of the frame.  The box comes from scipy-based blob detection and
is validated visually before anything is written.
"""
import json, os
import numpy as np
from PIL import Image
from scipy import ndimage

DISH = "/opt/data/omakase-guide/images/dish"
OUT = "/opt/data/omakase-guide/images/dish/norm"
SRC_MANIFEST = "/opt/data/omakase-guide/journal.json"


# ---------- colour ----------
def srgb_to_lab(rgb):
    """rgb float 0-1 (H,W,3) -> L 0-100, a, b"""
    m = np.array([[0.4124, 0.3576, 0.1805],
                  [0.2126, 0.7152, 0.0722],
                  [0.0193, 0.1192, 0.9505]])
    xyz = rgb @ m.T
    wp = np.array([0.95047, 1.0, 1.08883])
    t = xyz / wp
    d = 6 / 29
    f = np.where(t > d ** 3, np.cbrt(t), t / (3 * d * d) + 4 / 29)
    L = 116 * f[..., 1] - 16
    a = 500 * (f[..., 0] - f[..., 1])
    b = 200 * (f[..., 1] - f[..., 2])
    return L, a, b


def lab_to_srgb(L, a, b):
    fy = (L + 16) / 116
    fx = fy + a / 500
    fz = fy - b / 200
    d = 6 / 29
    f = np.stack([fx, fy, fz], -1)
    t = np.where(f > d, f ** 3, 3 * d * d * (f - 4 / 29))
    wp = np.array([0.95047, 1.0, 1.08883])
    xyz = t * wp
    m = np.array([[3.2406, -1.5372, -0.4986],
                  [-0.9689, 1.8758, 0.0415],
                  [0.0557, -0.2040, 1.0570]])
    rgb = xyz @ m.T
    return np.clip(rgb, 0, 1)


def stats(path, size=256):
    im = Image.open(path).convert("RGB").resize((size, size), Image.LANCZOS)
    arr = np.asarray(im, dtype=np.float32) / 255.0
    lin = np.where(arr <= 0.04045, arr / 12.92, ((arr + 0.055) / 1.055) ** 2.4)
    L, a, b = srgb_to_lab(lin)
    return dict(L=float(np.median(L)), a=float(np.median(a)), b=float(np.median(b)),
                Lp5=float(np.percentile(L, 5)), Lp95=float(np.percentile(L, 95)))


def _centre_stats(path, size=256):
    """Stats over the central 60% box — a decent proxy for 'the sushi', since
    every photo is composed with the piece near the middle."""
    im = Image.open(path).convert("RGB").resize((size, size), Image.LANCZOS)
    w, h = im.size
    box = (int(w * 0.20), int(h * 0.20), int(w * 0.80), int(h * 0.80))
    arr = np.asarray(im.crop(box), dtype=np.float32) / 255.0
    lin = np.where(arr <= 0.04045, arr / 12.92, ((arr + 0.055) / 1.055) ** 2.4)
    L, a, b = srgb_to_lab(lin)
    # p75 rather than the median: a dark slate/black plate drags the median down
    # even when the rice and fish are perfectly exposed.
    return dict(L=float(np.percentile(L, 75)), a=float(np.median(a)), b=float(np.median(b)),
                med=float(np.median(L)), Lp90=float(np.percentile(L, 90)),
                Lp10=float(np.percentile(L, 10)))


def stats(path, size=256):
    return _centre_stats(path, size)


def normalise_image(path, target, strength_L=0.9, strength_ab=0.55, max_shift=18.0):
    im = Image.open(path).convert("RGB")
    arr = np.asarray(im, dtype=np.float32) / 255.0
    lin = np.where(arr <= 0.04045, arr / 12.92, ((arr + 0.055) / 1.055) ** 2.4)
    L, a, b = srgb_to_lab(lin)
    s = _centre_stats(path)

    # exposure: bring the subject's p75 luminance onto the target. Small gaps are
    # a straight offset; big gaps use a gamma curve so the shadows lift instead of
    # the highlights blowing out.
    want = target["L"] - s["L"]
    if abs(want) <= max_shift:
        Ln = L + want
    else:
        lo, hi = max(s["L"], 1.0) / 100.0, target["L"] / 100.0
        g = float(np.clip(np.log(hi) / np.log(lo), 0.35, 1.8))
        Ln = 100.0 * np.clip(L / 100.0, 0, 1) ** g
        Ln = Ln + (target["L"] - float(np.percentile(Ln, 75)))
    Ln = np.clip(Ln, 0, 100)
    # highlight rolloff keeps white rice from going flat
    hi_mask = Ln > 96
    Ln = np.where(hi_mask, 96 + (Ln - 96) * 0.92, Ln)
    # fixed-point trim against the SAME centre region used for measurement
    hh, ww = Ln.shape
    def _c(m):
        return float(np.percentile(m[int(hh * .2):int(hh * .8), int(ww * .2):int(ww * .8)], 75))
    for _ in range(4):
        gap = target["L"] - _c(Ln)
        if abs(gap) < 0.5:
            break
        Ln = np.clip(Ln + gap, 0, 100)

    # lift a touch of contrast so brightened photos don't read flat, and nudge
    # chroma back up when the piece is pale (white fish on a white plate)
    mid = 55.0
    Ln = mid + (Ln - mid) * 1.07
    Ln = np.clip(Ln, 0, 100)
    da = float(np.clip((s["a"] - target["a"]) * strength_ab, -5, 5))
    db = float(np.clip((s["b"] - target["b"]) * strength_ab, -5, 5))
    chroma = float(np.hypot(s["a"], s["b"]))
    boost = 1.10 if chroma < 8 else 1.03
    out = lab_to_srgb(Ln, (a - da) * boost, (b - db) * boost)
    srgb = np.where(out <= 0.0031308, out * 12.92, 1.055 * out ** (1 / 2.4) - 0.055)
    return Image.fromarray((np.clip(srgb, 0, 1) * 255).astype(np.uint8))


# ---------- subject ----------
def subject_box(path, n=200):
    """In-focus subject box.

    These are counter shots with shallow depth of field: the nigiri is the only
    sharp thing in frame, the plate/wood fall off into bokeh. So high-frequency
    energy is a far better cue than colour saliency (which mis-fired badly).
    """
    im = Image.open(path).convert("RGB")
    W, H = im.size
    small = im.resize((int(n * 0.75), n), Image.LANCZOS)
    arr = np.asarray(small.convert("L"), dtype=np.float32) / 255.0

    blur = ndimage.gaussian_filter(arr, 2.0)
    hp = np.abs(arr - blur)                       # high-frequency energy
    energy = ndimage.gaussian_filter(hp, 6.0)     # pool it into a smooth map
    energy = energy / (energy.max() + 1e-8)

    h, w = energy.shape
    yy, xx = np.mgrid[0:h, 0:w]
    prior = np.exp(-(((yy - h / 2) / (h * 0.55)) ** 2 + ((xx - w / 2) / (w * 0.55)) ** 2))
    sc = energy * (0.45 + 0.55 * prior)

    thr = np.percentile(sc, 85)
    mask = sc >= thr
    mask = ndimage.binary_opening(mask, np.ones((3, 3)))
    mask = ndimage.binary_closing(mask, np.ones((7, 7)))
    lab, nlab = ndimage.label(mask)
    if nlab == 0:
        return None
    sizes = ndimage.sum(mask, lab, range(1, nlab + 1))
    k = int(np.argmax(sizes)) + 1
    blob = lab == k
    ys, xs = np.nonzero(blob)
    if len(xs) < 50:
        return None
    x0, x1 = xs.min() / w, (xs.max() + 1) / w
    y0, y1 = ys.min() / h, (ys.max() + 1) / h
    return dict(x0=float(x0), x1=float(x1), y0=float(y0), y1=float(y1),
                w=float(x1 - x0), h=float(y1 - y0), area=float(sizes[k - 1] / (w * h)))


def main():
    files = sorted(f for f in os.listdir(DISH) if f.endswith(".jpg"))
    data = {f: stats(os.path.join(DISH, f)) for f in files}
    tgt = {k: float(np.median([v[k] for v in data.values()])) for k in ("L", "a", "b")}
    print(f"{len(files)} photos | target L={tgt['L']:.1f} a={tgt['a']:.1f} b={tgt['b']:.1f}\n")
    print(f"{'file':22s} {'L':>6s} {'a':>6s} {'b':>6s} {'dL':>6s}   subject box (x0,x1,y0,y1) frac")
    boxes = {}
    for f in files:
        p = os.path.join(DISH, f)
        box = subject_box(p)
        boxes[f] = box
        bx = (f"{box['x0']:.2f},{box['x1']:.2f},{box['y0']:.2f},{box['y1']:.2f} {box['frac']:.2f}"
              if box else "FAIL")
        d = data[f]
        print(f"{f:22s} {d['L']:6.1f} {d['a']:6.1f} {d['b']:6.1f} {tgt['L']-d['L']:+6.1f}   {bx}")
    json.dump({"target": tgt, "stats": data, "boxes": boxes},
              open("/opt/data/omakase-guide/norm_stats.json", "w"), indent=1)


if __name__ == "__main__":
    main()
